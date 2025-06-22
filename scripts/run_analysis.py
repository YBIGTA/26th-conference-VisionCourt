# scripts/run_analysis.py

import os
import json
import pandas as pd
from basketball_event.detector import BasketballEventAnalyzer

def load_detection_data_from_folder(folder_path):
    """detection_output 폴더에서 프레임별 데이터 로드"""
    all_detections = []
    
    # 폴더 내 모든 txt 파일 읽기
    for filename in sorted(os.listdir(folder_path)):
        if filename.endswith('.txt') and filename.startswith('frame_'):
            file_path = os.path.join(folder_path, filename)
            
            with open(file_path, 'r') as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) != 7:  # frame_id, class_id, x_center, y_center, width, height, team_id
                        continue
                    frame_id, class_id, x_center, y_center, width, height, team_id = parts
                    all_detections.append({
                        'frame_id': int(frame_id),
                        'class_id': int(class_id),
                        'x_center': float(x_center),
                        'y_center': float(y_center),
                        'width': float(width),
                        'height': float(height),
                        'team_id': int(team_id)
                    })
    
    return all_detections

def load_tracking_data_from_folder(folder_path):
    """tracking_output 폴더에서 프레임별 데이터 로드"""
    all_tracks = []
    
    # 폴더 내 모든 txt 파일 읽기
    for filename in sorted(os.listdir(folder_path)):
        if filename.endswith('.txt') and filename.startswith('frame_'):
            file_path = os.path.join(folder_path, filename)
            
            with open(file_path, 'r') as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) != 6:  # frame_id, track_id, x_center, y_center, width, height
                        continue
                    frame_id, track_id, x_center, y_center, width, height = parts
                    all_tracks.append({
                        'frame_id': int(frame_id),
                        'track_id': int(track_id),
                        'x_center': float(x_center),
                        'y_center': float(y_center),
                        'width': float(width),
                        'height': float(height)
                    })
    
    return all_tracks

def frame_to_timestamp(frame_id, fps=30):
    """프레임 번호를 MM:SS:FF 형식의 timestamp로 변환"""
    total_seconds = frame_id / fps
    minutes = int(total_seconds // 60)
    seconds = int(total_seconds % 60)
    frames = int((total_seconds % 1) * fps)
    return f"{minutes:02d}:{seconds:02d}:{frames:02d}"

def determine_clock_actions(analysis_result, prev_shot_clock):
    """메인 클록과 샷클락 액션 결정"""
    main_clock_action = "start"  # 기본값
    shot_clock_action = "start"  # 기본값
    
    # 샷클락 리셋 조건 확인
    events = analysis_result['events']
    current_shot_clock = analysis_result['shot_clock']
    
    # 이벤트에 따른 샷클락 액션 결정
    for event in events:
        if event['type'] in ['score', 'rebound', 'shot']:
            shot_clock_action = "reset"
            break
    
    # 샷클락 위반 확인
    if any(event['type'] == 'shot_clock_violation' for event in events):
        shot_clock_action = "reset"
    
    # 샷클락이 12초에서 변경되었는지 확인
    if prev_shot_clock == 12 and current_shot_clock < 12:
        shot_clock_action = "start"
    
    return main_clock_action, shot_clock_action

def convert_event_to_format(event, team_mapping):
    """이벤트를 요구사항 형식으로 변환"""
    event_type = event['type']
    team = event.get('team')
    team_name = f"team_{team + 1}" if team is not None else None
    
    # 이벤트 타입 매핑
    event_mapping = {
        'shot': '2점슛 시도',
        'score': '2점슛 성공',
        'rebound': '리바운드',
        'assist': '어시스트',
        'shot_clock_violation': '샷클락 위반'
    }
    
    event_name = event_mapping.get(event_type, event_type)
    
    # 성공 여부 결정
    success = event_type in ['score', 'assist', 'rebound']
    
    # 점수 결정
    score = 2 if event_type == 'score' else 0
    
    return {
        "event": event_name,
        "team": team_name,
        "score": score,
        "success": success,
        "timestamp": frame_to_timestamp(event.get('frame_id', 0))
    }

def main():
    # 프로젝트 경로 설정
    scripts_dir = os.path.dirname(__file__)
    project_root = os.path.dirname(scripts_dir)
    
    # JSON 출력 폴더 생성
    json_output_dir = os.path.join(project_root, 'frame_events')
    os.makedirs(json_output_dir, exist_ok=True)
    
    # 분석기 초기화
    analyzer = BasketballEventAnalyzer(
        possession_iou_thresh=0.3,
        score_iou_thresh=0.2,
        player_match_thresh=0.5
    )
    
    # 데이터 폴더 경로
    detection_folder = os.path.join(project_root, 'data', 'detection_output')
    tracking_folder = os.path.join(project_root, 'data', 'tracking_output')
    
    # 폴더 존재 확인
    if not os.path.exists(detection_folder):
        print(f"❌ detection_output 폴더를 찾을 수 없습니다: {detection_folder}")
        return
    
    if not os.path.exists(tracking_folder):
        print(f"❌ tracking_output 폴더를 찾을 수 없습니다: {tracking_folder}")
        return
    
    print("📁 프레임별 데이터 파일을 로드합니다...")
    detection_data = load_detection_data_from_folder(detection_folder)
    tracking_data = load_tracking_data_from_folder(tracking_folder)
    
    print(f"✅ 첫 번째 모델 데이터: {len(detection_data)}개 레코드")
    print(f"✅ 두 번째 모델 데이터: {len(tracking_data)}개 레코드")
    
    # 프레임별로 데이터 그룹화
    detection_by_frame = {}
    tracking_by_frame = {}
    
    for det in detection_data:
        frame_id = det['frame_id']
        if frame_id not in detection_by_frame:
            detection_by_frame[frame_id] = []
        detection_by_frame[frame_id].append(det)
    
    for track in tracking_data:
        frame_id = track['frame_id']
        if frame_id not in tracking_by_frame:
            tracking_by_frame[frame_id] = []
        tracking_by_frame[frame_id].append(track)
    
    # 프레임 범위 확인
    all_frames = set(detection_by_frame.keys()) | set(tracking_by_frame.keys())
    if all_frames:
        min_frame = min(all_frames)
        max_frame = max(all_frames)
        print(f"📊 분석할 프레임 범위: {min_frame} ~ {max_frame}")
    else:
        print("❌ 분석할 데이터가 없습니다.")
        return
    
    prev_shot_clock = 12
    
    # 프레임별 분석 및 JSON 생성
    for frame_id in range(min_frame, max_frame + 1):
        frame_detections = detection_by_frame.get(frame_id, [])
        frame_tracks = tracking_by_frame.get(frame_id, [])
        
        if not frame_detections or not frame_tracks:
            continue
        
        # 프레임 분석 (프레임 ID 전달)
        analysis_result = analyzer.analyze_frame(frame_detections, frame_tracks, frame_id)
        
        # 클록 액션 결정
        main_clock_action, shot_clock_action = determine_clock_actions(analysis_result, prev_shot_clock)
        
        # JSON 데이터 구성
        frame_data = {
            "main_clock_action": main_clock_action,
            "shot_clock_action": shot_clock_action
        }
        
        # 이벤트가 있는 경우 이벤트 정보 추가
        if analysis_result['events']:
            events_data = []
            for event in analysis_result['events']:
                # 프레임 ID를 이벤트에 추가
                event['frame_id'] = frame_id
                event_data = convert_event_to_format(event, {})
                events_data.append(event_data)
            
            # 첫 번째 이벤트만 사용 (하나의 프레임에는 하나의 주요 이벤트만)
            if events_data:
                frame_data.update(events_data[0])
        
        # JSON 파일로 저장
        json_filename = f"frame_{frame_id:03d}.json"
        json_filepath = os.path.join(json_output_dir, json_filename)
        
        with open(json_filepath, 'w', encoding='utf-8') as f:
            json.dump(frame_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 프레임 {frame_id}: {json_filename} 생성됨")
        
        # 이전 샷클락 업데이트
        prev_shot_clock = analysis_result['shot_clock']
    
    print(f"\n🎉 모든 프레임 JSON 파일이 생성되었습니다: {json_output_dir}")

if __name__ == "__main__":
    main()
