import math
from typing import List, Dict, Optional, Tuple
import numpy as np

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

def get_possession(
    frames: List[List[List[float]]],
    min_frames: int = 15,
    dist_thresh: float = 0.01,
    initial_frames: int = 15
) -> List[int]:
    """
    각 프레임별로 소유권(실제 팀번호, team_id)을 반환. min_frames 이상 연속 소유시 확정.
    시작 initial_frames 프레임은 1프레임에서 공과 가장 가까운 선수의 team_id로 강제.
    반환: [0, 0, 0, 1, 1, ...] (프레임별 소유 팀번호)
    """
    possession_history = []
    last_team_id = None
    owner_count = 0
    for frame_idx, detections in enumerate(frames):
        ball, players, rim = parse_frame_detections(detections)
        if not ball or not players:
            possession_history.append(last_team_id)
            owner_count = 0
            continue
        ball_center = bbox_center(ball)
        min_dist = float('inf')
        owner_team_id = None
        for player in players:
            player_center = bbox_center(player['bbox'])
            dist = euclidean(ball_center, player_center)
            if dist < min_dist:
                min_dist = dist
                owner_team_id = player['team_id']
        if min_dist < dist_thresh:
            if owner_team_id == last_team_id:
                owner_count += 1
            else:
                owner_count = 1
                last_team_id = owner_team_id
            if owner_count >= min_frames:
                possession_history.append(owner_team_id)
            else:
                possession_history.append(last_team_id)
        else:
            possession_history.append(last_team_id)
            owner_count = 0
    # 시작 initial_frames 프레임은 1프레임에서 공과 가장 가까운 선수의 team_id로 강제
    if len(frames) > 0 and initial_frames > 0:
        first_ball, first_players, _ = parse_frame_detections(frames[0])
        if first_ball and first_players:
            ball_center = bbox_center(first_ball)
            min_dist = float('inf')
            first_team_id = None
            for player in first_players:
                player_center = bbox_center(player['bbox'])
                dist = euclidean(ball_center, player_center)
                if dist < min_dist:
                    min_dist = dist
                    first_team_id = player['team_id']
            for i in range(min(initial_frames, len(possession_history))):
                possession_history[i] = first_team_id
    # None이 남아있으면 마지막 값으로 채움
    for i in range(len(possession_history)):
        if possession_history[i] is None:
            possession_history[i] = possession_history[i-1] if i > 0 else 0
    return possession_history

def detect_shot(
    frames: List[List[List[float]]],
    possession_history: List[Optional[int]],
    score_events: Optional[List[Optional[int]]] = None
) -> List[Optional[int]]:
    """
    슛: 공 바운딩박스가 림 바운딩박스에 처음 겹치는 순간(이전 프레임은 겹치지 않고 이번 프레임은 겹칠 때),
    이전 소유권 팀이 슛을 쏜 것으로 기록. 연속 겹침 구간에서는 한 번만 기록.
    득점이 발생한 경우도 슛으로 간주.
    반환: [None, None, 0, None, ...] (슛 발생시 소유 팀번호)
    """
    shot_events = [None] * len(frames)
    prev_owner = None
    prev_rim_overlap = False
    for i, detections in enumerate(frames):
        ball, players, rim = parse_frame_detections(detections)
        owner_team = possession_history[i]
        if not ball or not rim:
            prev_owner = owner_team
            prev_rim_overlap = False
            continue
        bx1, by1 = ball[0] - ball[2]/2, ball[1] - ball[3]/2
        bx2, by2 = ball[0] + ball[2]/2, ball[1] + ball[3]/2
        rx1, ry1 = rim[0] - rim[2]/2, rim[1] - rim[3]/2
        rx2, ry2 = rim[0] + rim[2]/2, rim[1] + rim[3]/2
        rim_overlap = not (bx2 < rx1 or bx1 > rx2 or by2 < ry1 or by1 > ry2)
        # 슛 판정: 이전 프레임은 겹치지 않고 이번 프레임은 겹치면
        if not prev_rim_overlap and rim_overlap:
            shot_events[i] = prev_owner
        # 득점이 발생한 경우 무조건 슛으로 간주
        if score_events is not None and score_events[i] is not None:
            shot_events[i] = prev_owner
        prev_owner = owner_team
        prev_rim_overlap = rim_overlap
    return shot_events

def detect_score(
    frames: List[List[List[float]]],
    shot_events: List[Optional[int]],
    ball_boxes: List[Optional[Tuple[float, float, float, float]]],
    rim_centers: List[Optional[Tuple[float, float]]],
    rim_dist_thresh: float = 0.005
) -> Tuple[List[Optional[int]], List[Optional[float]]]:
    """
    득점: 슛 발생 후 공이 사라졌다가 다시 나타날 때, 사라지기 전 마지막 위치와 다시 나타난 첫 위치를 잇는 선과 림 중심의 거리가 rim_dist_thresh 이하이면 득점으로 간주.
    반환: (score_events, ball_rim_distances)
    score_events: [None, None, 0, ...] (득점시 슛 팀번호)
    ball_rim_distances: [None, None, 0.003, ...] (득점 판정에 사용된 거리)
    """
    score_events = [None] * len(frames)
    ball_rim_distances = [None] * len(frames)
    i = 0
    while i < len(frames):
        if shot_events[i] is not None:
            # 슛 이후 공이 사라지는 구간 찾기
            last_ball_idx = None
            for j in range(i, len(frames)):
                if ball_boxes[j] is not None:
                    last_ball_idx = j
                else:
                    break
            # 공이 사라진 구간 이후 다시 나타나는 첫 프레임 찾기
            first_after_idx = None
            for k in range(last_ball_idx+1, len(frames)):
                if ball_boxes[k] is not None:
                    first_after_idx = k
                    break
                # 림이 없으면 중단
                if rim_centers[k] is None:
                    break
            if last_ball_idx is not None and first_after_idx is not None:
                # 두 점과 림 중심의 거리 계산
                ball1 = ball_boxes[last_ball_idx]
                ball2 = ball_boxes[first_after_idx]
                rim_center = rim_centers[first_after_idx]
                # 점과 선분 사이 거리
                def point_line_dist(px, py, x1, y1, x2, y2):
                    A = px - x1
                    B = py - y1
                    C = x2 - x1
                    D = y2 - y1
                    dot = A * C + B * D
                    len_sq = C * C + D * D
                    param = dot / len_sq if len_sq != 0 else -1
                    if param < 0:
                        xx, yy = x1, y1
                    elif param > 1:
                        xx, yy = x2, y2
                    else:
                        xx = x1 + param * C
                        yy = y1 + param * D
                    dx = px - xx
                    dy = py - yy
                    return (dx * dx + dy * dy) ** 0.5
                dist = point_line_dist(rim_center[0], rim_center[1], ball1[0], ball1[1], ball2[0], ball2[1])
                ball_rim_distances[first_after_idx] = dist
                if dist <= rim_dist_thresh:
                    score_events[first_after_idx] = shot_events[i]
            i = first_after_idx if first_after_idx is not None else i+1
        else:
            i += 1
    return score_events, ball_rim_distances

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
    어시스트 발생 프레임 인덱스 반환. 득점 직전 마지막 소유권자가 슛 팀과 다르고, 같은 팀이면 어시스트.
    반환: [None, None, None, 0, ...] (어시스트 팀 인덱스)
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

def extrapolate_ball(frames: List[List[List[float]]], max_missing: int = None) -> List[Optional[Tuple[float, float, float, float]]]:
    """
    공이 detection에서 사라진 경우, 직전 프레임의 진행방향 또는 슛-림 사이 구간에서는 포물선(중력) 궤적(2차 회귀)을 사용해 가상의 바운딩박스를 생성.
    반환: 각 프레임별 (x, y, w, h) 또는 None
    """
    ball_boxes = []
    last_ball = None
    last_vec = None
    missing_count = 0
    # 포물선 보정용 변수
    shot_mode = False
    shot_start_idx = None
    shot_start_pos = None
    shot_vx = None
    shot_vy = None
    poly_px = None
    poly_py = None
    t_since_shot = 0
    # 최근 N프레임 공 중심 저장 (속도/회귀 추정용)
    N = 7
    recent_centers = []
    for i, detections in enumerate(frames):
        # 공, 림, 선수 분리
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
        # 소유 선수 찾기 (공과 가장 가까운 선수)
        owner_player_bbox = None
        if ball and players:
            ball_center = bbox_center(ball)
            min_dist = float('inf')
            for player in players:
                player_center = bbox_center(player['bbox'])
                dist = euclidean(ball_center, player_center)
                if dist < min_dist:
                    min_dist = dist
                    owner_player_bbox = player['bbox']
        # 공이 소유 선수 바운딩박스 안에 있는지
        in_player = False
        if ball and owner_player_bbox:
            bx1, by1 = ball[0] - ball[2]/2, ball[1] - ball[3]/2
            bx2, by2 = ball[0] + ball[2]/2, ball[1] + ball[3]/2
            px1, py1 = owner_player_bbox[0] - owner_player_bbox[2]/2, owner_player_bbox[1] - owner_player_bbox[3]/2
            px2, py2 = owner_player_bbox[0] + owner_player_bbox[2]/2, owner_player_bbox[1] + owner_player_bbox[3]/2
            if not (bx2 < px1 or bx1 > px2 or by2 < py1 or by1 > py2):
                in_player = True
        # 림과 겹치는지
        rim_overlap = False
        if ball and rim:
            bx1, by1 = ball[0] - ball[2]/2, ball[1] - ball[3]/2
            bx2, by2 = ball[0] + ball[2]/2, ball[1] + ball[3]/2
            rx1, ry1 = rim[0] - rim[2]/2, rim[1] - rim[3]/2
            rx2, ry2 = rim[0] + rim[2]/2, rim[1] + rim[3]/2
            if not (bx2 < rx1 or bx1 > rx2 or by2 < ry1 or by1 > ry2):
                rim_overlap = True
        # 실제 공이 감지된 경우
        if ball:
            ball_boxes.append(ball)
            last_ball = ball
            missing_count = 0
            # 최근 중심 좌표 저장
            recent_centers.append(bbox_center(ball))
            if len(recent_centers) > N:
                recent_centers.pop(0)
            # 슛-림 사이 구간 진입/종료 판정
            if not in_player and not rim_overlap and not shot_mode and len(recent_centers) == N:
                # 슛 시점: 최근 N프레임으로 2차 회귀(포물선) 추정
                shot_mode = True
                shot_start_idx = i
                shot_start_pos = bbox_center(ball)
                t_arr = np.arange(N)
                xs = np.array([c[0] for c in recent_centers])
                ys = np.array([c[1] for c in recent_centers])
                poly_px = np.polyfit(t_arr, xs, 1)  # x축: 1차(등속)
                poly_py = np.polyfit(t_arr, ys, 2)  # y축: 2차(포물선)
                t_since_shot = 0
            if rim_overlap and shot_mode:
                # 림에 닿으면 포물선 보정 종료
                shot_mode = False
        else:
            # 공이 사라진 경우
            if shot_mode and last_ball and shot_start_pos is not None and poly_px is not None and poly_py is not None:
                # 2차 회귀(포물선) 궤적 보정
                t_since_shot += 1
                t_next = N + t_since_shot - 1
                new_x = np.polyval(poly_px, t_next)
                new_y = np.polyval(poly_py, t_next)
                new_box = (new_x, new_y, last_ball[2], last_ball[3])
                # 림과 겹치는지 확인
                rim_overlap = False
                if rim:
                    bx1, by1 = new_x - last_ball[2]/2, new_y - last_ball[3]/2
                    bx2, by2 = new_x + last_ball[2]/2, new_y + last_ball[3]/2
                    rx1, ry1 = rim[0] - rim[2]/2, rim[1] - rim[3]/2
                    rx2, ry2 = rim[0] + rim[2]/2, rim[1] + rim[3]/2
                    if not (bx2 < rx1 or bx1 > rx2 or by2 < ry1 or by1 > ry2):
                        rim_overlap = True
                if rim_overlap:
                    shot_mode = False
                ball_boxes.append(new_box)
                last_ball = new_box
            elif last_ball and last_vec and (max_missing is None or missing_count < max_missing):
                # 기존 선형 외삽
                new_x = last_ball[0] + last_vec[0]
                new_y = last_ball[1] + last_vec[1]
                new_box = (new_x, new_y, last_ball[2], last_ball[3])
                # 선수, 림과 겹치는지 확인
                overlaps = False
                for player in players:
                    if bbox_iou(new_box, player['bbox']) > 0:
                        overlaps = True
                        break
                if rim and bbox_iou(new_box, rim) > 0:
                    overlaps = True
                if overlaps:
                    ball_boxes.append(new_box)
                    last_ball = new_box
                else:
                    # 겹치지 않으면 마지막 바운딩박스 유지
                    ball_boxes.append(last_ball)
                missing_count += 1
            else:
                ball_boxes.append(None)
                missing_count = 0
    return ball_boxes

