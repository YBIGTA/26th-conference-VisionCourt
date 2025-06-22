# VisionCourt - Basketball Event Analysis System

농구 경기의 컴퓨터 비전 모델 출력을 분석하여 슛, 득점, 리바운드, 어시스트 등의 이벤트를 자동으로 감지하고 통계를 산출하는 시스템입니다.

## 🏀 프로젝트 개요

VisionCourt는 두 개의 컴퓨터 비전 모델의 출력을 병합하여 농구 경기의 이벤트를 실시간으로 분석합니다:

- **첫 번째 모델**: Detection 모델 (볼, 선수, 림 감지 + 팀 구분)
- **두 번째 모델**: Tracking 모델 (선수 추적)

## 📁 프로젝트 구조

```
visioncourt/
├── basketball_event/
│   ├── __init__.py
│   ├── detector.py          # 이벤트 감지 핵심 로직
├── data/
│   ├── detection_output/    # 첫 번째 모델 출력 (프레임별 txt)
│   ├── tracking_output/     # 두 번째 모델 출력 (프레임별 txt)
├── frame_events/           # 분석 결과 JSON 파일들
├── scripts/
│   └── run_analysis.py     # 메인 분석 스크립트
└── README.md
```

## 🎯 주요 기능

### 이벤트 감지
- **슛 (Shot)**: 득점 또는 림 근처에서의 방향/가속도 변화
- **득점 (Score)**: 볼이 림을 통과하는 패턴 감지
- **리바운드 (Rebound)**: 슛 실패 후 볼을 잡는 패턴
- **어시스트 (Assist)**: 득점 직전 패스한 선수 감지

### 클록 관리
- **샷클락**: 3x3 농구 규칙 (12초)
- **메인 클록**: 게임 진행 상태 관리

### 통계 산출
- 팀별 통계 (득점, 리바운드, 어시스트, 슛 시도)
- 개인별 통계 (track_id 1~6)

## 🚀 사용법

### 1. 환경 설정
```bash
# 프로젝트 디렉토리로 이동
cd visioncourt

# Python 환경 설정 (가상환경 권장)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 필요한 패키지 설치
pip install numpy pandas
```

### 2. 데이터 준비
두 모델의 출력을 다음 형식으로 준비:

**Detection 모델 출력** (`data/detection_output/frame_XXX.txt`):
```
frame_id class_id x_center y_center width height team_id
```
- `class_id`: 0=볼, 1=선수, 2=림
- `team_id`: 0=팀A, 1=팀B

**Tracking 모델 출력** (`data/tracking_output/frame_XXX.txt`):
```
frame_id track_id x_center y_center width height
```
- `track_id`: 1~6 (선수 추적 ID)

### 3. 분석 실행
```bash
# PYTHONPATH 설정 후 분석 실행
PYTHONPATH=/path/to/visioncourt python scripts/run_analysis.py
```

### 4. 결과 확인
- **JSON 파일**: `frame_events/frame_XXX.json` (프레임별 이벤트)
- **통계 파일**: `game_statistics.csv`, `player_statistics.csv`

## 📊 이벤트 감지 로직

### 슛 (Shot) 감지
```python
def detect_shot_advanced(self, ball, hoop, current_possessor, current_team):
```

**조건:**
1. **득점 발생** → 자동으로 슛 시도도 함께 기록
2. **볼이 림을 향하고 림 근처에서 부딪혀서 진행방향 또는 가속도 변화**
   - 볼이 림 방향으로 이동 (이전 프레임 대비 거리 감소)
   - 림 100픽셀 이내
   - 진행방향 변화: 최근 3프레임 방향 벡터 내적 < 0.7
   - 가속도 변화: 최근 가속도 절댓값 > 100

### 득점 (Score) 감지
```python
def detect_score_advanced(self, ball, hoop):
```

**조건:**
- 볼이 림 근처에 있는지 확인 (IoU + 거리 기반)
- 볼이 림 위에 있는지 확인 (y좌표가 림보다 위)
- 볼이 림 근처에 3프레임 이상 머무름
- 볼이 림 위에 2프레임 이상 머무름
- 볼이 아래로 떨어지는지 확인 (득점 후)

### 리바운드 (Rebound) 감지
```python
def detect_rebound_advanced(self, ball, players, current_possessor):
```

**조건:**
- 볼이 아래로 떨어지는지 확인
- 볼이 림 근처에서 튕겨나왔는지 확인 (위로 올라갔다가 아래로 떨어지는 패턴)
- 가장 가까운 선수 찾기
- 선수가 볼 80픽셀 이내에 있고, 볼 소유권이 변경되었는지 확인

### 어시스트 (Assist) 감지
```python
def detect_assist_advanced(self, ball, players, current_possessor, current_team):
```

**조건:**
- 최근에 득점이 발생했는지 확인 (5프레임 이내)
- 득점 직전에 볼을 소유했던 선수가 다른 팀인지 확인
- 슛 시도 후 3프레임 이내에 득점
- 이전 볼 소유자 찾기

## ⏰ 클록 관리 로직

### 샷클락 (Shot Clock) - 3x3 농구 규칙
```python
def update_shot_clock(self, events, current_possessor, current_team):
```

**초기값:** 12초

**리셋 조건:**
- 득점 발생
- 리바운드 발생  
- 슛 시도 발생

**시작 조건:**
- 볼 소유권이 변경되었을 때

**감소:**
- 프레임당 약 0.033초 (30fps 기준)
- `shot_clock = max(0, 12 - time_elapsed)`

**위반 감지:**
- 샷클락이 0 이하가 되면 `shot_clock_violation` 이벤트 발생
- 자동으로 12초로 리셋

## 📄 출력 형식

### JSON 파일 형식 (`frame_events/frame_XXX.json`)
```json
{
  "main_clock_action": "start/pause/reset",
  "shot_clock_action": "start/pause/reset",
  "event": "2점슛 시도/2점슛 성공/리바운드/어시스트",
  "team": "team_1/team_2",
  "score": 2,
  "success": true/false,
  "timestamp": "MM:SS:FF"
}
```

### 이벤트 타입
- `2점슛 시도`: 슛 시도 감지
- `2점슛 성공`: 득점 감지
- `리바운드`: 리바운드 감지
- `어시스트`: 어시스트 감지
- `샷클락 위반`: 샷클락 위반 감지

## 🔧 기술적 특징

### 2D 매핑 대비
- 향후 2D 매핑에서도 동일한 로직 적용 가능
- 실제 농구장 좌표계로 변환 시 더 정확한 판정 가능

### 시간 기반 감지
- 단순 겹침이 아닌 시간적 패턴 분석
- 여러 프레임의 정보를 종합적으로 활용

### 3x3 농구 규칙
- 12초 샷클락
- 2점 득점
- 3명 vs 3명 경기 규칙 반영

## 📈 성능 최적화

### 프레임 분석 범위
- **이벤트 감지**: 주로 이전 프레임과 현재 프레임 (2프레임)
- **볼 궤적**: 최대 30프레임 저장
- **속도/가속도**: 최근 10프레임 히스토리

### 임계값 설정
- **소유권 판별**: IoU > 0.3
- **득점 감지**: IoU > 0.2
- **선수 매칭**: IoU > 0.5
- **방향 변화**: 내적 < 0.7
- **가속도 변화**: 절댓값 > 100

## 🚀 향후 개발 계획

1. **2D 매핑 통합**: 실제 농구장 좌표계 적용
2. **다중 앵글 지원**: 여러 카메라 앵글 융합
3. **실시간 분석**: 실시간 스트리밍 지원
4. **웹 인터페이스**: 실시간 대시보드 개발
5. **AI 모델 통합**: 더 정확한 객체 감지 모델 적용

## 📝 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 🤝 기여하기

버그 리포트, 기능 제안, 코드 기여를 환영합니다. Pull Request를 통해 기여해 주세요.

## 📞 문의

프로젝트에 대한 문의사항이 있으시면 이슈를 생성해 주세요. 
