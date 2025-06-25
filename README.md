# visioncourt

## 프로젝트 구조

```
visioncourt/
│
├── basketball_event/
│   ├── __init__.py
│   ├── detector.py              # 농구 이벤트(소유권, 슛, 득점, 리바운드, 어시스트) 판별 함수 모듈
│   └── player_event_stats.py    # 이벤트별 선수(track_id) 기록 추출 함수 모듈
│
├── scripts/
│   ├── run_analysis.py          # detection_output을 분석해 event_results 생성
│   └── run_player_stats.py      # event_results, tracking_output을 분석해 player_event_results 생성
│
├── data/
│   └── detection_output/        # 프레임별 detection 더미 데이터(txt)
│   └── tracking_output/         # 프레임별 tracking 더미 데이터(txt)
│
├── event_results/               # 프레임별 이벤트 분석 결과(json)
│
├── player_event_results/        # 이벤트별 선수 기록 결과(json)
│
└── README.md                    # (본 문서)
```

---

## 1. 주요 모듈 및 스크립트 설명

### `basketball_event/detector.py`
- **역할**: 프레임별 detection 데이터로부터 농구 이벤트(소유권, 슛, 득점, 리바운드, 어시스트)를 판별하는 함수 제공
- **주요 함수**
  - `get_possession(frames, ...)` : 공 소유 선수 인덱스 판별
  - `detect_shot(frames, possession_history, ...)` : 슛 이벤트 감지 (진행방향 불연속, 득점 포함)
  - `detect_score(frames, shot_events, ...)` : 득점 이벤트 감지
  - `detect_rebound(frames, ...)` : 리바운드 이벤트 감지
  - `detect_assist(frames, ...)` : 어시스트 이벤트 감지

### `basketball_event/player_event_stats.py`
- **역할**: 이벤트 결과와 tracking_output을 매칭하여, 득점/리바운드/어시스트가 발생한 선수의 track_id, 좌표, timestamp를 이벤트별 json으로 저장
- **주요 함수**
  - `export_event_player_json(event_results_dir, tracking_output_dir, output_dir)`
    - 각 이벤트별로 json 파일(`score_frame_0004_track_3.json` 등) 생성

### `scripts/run_analysis.py`
- **역할**: detection_output의 프레임별 txt를 분석하여 event_results 폴더에 프레임별 이벤트 결과(json) 생성
- **주요 동작**
  - main_clock, shot_clock, possession, shot, score, rebound, assist 등 기록

### `scripts/run_player_stats.py`
- **역할**: event_results와 tracking_output을 분석하여 player_event_results 폴더에 이벤트별 선수 기록(json) 생성
- **주요 동작**
  - 득점/리바운드/어시스트가 발생한 선수의 track_id, 좌표, timestamp를 json으로 저장

---

## 2. 더미 데이터셋 포맷

### `data/detection_output/frame_XXXX.txt`
- 각 프레임별 detection 결과
- **frame_id는 파일명(`frame_0001.txt` 등)에서 추출하며, 각 줄에는 frame_id 칼럼이 없음**
- 포맷:  
  ```
  <class_id> <x_center> <y_center> <width> <height> <team_id> <timestamp>
  ```
  - class_id: 0=공, 1=선수, 2=림
  - team_id: 선수만 0/1, 공/림은 0
  - timestamp: 해당 프레임의 서버시간(초, float)

### `data/tracking_output/frame_XXXX.txt`
- 각 프레임별 tracking 결과 (선수만)
- **frame_id는 파일명(`frame_0001.txt` 등)에서 추출하며, 각 줄에는 frame_id 칼럼이 없음**
- 포맷:  
  ```
  <class_id> <x_center> <y_center> <width> <height> <track_id>
  ```
  - class_id: 1(선수)
  - track_id: 1~6 (선수별 고유번호)

---

## 3. 결과 데이터 포맷

### `event_results/frame_XXXX.json`
- 프레임별 이벤트 분석 결과
- 주요 필드:
  - main_clock: "MM:SS"
  - shot_clock: int(초)
  - possession, shot, score, rebound, assist: 선수 인덱스(없으면 null)
  - timestamp: "YYYY-MM-DD HH:MM:SS.sss"

### `player_event_results/score_frame_XXXX_track_YY.json` 등
- 득점/리바운드/어시스트가 발생한 선수별 기록
- 주요 필드:
  - frame_id: int
  - event: "score" | "rebound" | "assist"
  - track_id: int (1~6)
  - position: [x, y]
  - timestamp: "YYYY-MM-DD HH:MM:SS.sss"

---

## 4. 실행 예시

1. **분석 실행**
   ```bash
   PYTHONPATH=. python3 scripts/run_analysis.py
   ```
   → event_results/에 프레임별 이벤트 결과 생성

2. **선수별 이벤트 기록 추출**
   ```bash
   PYTHONPATH=. python3 scripts/run_player_stats.py
   ```
   → player_event_results/에 이벤트별 선수 기록 json 생성

---

## 5. 참고

- 더미 데이터셋은 예시이므로 실제 분석을 위해서는 detection/tracking 모델의 출력 포맷에 맞게 데이터를 준비해야 합니다.
- detector.py의 파라미터(림 근처 거리, 각도 등)는 실제 데이터에 맞게 조정 가능합니다. 