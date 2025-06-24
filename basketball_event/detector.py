import math
from typing import List, Dict, Optional, Tuple

# 바운딩박스의 중심 좌표(x, y) 반환
def bbox_center(bbox):
    x, y, w, h = bbox
    return (x, y)

# 두 바운딩박스의 IoU(겹치는 비율) 계산
def bbox_iou(boxA, boxB):
    # box: (x_center, y_center, w, h)
    xA1, yA1 = boxA[0] - boxA[2]/2, boxA[1] - boxA[3]/2
    xA2, yA2 = boxA[0] + boxA[2]/2, boxA[1] + boxA[3]/2
    xB1, yB1 = boxB[0] - boxB[2]/2, boxB[1] - boxB[3]/2
    xB2, yB2 = boxB[0] + boxB[2]/2, boxB[1] + boxB[3]/2
    inter_x1 = max(xA1, xB1)
    inter_y1 = max(yA1, yB1)
    inter_x2 = min(xA2, xB2)
    inter_y2 = min(yA2, yB2)
    inter_area = max(0, inter_x2 - inter_x1) * max(0, inter_y2 - inter_y1)
    areaA = (xA2 - xA1) * (yA2 - yA1)
    areaB = (xB2 - xB1) * (yB2 - yB1)
    if areaA + areaB - inter_area == 0:
        return 0
    return inter_area / (areaA + areaB - inter_area)

# 두 점 (x, y) 사이의 유클리드 거리 계산
def euclidean(p1, p2):
    return math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)

# 프레임의 detection 리스트에서 공, 림, 선수 정보 분리
def parse_frame_detections(detections):
    ball = None
    rim = None
    players = []
    for det in detections:
        class_id, x, y, w, h, team_id = det
        if class_id == 0:
            ball = (x, y, w, h)
        elif class_id == 1:
            players.append({'bbox': (x, y, w, h), 'team_id': team_id})
        elif class_id == 2:
            rim = (x, y, w, h)
    return ball, players, rim

def get_possession(frames: List[List[List[float]]], min_frames: int = 3, dist_thresh: float = 50) -> List[Optional[int]]:
    """
    각 프레임별로 소유권(선수 인덱스)을 반환. min_frames 이상 연속 소유시 확정.
    반환: [None, 2, 2, 2, 3, ...] (프레임별 소유 선수 인덱스)
    """
    possession_history = []
    last_owner = None
    owner_count = 0
    for frame_idx, detections in enumerate(frames):
        ball, players, rim = parse_frame_detections(detections)
        if not ball or not players:
            possession_history.append(None)
            last_owner = None
            owner_count = 0
            continue
        ball_center = bbox_center(ball)
        min_dist = float('inf')
        owner = None
        for idx, player in enumerate(players):
            player_center = bbox_center(player['bbox'])
            dist = euclidean(ball_center, player_center)
            if dist < min_dist:
                min_dist = dist
                owner = idx
        if min_dist < dist_thresh:
            if owner == last_owner:
                owner_count += 1
            else:
                owner_count = 1
                last_owner = owner
            if owner_count >= min_frames:
                possession_history.append(owner)
            else:
                possession_history.append(None)
        else:
            possession_history.append(None)
            last_owner = None
            owner_count = 0
    return possession_history

def detect_shot(
    frames: List[List[List[float]]],
    possession_history: List[Optional[int]],
    rim_dist_thresh: float = 100,
    traj_window: int = 4,
    angle_thresh: float = 45.0,
    score_events: Optional[List[Optional[int]]] = None
) -> List[Optional[int]]:
    """
    득점이 발생한 경우 무조건 슛으로 간주하고,
    림 근처 도달 전 최근 N프레임의 공 궤적에서 진행방향이 불연속(각도 변화가 angle_thresh 이상)인 경우도 슛으로 판정.
    반환: [None, None, 2, None, ...] (슛 발생시 소유자 인덱스)
    """
    shot_events = [None] * len(frames)
    ball_traj = []  # 최근 traj_window 프레임의 공 중심 좌표
    prev_owner = None
    for i, detections in enumerate(frames):
        ball, players, rim = parse_frame_detections(detections)
        owner = possession_history[i]
        if ball:
            ball_traj.append(bbox_center(ball))
            if len(ball_traj) > traj_window:
                ball_traj.pop(0)
        # 1. 득점이 발생한 경우 무조건 슛으로 간주
        if score_events is not None and score_events[i] is not None:
            shot_events[i] = score_events[i]
            prev_owner = owner
            continue
        # 2. 림 근처 도달 + 진행방향 불연속성 체크
        if ball and rim and euclidean(bbox_center(ball), bbox_center(rim)) < rim_dist_thresh:
            if len(ball_traj) == traj_window:
                v1 = (ball_traj[-2][0] - ball_traj[-3][0], ball_traj[-2][1] - ball_traj[-3][1])
                v2 = (ball_traj[-1][0] - ball_traj[-2][0], ball_traj[-1][1] - ball_traj[-2][1])
                dot = v1[0]*v2[0] + v1[1]*v2[1]
                mag1 = math.hypot(*v1)
                mag2 = math.hypot(*v2)
                if mag1 > 0 and mag2 > 0:
                    cos_theta = dot / (mag1 * mag2)
                    angle = math.degrees(math.acos(max(-1, min(1, cos_theta))))
                    if angle > angle_thresh:
                        shot_events[i] = prev_owner
        prev_owner = owner
    return shot_events

def detect_score(frames: List[List[List[float]]], shot_events: List[Optional[int]], iou_thresh: float = 0.2) -> List[Optional[int]]:
    """
    득점 발생 프레임 인덱스 반환. 공이 림 바운딩박스와 겹치면 득점.
    반환: [None, None, None, 3, ...] (득점시 슛 선수 인덱스)
    """
    score_events = [None] * len(frames)
    for i, detections in enumerate(frames):
        ball, players, rim = parse_frame_detections(detections)
        if not ball or not rim:
            continue
        iou = bbox_iou(ball, rim)
        if iou > iou_thresh:
            # 직전 프레임에서 슛이 있었는지 확인
            for j in range(i-1, -1, -1):
                if shot_events[j] is not None:
                    score_events[i] = shot_events[j]
                    break
    return score_events

def detect_rebound(frames: List[List[List[float]]], shot_events: List[Optional[int]], score_events: List[Optional[int]], possession_history: List[Optional[int]]) -> List[Optional[int]]:
    """
    리바운드 발생 프레임 인덱스 반환. 슛 후 득점이 아니고, 다음 소유권이 다른 선수로 넘어가면 리바운드.
    반환: [None, None, None, 2, ...] (리바운드 선수 인덱스)
    """
    rebound_events = [None] * len(frames)
    last_shot_idx = None
    for i in range(1, len(frames)):
        if shot_events[i-1] is not None:
            last_shot_idx = i-1
        if last_shot_idx is not None and score_events[i] is None:
            # 득점이 아니고, 소유권이 새로 생김
            if possession_history[i] is not None and possession_history[i-1] is None:
                rebound_events[i] = possession_history[i]
                last_shot_idx = None  # 한 번만 체크
        if score_events[i] is not None:
            last_shot_idx = None
    return rebound_events

def detect_assist(frames: List[List[List[float]]], shot_events: List[Optional[int]], score_events: List[Optional[int]], possession_history: List[Optional[int]], team_ids: List[List[int]]) -> List[Optional[int]]:
    """
    어시스트 발생 프레임 인덱스 반환. 득점 직전 마지막 소유권자가 슛 선수와 다르고, 같은 팀이면 어시스트.
    team_ids: 각 프레임별 선수들의 team_id 리스트
    반환: [None, None, None, 1, ...] (어시스트 선수 인덱스)
    """
    assist_events = [None] * len(frames)
    for i, scorer in enumerate(score_events):
        if scorer is not None:
            # 득점 직전 마지막 소유권자 찾기
            for j in range(i-1, -1, -1):
                if possession_history[j] is not None:
                    if possession_history[j] != scorer:
                        # 같은 팀인지 확인
                        scorer_team = team_ids[i][scorer] if scorer < len(team_ids[i]) else None
                        assist_team = team_ids[j][possession_history[j]] if possession_history[j] < len(team_ids[j]) else None
                        if scorer_team is not None and assist_team is not None and scorer_team == assist_team:
                            assist_events[i] = possession_history[j]
                    break
    return assist_events

