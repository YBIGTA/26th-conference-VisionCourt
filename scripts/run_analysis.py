# scripts/run_analysis.py

import os
import json
from glob import glob
from datetime import datetime, timedelta
from basketball_event import detector

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'detection_output')
RESULT_DIR = os.path.join(os.path.dirname(__file__), '..', 'event_results')

# 초를 MM:SS 문자열로 변환
def seconds_to_mmss(seconds):
    seconds = max(0, int(seconds))
    m = seconds // 60
    s = seconds % 60
    return f"{m:02d}:{s:02d}"

# timestamp(float, epoch seconds)를 시계 문자열로 변환
def timestamp_to_str(ts):
    dt = datetime.fromtimestamp(ts)
    return dt.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]

# 프레임별 txt파일 읽기 함수
def read_frame_txt(txt_path):
    detections = []
    timestamps = []
    frame_id = None
    with open(txt_path, 'r') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) < 8:
                continue
            fid, class_id, x, y, w, h, team_id, ts = parts
            frame_id = int(fid)
            detection = [int(class_id), float(x), float(y), float(w), float(h), int(team_id)]
            detections.append(detection)
            timestamps.append(float(ts))
    # 하나의 프레임에 여러 detection이 있을 수 있으나, frame_id와 timestamp는 모두 동일하다고 가정
    return frame_id, detections, timestamps[0] if timestamps else None

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
        frame_id, detections, ts = read_frame_txt(txt_path)
        frames.append(detections)
        # 선수만 team_id 추출 (class_id==1)
        team_ids.append([det[-1] for det in detections if det[0] == 1])
        timestamps.append(ts)
        frame_ids.append(frame_id)

    # 이벤트 판별
    possession_history = detector.get_possession(frames)
    shot_events = detector.detect_shot(frames, possession_history)
    score_events = detector.detect_score(frames, shot_events)
    rebound_events = detector.detect_rebound(frames, shot_events, score_events, possession_history)
    assist_events = detector.detect_assist(frames, shot_events, score_events, possession_history, team_ids)

    # 클락 관리 변수
    main_clock = 600.0  # 10분(600초)
    main_clock_action = None
    shot_clock = 12.0
    shot_clock_action = None
    last_shot_clock_reset_time = None
    last_shot_clock_event_time = None
    last_possession_team = None
    last_score_team = None
    last_score_frame = None

    for idx, frame_id in enumerate(frame_ids):
        # 현재 프레임의 서버시간(이벤트 발생 기준)
        current_server_time = timestamps[idx]
        # 이벤트 정보
        event = {
            'frame_id': frame_id,
            'main_clock': None,
            'main_clock_action': None,
            'shot_clock': None,
            'shot_clock_action': None,
            'possession': possession_history[idx],
            'shot': shot_events[idx],
            'score': score_events[idx],
            'rebound': rebound_events[idx],
            'assist': assist_events[idx],
            'timestamp': None
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

        # shot_clock 관리 (1초 단위 내림)
        shot_clock_action = None
        reset_needed = False
        # 1. 득점 후 소유권이 득점팀과 다르면 리셋
        if score_events[idx] is not None:
            scorer_idx = score_events[idx]
            scorer_team = team_ids[idx][scorer_idx] if scorer_idx is not None and scorer_idx < len(team_ids[idx]) else None
            last_score_team = scorer_team
            last_score_frame = idx
            # 다음 프레임에서 소유권이 바뀌는지 확인
            if idx+1 < len(possession_history):
                next_possessor = possession_history[idx+1]
                next_team = team_ids[idx+1][next_possessor] if next_possessor is not None and next_possessor < len(team_ids[idx+1]) else None
                if next_team is not None and next_team != scorer_team:
                    reset_needed = True
        # 2. 슛 후 득점이 아니고 리바운드 발생시 리셋
        elif rebound_events[idx] is not None:
            reset_needed = True
        # 3. 슛 없이 소유권이 다른팀으로 바뀌면 리셋
        elif idx > 0:
            prev_possessor = possession_history[idx-1]
            prev_team = team_ids[idx-1][prev_possessor] if prev_possessor is not None and prev_possessor < len(team_ids[idx-1]) else None
            curr_possessor = possession_history[idx]
            curr_team = team_ids[idx][curr_possessor] if curr_possessor is not None and curr_possessor < len(team_ids[idx]) else None
            if prev_team is not None and curr_team is not None and prev_team != curr_team:
                # 슛 이벤트가 없고, 득점/리바운드도 아닌 경우
                if shot_events[idx] is None and score_events[idx] is None and rebound_events[idx] is None:
                    reset_needed = True
        if reset_needed:
            # shot_clock을 12-(현재 서버시간-프레임 timestamp)초로 리셋
            shot_clock_action = 'reset'
            last_shot_clock_reset_time = current_server_time
            last_shot_clock_event_time = timestamps[idx]
            shot_clock = 12.0
        else:
            # shot_clock 유지, 경과시간만큼 1초 단위로 감소
            if last_shot_clock_reset_time is not None:
                elapsed = current_server_time - last_shot_clock_reset_time
                shot_clock = max(0.0, 12.0 - elapsed)
                shot_clock = int(shot_clock)  # 1초 단위로 내림
            else:
                shot_clock = 12.0
        event['shot_clock'] = int(shot_clock)
        event['shot_clock_action'] = shot_clock_action

        # timestamp를 시계 문자열로 변환
        event['timestamp'] = timestamp_to_str(current_server_time)

        # 결과 저장
        json_name = f'frame_{frame_id:04d}.json'
        json_path = os.path.join(RESULT_DIR, json_name)
        with open(json_path, 'w') as jf:
            json.dump(event, jf, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    main()
