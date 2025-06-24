import os
from basketball_event.player_event_stats import export_event_player_json

if __name__ == '__main__':
    event_results_dir = os.path.join(os.path.dirname(__file__), '..', 'event_results')
    tracking_output_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'tracking_output')
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'player_event_results')
    export_event_player_json(event_results_dir, tracking_output_dir, output_dir)
    print(f'이벤트별 선수 기록 json이 {output_dir}에 생성되었습니다.') 