import os
import json

def export_event_player_json(event_results_dir, tracking_output_dir, output_dir):
    """
    event_results_dir: 이벤트 결과 json들이 저장된 폴더
    tracking_output_dir: tracking_output/frame_XXXX.txt들이 저장된 폴더
    output_dir: 이벤트별 json을 저장할 폴더
    (각 txt파일의 각 줄에는 frame_id 칼럼이 없고, 파일명에서 frame_id를 추출)
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    # event_results 폴더의 모든 json 파일 순회
    for fname in sorted(os.listdir(event_results_dir)):
        if not fname.endswith('.json'):
            continue
        frame_id = int(fname.split('_')[1].split('.')[0])
        # 이벤트 결과 읽기
        with open(os.path.join(event_results_dir, fname), 'r') as f:
            event = json.load(f)
        # 이벤트 종류별로 처리
        for event_type in ['score', 'rebound', 'assist']:
            player_idx = event.get(event_type)
            if player_idx is not None:
                # 해당 프레임의 tracking_output에서 선수 좌표와 track_id 찾기
                track_txt = os.path.join(tracking_output_dir, f'frame_{frame_id:04d}.txt')
                if not os.path.exists(track_txt):
                    continue
                with open(track_txt, 'r') as tf:
                    lines = [line.strip().split() for line in tf if line.strip()]
                # 선수만 (class_id==1)
                players = [l for l in lines if l[0] == '1']
                if player_idx < len(players):
                    p = players[player_idx]
                    # tracking_output: <class_id> <x_center> <y_center> <width> <height> <track_id>
                    track_id = int(p[5])
                    x = float(p[1])
                    y = float(p[2])
                    # 이벤트 json 저장
                    out = {
                        'frame_id': frame_id,
                        'event': event_type,
                        'track_id': track_id,
                        'position': [x, y],
                        'timestamp': event['timestamp']
                    }
                    out_name = f'{event_type}_frame_{frame_id:04d}_track_{track_id}.json'
                    out_path = os.path.join(output_dir, out_name)
                    with open(out_path, 'w') as jf:
                        json.dump(out, jf, ensure_ascii=False, indent=2) 