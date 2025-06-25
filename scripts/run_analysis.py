# scripts/run_analysis.py

import os
import json
from glob import glob
from datetime import datetime, timedelta
from basketball_event import detector
from basketball_event.detector import bbox_iou, parse_frame_detections
import numpy as np

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'detection_output')
RESULT_DIR = os.path.join(os.path.dirname(__file__), '..', 'event_results')

# 초를 MM:SS 문자열로 변환
def seconds_to_mmss(seconds):
    seconds = max(0, int(seconds))
    m = seconds // 60
    s = seconds % 60
    return f"{m:02d}:{s:02d}"

# 프레임별 txt파일 읽기 함수 (frame_id는 파일명에서 추출, 각 줄에는 frame_id 없음)
def read_frame_txt(txt_path):
    detections = []
    timestamp_str = None
    with open(txt_path, 'r') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) < 7:
                continue
            # detection_output: <date> <time> <class_id> <x_center> <y_center> <width> <height> <team_id>
            # 날짜는 무시, 시분초만 사용
            time_str = parts[1]
            class_id = int(parts[2])
            x = float(parts[3])
            y = float(parts[4])
            w = float(parts[5])
            h = float(parts[6])
            team_id = int(parts[7]) if len(parts) > 7 else 0
            detection = [class_id, x, y, w, h, team_id]
            detections.append(detection)
            timestamp_str = time_str  # 모든 detection의 시분초는 동일하다고 가정
    return detections, timestamp_str

def main():
    # 프레임별 txt파일 정렬
    txt_files = sorted(glob(os.path.join(DATA_DIR, 'frame_*.txt')))
    if not os.path.exists(RESULT_DIR):
        os.makedirs(RESULT_DIR)

    frames = []
    team_ids = []
    timestamps = []
    frame_ids = []
    for txt_path in txt_files:
        # frame_id는 파일명에서 추출
        fname = os.path.basename(txt_path)
        frame_id = int(fname.split('_')[1].split('.')[0])
        detections, ts = read_frame_txt(txt_path)
        frames.append(detections)
        # 선수만 team_id 추출 (class_id==1)
        team_ids.append([det[-1] for det in detections if det[0] == 1])
        timestamps.append(ts)
        frame_ids.append(frame_id)

    # 공 바운딩박스 보정: detection 누락 구간 보완
    ball_boxes = detector.extrapolate_ball(frames, max_missing=None)
    for i, detections in enumerate(frames):
        # 기존 공 제거
        detections_wo_ball = [det for det in detections if det[0] != 0]
        # 가상 공이 있으면 추가 (team_id는 -1로 표기)
        if ball_boxes[i] is not None:
            x, y, w, h = ball_boxes[i]
            detections_wo_ball.insert(0, [0, x, y, w, h, -1])
        frames[i] = detections_wo_ball

    # 림 중심 좌표 추출
    rim_centers = []
    for i, detections in enumerate(frames):
        rim = None
        for det in detections:
            if det[0] == 2:
                rim = (det[1], det[2], det[3], det[4])
                break
        rim_center = (rim[0], rim[1]) if rim else None
        rim_centers.append(rim_center)

    # 이벤트 판별
    possession_history = detector.get_possession(frames, min_frames=15, initial_frames=15)
    shot_events = detector.detect_shot(frames, possession_history)
    score_events, ball_rim_dists = detector.detect_score(frames, shot_events, ball_boxes, rim_centers)
    rebound_events = detector.detect_rebound(frames, shot_events, score_events, possession_history)
    assist_events = detector.detect_assist(frames, shot_events, score_events, possession_history, team_ids)

    # 클락 관리 변수
    main_clock = 600.0  # 10분(600초)
    main_clock_action = None
    shot_clock = 12.0
    shot_clock_action = None
    last_shot_clock_reset_frame = 1
    last_shot_clock_event_time = None
    last_possession_team = None
    last_score_team = None
    last_score_frame = None

    def get_team_from_idx(idx, team_list):
        return team_list[idx] if idx is not None and idx < len(team_list) else None

    for idx, frame_id in enumerate(frame_ids):
        # possession은 팀 인덱스(0 또는 1)로 바로 기록
        poss_team = possession_history[idx]
        shot_team = shot_events[idx]
        score_team = score_events[idx]
        rebound_team = rebound_events[idx]
        assist_team = assist_events[idx]
        # shot_clock 관리 (리셋 이벤트 발생시 12초로 초기화, 그 외에는 프레임마다 감소)
        shot_clock_action = None
        reset_needed = False
        if score_events[idx] is not None:
            scorer_idx = score_events[idx]
            scorer_team = team_ids[idx][scorer_idx] if scorer_idx is not None and scorer_idx < len(team_ids[idx]) else None
            last_score_team = scorer_team
            last_score_frame = idx
            if idx+1 < len(possession_history):
                next_possessor = possession_history[idx+1]
                next_team = team_ids[idx+1][next_possessor] if next_possessor is not None and next_possessor < len(team_ids[idx+1]) else None
                if next_team is not None and next_team != scorer_team:
                    reset_needed = True
        elif rebound_events[idx] is not None:
            reset_needed = True
        elif shot_events[idx] is not None:
            reset_needed = True
        elif idx > 0:
            prev_team = possession_history[idx-1]
            curr_team = possession_history[idx]
            if prev_team is not None and curr_team is not None and prev_team != curr_team:
                if shot_events[idx] is None and score_events[idx] is None and rebound_events[idx] is None:
                    reset_needed = True
        if reset_needed:
            shot_clock_action = 'reset'
            shot_clock = 12.0
            last_shot_clock_reset_frame = frame_id
        else:
            elapsed_frames = frame_id - last_shot_clock_reset_frame
            shot_clock = max(0.0, 12.0 - elapsed_frames / 30)
        # 공-림 IoU 계산 (보정된 공 바운딩박스 사용)
        ball = ball_boxes[idx]
        rim = None
        # rim은 detection에서 추출
        for det in frames[idx]:
            if det[0] == 2:
                rim = (det[1], det[2], det[3], det[4])
                break
        ball_rim_iou = None
        if ball and rim:
            ball_rim_iou = bbox_iou(ball, rim)
        event = {
            'frame_id': frame_id,
            'main_clock': None,
            'main_clock_action': None,
            'shot_clock': int(shot_clock),
            'shot_clock_action': shot_clock_action,
            'possession': poss_team,
            'shot': shot_team,
            'score': score_team,
            'rebound': rebound_team,
            'assist': assist_team,
            'timestamp': timestamps[idx] if timestamps[idx] is not None else None,
            'ball_rim_dist': ball_rim_dists[idx]
        }
        # main_clock 관리 (1초 단위 내림)
        if frame_id == 1:
            main_clock = 600.0
            main_clock_action = 'start'  # 10분 리셋
        else:
            main_clock = 600.0 - (frame_id - 1) * (1/30)
            main_clock = int(main_clock)  # 1초 단위로 내림
            main_clock_action = None  # 이후에는 건드리지 않음
        event['main_clock'] = seconds_to_mmss(main_clock)
        event['main_clock_action'] = main_clock_action

        # 결과 저장
        json_name = f'frame_{frame_id:04d}.json'
        json_path = os.path.join(RESULT_DIR, json_name)
        with open(json_path, 'w') as jf:
            json.dump(event, jf, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    main()
