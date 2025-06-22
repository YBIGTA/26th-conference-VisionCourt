# VisionCourt - Basketball Event Analysis System

## 프로젝트 개요

VisionCourt는 컴퓨터 비전을 활용한 농구 이벤트 분석 시스템입니다. 두 개의 컴퓨터 비전 모델(Detection 모델과 Tracking 모델)의 출력을 결합하여 농구 경기 중 발생하는 이벤트(득점, 리바운드, 어시스트, 슛 등)를 실시간으로 감지하고 분석합니다.

## 프로젝트 구조

```
visioncourt/
├── basketball_event/          # 핵심 분석 모듈
│   ├── __init__.py
│   └── detector.py           # BasketballEventAnalyzer 클래스
├── data/                     # 입력 데이터
│   ├── detection_output/     # Detection 모델 출력 (프레임별 txt 파일)
│   └── tracking_output/      # Tracking 모델 출력 (프레임별 txt 파일)
├── event_results/            # 분석 결과 출력
│   └── frame_*.json         # 프레임별 이벤트 JSON 파일
├── scripts/                  # 실행 스크립트
│   └── run_analysis.py      # 메인 분석 실행 스크립트
└── README.md
```

## 주요 기능

### 1. 이벤트 감지
- **슛 감지**: 볼이 림을 향해 이동하며 방향/가속도 변화 시 감지
- **득점 감지**: 볼이 림 근처에서 방향 변화 시 감지
- **리바운드 감지**: 득점 후 볼 소유권 변경 시 감지
- **어시스트 감지**: 슛 시도 후 득점 시 마지막 패스 선수 감지
- **골밑슛 감지**: 낮은 궤적과 수평 이동 패턴으로 감지

### 2. 클록 관리
- **메인 클록**: 경기 시간 관리
- **샷 클록**: 3x3 농구 규칙에 따른 12초 샷 클록
- **클록 액션**: start, pause, reset 상태 관리

### 3. 통계 추적
- 팀별 득점, 리바운드, 어시스트, 슛 시도 통계
- 개인별 선수 통계 (track_id 기반)
- 볼 소유권 추적

## 입력 데이터 형식

### Detection 모델 출력 (detection_output/frame_*.txt)
```
frame_id class_id x_center y_center width height team_id
```
- `class_id`: 0=볼, 1=선수, 2=림
- `team_id`: 0=팀A, 1=팀B

### Tracking 모델 출력 (tracking_output/frame_*.txt)
```
frame_id track_id x_center y_center width height
```
- `track_id`: 1~6 (개별 선수 식별)

## 출력 데이터 형식

### 이벤트 결과 (event_results/frame_*.json)
```json
{
  "main_clock_action": "start",
  "shot_clock_action": "start",
  "events": [
    {
      "event": "2점슛 성공",
      "team": "team_1",
      "score": 2,
      "success": true,
      "timestamp": "00:00:15"
    }
  ]
}
```

## 기술적 특징

### 1. 고급 이벤트 감지 알고리즘
- **볼 궤적 분석**: 최대 30프레임의 볼 궤적 추적
- **속도/가속도 분석**: 볼의 물리적 움직임 패턴 분석
- **2D 매핑**: 코트 좌표계 변환을 통한 정확한 거리 계산
- **IoU 기반 매칭**: 선수 detection과 tracking 데이터 매칭

### 2. 3x3 농구 규칙 적용
- 12초 샷 클록
- 득점 시 샷 클록 리셋
- 리바운드 시 샷 클록 리셋

### 3. 실시간 처리
- 프레임별 실시간 분석
- 30fps 기준 타임스탬프 생성
- 상태 기반 이벤트 감지

## 사용 방법

### 1. 환경 설정
```bash
cd /path/to/visioncourt
```

### 2. 데이터 준비
- `data/detection_output/` 폴더에 프레임별 detection 결과 파일 배치
- `data/tracking_output/` 폴더에 프레임별 tracking 결과 파일 배치

### 3. 분석 실행
```bash
python scripts/run_analysis.py
```

### 4. 결과 확인
- `event_results/` 폴더에서 프레임별 JSON 결과 파일 확인

## 이벤트 감지 로직

### 슛 감지
1. 볼이 선수로부터 떨어짐 확인
2. 볼이 림을 향해 이동하는지 확인
3. 림 근처(100픽셀 이내)에서 방향/가속도 변화 감지
4. 조건 만족 시 슛 이벤트 발생

### 득점 감지
1. 볼이 림 근처에서 방향 변화 감지
2. 이전 프레임과 현재 프레임의 방향 벡터 계산
3. 내적(dot product) < 0.8 시 득점으로 판정

### 리바운드 감지
1. 득점 이벤트 발생 후
2. 볼 소유권이 변경되는 시점 감지
3. 새로운 소유자가 리바운드로 판정

### 어시스트 감지
1. 슛 시도 후 득점 발생 시
2. 슛 시도 전 마지막 패스 선수 감지
3. 해당 선수를 어시스트로 판정

## 클록 관리 로직

### 샷 클록
- **시작**: 볼 소유권 획득 시
- **리셋**: 득점, 리바운드, 슛 시도 시
- **위반**: 12초 경과 시

### 메인 클록
- 경기 시작부터 종료까지 연속 실행
- 이벤트 발생 시에도 계속 진행

## 향후 개발 계획

### 1. 2D 매핑 고도화
- 코트 좌표계 정확도 향상
- 실제 거리 기반 이벤트 감지
- 3D 공간 분석 도입

### 2. 이벤트 감지 정확도 향상
- 머신러닝 기반 패턴 학습
- 더 정교한 물리적 모델링
- 노이즈 필터링 개선

### 3. 실시간 스트리밍 지원
- 실시간 비디오 스트림 처리
- 지연 시간 최소화
- 웹 인터페이스 개발

## 기술 스택

- **Python**: 메인 개발 언어
- **NumPy**: 수치 계산 및 배열 처리
- **Pandas**: 데이터 처리 및 분석
- **JSON**: 결과 데이터 직렬화

## 라이선스

이 프로젝트는 교육 및 연구 목적으로 개발되었습니다.

## 기여

프로젝트 개선을 위한 제안이나 버그 리포트는 언제든 환영합니다. 