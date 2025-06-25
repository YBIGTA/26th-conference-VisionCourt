# visioncourt

## 프로젝트 개요

**visioncourt**는 농구 경기의 프레임별 detection/tracking 데이터를 분석하여, 소유권, 슛, 득점, 리바운드, 어시스트 등 주요 이벤트를 자동으로 판별하고, 팀/선수별 기록을 산출하는 파이프라인입니다.

---

## 전체 프로세스 요약

1. **입력 데이터**
   - `data/detection_output/`: 프레임별 detection 결과(txt, 정규화 좌표)
   - `data/tracking_output/`: 프레임별 tracking 결과(txt, 선수별 track_id)

2. **분석 파이프라인**
   - `scripts/run_analysis.py` 실행 시 아래 순서로 처리
     1. **프레임별 detection 데이터 로딩**
     2. **공 바운딩박스 보정**: detection 누락 구간은 최근 궤적/포물선(2차 회귀) 보간으로 가상 공 위치 생성
     3. **이벤트 판별**
        - **소유권**: 공과 가장 가까운 선수의 team_id가 15프레임 이상 연속되면 소유권 인정. 시작 15프레임은 1프레임 기준 강제.
        - **슛**: 공 바운딩박스가 림 바운딩박스에 처음 겹치는 순간(이전 프레임은 겹치지 않고 이번 프레임은 겹칠 때), 이전 소유권 팀이 슛을 쏜 것으로 기록
        - **득점**: 슛 이후 공이 사라졌다가 다시 나타날 때, 사라지기 전 마지막 위치와 다시 나타난 첫 위치를 잇는 선과 림 중심의 거리가 0.005 이하이면 득점으로 간주
        - **리바운드**: 슛 후 득점이 아니고, 다음 소유권이 다른 팀으로 넘어가면 리바운드
        - **어시스트**: 득점 직전 마지막 소유권자가 슛 팀과 다르고, 같은 팀이면 어시스트
     4. **샷클락/메인클락 관리**: 이벤트 발생 시 shot_clock 리셋 등
     5. **결과 저장**: `event_results/frame_XXXX.json`에 프레임별 이벤트/클락/거리 등 기록

3. **출력 데이터**
   - `event_results/`: 프레임별 이벤트 결과(json)
     - 주요 필드: `frame_id`, `main_clock`, `shot_clock`, `possession`, `shot`, `score`, `rebound`, `assist`, `timestamp`, `ball_rim_dist`(득점 판정에 사용된 거리)
   - (선택) `player_event_results/`: 선수별 이벤트 기록(json)

---

## 주요 로직 및 함수 설명

### 1. **공 바운딩박스 보정 (interpolation/extrapolation)**
- detection에서 공이 사라진 구간은 최근 7프레임의 중심좌표로 2차(포물선) 회귀하여 궤적을 예측
- 슛-림 사이 구간에서 detection이 없으면 이 궤적을 사용
- 림에 닿으면 보정 종료

### 2. **소유권(get_possession)**
- 공과 가장 가까운 선수의 team_id가 15프레임 이상 연속되면 소유권 인정
- 시작 15프레임은 1프레임에서 공과 가장 가까운 팀으로 강제

### 3. **슛(detect_shot)**
- 공 바운딩박스가 림 바운딩박스에 처음 겹치는 순간(이전 프레임은 겹치지 않고 이번 프레임은 겹칠 때),
  이전 프레임의 소유권 팀이 슛을 쏜 것으로 기록

### 4. **득점(detect_score)**
- 슛 이후 공이 사라졌다가 다시 나타날 때, 사라지기 전 마지막 위치와 다시 나타난 첫 위치를 잇는 선과 림 중심의 거리가 0.005 이하이면 득점으로 간주
- 해당 거리(`ball_rim_dist`)는 event json에 기록

### 5. **리바운드/어시스트**
- 리바운드: 슛 후 득점이 아니고, 다음 소유권이 다른 팀으로 넘어가면 리바운드
- 어시스트: 득점 직전 마지막 소유권자가 슛 팀과 다르고, 같은 팀이면 어시스트

### 6. **샷클락/메인클락 관리**
- shot, score, rebound, 소유권 변경 등 이벤트 발생 시 shot_clock을 12초로 리셋
- main_clock은 프레임별로 자동 감소

---

## 실행 방법

```bash
# 분석 실행
PYTHONPATH=. python3 scripts/run_analysis.py
```

- 결과는 `event_results/` 폴더에 프레임별 json으로 저장됩니다.

---

## 데이터 포맷 예시

### detection_output (txt)
```
<date> <time> <class_id> <x_center> <y_center> <width> <height> <team_id>
```

### event_results/frame_XXXX.json
```
{
  "frame_id": 123,
  "main_clock": "09:58",
  "shot_clock": 10,
  "shot_clock_action": null,
  "possession": 1,
  "shot": 1,
  "score": 1,
  "rebound": null,
  "assist": null,
  "timestamp": "19:47:39.947",
  "ball_rim_dist": 0.0032
}
```

---

## 참고/특이사항
- 모든 좌표/거리는 0~1 정규화 기준
- 공이 detection에서 사라진 구간도 보정된 바운딩박스를 사용
- 소유권/이벤트는 팀번호(team_id) 기준으로만 기록
- 파라미터(프레임 수, 거리 임계값 등)는 코드에서 쉽게 조정 가능

---

## 문의/기여
- 코드 개선, 로직 제안, 버그 제보 등 언제든 환영합니다! 