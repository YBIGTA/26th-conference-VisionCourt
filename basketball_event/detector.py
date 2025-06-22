from collections import deque
import numpy as np

class BasketballEventAnalyzer:
    def __init__(self, possession_iou_thresh=0.3, score_iou_thresh=0.2, player_match_thresh=0.5):
        self.possession_thresh = possession_iou_thresh
        self.score_thresh = score_iou_thresh
        self.player_match_thresh = player_match_thresh
        
        # 이전 프레임 정보 저장
        self.prev_ball_center = None
        self.prev_ball_possessor = None
        self.prev_ball_possessor_team = None
        self.prev_hoop_detected = False
        self.ball_trajectory = deque(maxlen=30)  # 볼 궤적 추적 (더 긴 구간으로 확장)
        
        # 슛 관련 상태 (더 정교한 감지를 위해)
        self.shot_attempted = False
        self.shot_released = False
        self.shot_release_possessor = None
        self.shot_release_team = None
        self.shot_release_frame = None
        self.ball_direction_changed = False
        self.prev_ball_direction = None
        
        # 이벤트 감지를 위한 상태 변수들
        self.ball_near_hoop_frames = 0  # 볼이 림 근처에 머무른 프레임 수
        self.ball_above_hoop_frames = 0  # 볼이 림 위에 머무른 프레임 수
        self.last_score_frame = None  # 마지막 득점 프레임
        self.last_shot_frame = None   # 마지막 슛 시도 프레임
        self.ball_velocity_history = deque(maxlen=10)  # 볼 속도 히스토리
        self.ball_acceleration_history = deque(maxlen=10)  # 볼 가속도 히스토리
        
        # 3대3 농구 샷클락 (12초)
        self.shot_clock = 12
        self.shot_clock_active = False
        self.shot_clock_start_frame = None
        self.current_frame = 0
        
        # 팀별 이벤트 카운터
        self.team_a_score = 0
        self.team_b_score = 0
        self.team_a_rebounds = 0
        self.team_b_rebounds = 0
        self.team_a_assists = 0
        self.team_b_assists = 0
        self.team_a_shots = 0
        self.team_b_shots = 0
        
        # 개인별 통계 (track_id별)
        self.player_stats = {}
        for track_id in range(1, 7):  # track_id 1~6
            self.player_stats[track_id] = {
                'track_id': track_id,
                'team': (track_id - 1) % 2,  # 0, 1, 0, 1, 0, 1
                'points': 0,
                'shots_attempted': 0,
                'shots_made': 0,
                'rebounds': 0,
                'assists': 0,
                'possessions': 0
            }

    def update_player_stats(self, track_id, event_type, team_id=None):
        """개인별 통계 업데이트"""
        if track_id in self.player_stats:
            if event_type == 'score':
                self.player_stats[track_id]['points'] += 2  # 3x3 농구는 2점
                self.player_stats[track_id]['shots_made'] += 1
            elif event_type == 'shot':
                self.player_stats[track_id]['shots_attempted'] += 1
            elif event_type == 'rebound':
                self.player_stats[track_id]['rebounds'] += 1
            elif event_type == 'assist':
                self.player_stats[track_id]['assists'] += 1
            elif event_type == 'possession':
                self.player_stats[track_id]['possessions'] += 1

    def convert_yolo_to_bbox(self, x_center, y_center, w, h):
        """YOLO 형식을 바운딩 박스 형식으로 변환"""
        x1 = x_center - w / 2
        y1 = y_center - h / 2
        x2 = x_center + w / 2
        y2 = y_center + h / 2
        return [x1, y1, x2, y2]

    def iou(self, boxA, boxB):
        """두 바운딩 박스의 IoU 계산"""
        xA = max(boxA[0], boxB[0])
        yA = max(boxA[1], boxB[1])
        xB = min(boxA[2], boxB[2])
        yB = min(boxA[3], boxB[3])
        
        inter = max(0, xB - xA) * max(0, yB - yA)
        boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
        boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
        
        if boxAArea + boxBArea - inter == 0:
            return 0
        return inter / (boxAArea + boxBArea - inter)

    def calculate_ball_velocity(self, current_pos, prev_pos, fps=30):
        """볼의 속도 계산 (픽셀/초)"""
        if not prev_pos:
            return None
        
        dx = current_pos[0] - prev_pos[0]
        dy = current_pos[1] - prev_pos[1]
        distance = np.sqrt(dx**2 + dy**2)
        velocity = distance * fps  # 픽셀/초
        
        return velocity

    def calculate_ball_acceleration(self, current_velocity, prev_velocity, fps=30):
        """볼의 가속도 계산 (픽셀/초²)"""
        if current_velocity is None or prev_velocity is None:
            return None
        
        acceleration = (current_velocity - prev_velocity) * fps
        return acceleration

    def analyze_ball_trajectory(self, min_frames=5):
        """볼 궤적 분석 - 슛 패턴 감지 (골밑슛 포함)"""
        if len(self.ball_trajectory) < min_frames:
            return False, None
        
        # 최근 N프레임의 궤적 분석
        recent_traj = list(self.ball_trajectory)[-min_frames:]
        y_coords = [pos[1] for pos in recent_traj]
        x_coords = [pos[0] for pos in recent_traj]
        
        # 1. 포물선 패턴 감지 (상승→최고점→하강) - 일반 슛
        y_min_idx = np.argmin(y_coords)  # 최고점 (농구는 y가 작을수록 위)
        
        # 최고점이 중간에 있고, 양 끝보다 높으면 포물선
        if 1 < y_min_idx < len(y_coords) - 2:
            if (y_coords[0] > y_coords[y_min_idx] and 
                y_coords[-1] > y_coords[y_min_idx]):
                return True, recent_traj[y_min_idx]
        
        # 2. 수직 상승 패턴 감지 (직선 상승) - 일반 슛
        if len(y_coords) >= 3:
            y_diffs = [y_coords[i] - y_coords[i-1] for i in range(1, len(y_coords))]
            if all(diff < -5 for diff in y_diffs):  # 계속 위로 상승
                return True, recent_traj[-1]
        
        # 3. 골밑슛 패턴 감지 (낮은 궤적, 수평 이동)
        if len(y_coords) >= 3:
            # y좌표 변화가 작고 (낮은 궤적), x좌표 변화가 있는 경우
            y_variance = np.var(y_coords)  # y좌표 분산
            x_variance = np.var(x_coords)  # x좌표 분산
            
            # y 변화가 작고(낮은 궤적), x 변화가 있으면(수평 이동) 골밑슛 가능성
            if y_variance < 100 and x_variance > 50:  # 임계값 조정 가능
                return True, recent_traj[-1]
        
        return False, None

    def detect_shot_advanced(self, ball, hoop, current_possessor, current_team):
        """고급 슛 감지 - 단순화된 조건: 득점 또는 림 근처에서의 방향/가속도 변화"""
        if not ball or not self.prev_ball_center:
            return False, None
        
        ball_center = ball['center']
        
        # 1. 볼이 선수로부터 떠났는지 확인
        if not self.shot_released:
            return False, None
        
        # 2. 볼이 림을 향하고 있는지 확인
        if not hoop:
            return False, None
            
        hoop_center = [(hoop[0] + hoop[2])/2, (hoop[1] + hoop[3])/2]
        
        # 볼이 림 방향으로 이동하는지 확인 (이전 프레임과 비교)
        if self.prev_ball_center:
            prev_to_hoop = np.sqrt(
                (self.prev_ball_center[0] - hoop_center[0])**2 + 
                (self.prev_ball_center[1] - hoop_center[1])**2
            )
            current_to_hoop = np.sqrt(
                (ball_center[0] - hoop_center[0])**2 + 
                (ball_center[1] - hoop_center[1])**2
            )
            
            # 볼이 림을 향해 이동하는지 확인
            moving_toward_hoop = current_to_hoop < prev_to_hoop
            
            if moving_toward_hoop and current_to_hoop < 100:  # 림 100픽셀 이내
                # 3. 림 근처에서 진행방향 또는 가속도 변화 감지
                
                # 진행방향 변화 감지 (최근 3프레임 분석)
                if len(self.ball_trajectory) >= 3:
                    recent_traj = list(self.ball_trajectory)[-3:]
                    
                    # 방향 벡터 계산
                    direction_1 = [
                        recent_traj[1][0] - recent_traj[0][0],
                        recent_traj[1][1] - recent_traj[0][1]
                    ]
                    direction_2 = [
                        recent_traj[2][0] - recent_traj[1][0],
                        recent_traj[2][1] - recent_traj[1][1]
                    ]
                    
                    # 방향 벡터 정규화
                    mag_1 = np.sqrt(direction_1[0]**2 + direction_1[1]**2)
                    mag_2 = np.sqrt(direction_2[0]**2 + direction_2[1]**2)
                    
                    if mag_1 > 0 and mag_2 > 0:
                        direction_1 = [direction_1[0]/mag_1, direction_1[1]/mag_1]
                        direction_2 = [direction_2[0]/mag_2, direction_2[1]/mag_2]
                        
                        # 두 방향 벡터의 내적 계산
                        dot_product = direction_1[0] * direction_2[0] + direction_1[1] * direction_2[1]
                        
                        # 방향 변화 감지 (내적이 0.7 미만이면 방향 변화로 간주)
                        direction_changed = dot_product < 0.7
                        
                        if direction_changed:
                            return True, ball_center
                
                # 가속도 변화 감지
                if len(self.ball_acceleration_history) >= 2:
                    recent_accel = list(self.ball_acceleration_history)[-2:]
                    
                    # 가속도 변화가 급격한지 확인 (절댓값이 100 이상)
                    if abs(recent_accel[-1]) > 100:
                        return True, ball_center
        
        return False, None

    def detect_score_advanced(self, ball, hoop):
        """고급 득점 감지 - 2D 매핑을 고려한 정교한 감지"""
        if not ball or not hoop:
            return False, None
        
        ball_center = ball['center']
        hoop_center = [(hoop[0] + hoop[2])/2, (hoop[1] + hoop[3])/2]
        
        # 1. 볼이 림 근처에 있는지 확인 (IoU + 거리 기반)
        iou_bh = self.iou(ball['bbox'], hoop)
        distance_to_hoop = np.sqrt(
            (ball_center[0] - hoop_center[0])**2 + 
            (ball_center[1] - hoop_center[1])**2
        )
        
        # 2. 볼이 림 위에 있는지 확인 (y좌표가 림보다 위)
        ball_above_hoop = ball_center[1] < hoop_center[1]
        
        # 3. 볼이 림 근처에 일정 시간 머무르는지 확인
        if iou_bh > self.score_thresh or distance_to_hoop < 50:
            self.ball_near_hoop_frames += 1
            if ball_above_hoop:
                self.ball_above_hoop_frames += 1
        else:
            self.ball_near_hoop_frames = 0
            self.ball_above_hoop_frames = 0
        
        # 4. 득점 조건: 볼이 림 위에 2프레임 이상 머무르고, 림 근처에 3프레임 이상 머무름
        if (self.ball_above_hoop_frames >= 2 and 
            self.ball_near_hoop_frames >= 3):
            
            # 5. 볼이 아래로 떨어지는지 확인 (득점 후)
            if self.prev_ball_center:
                dy = ball_center[1] - self.prev_ball_center[1]
                if dy > 5:  # 아래로 떨어짐
                    return True, ball_center
        
        return False, None

    def detect_rebound_advanced(self, ball, players, current_possessor):
        """고급 리바운드 감지 - 여러 프레임의 패턴 분석"""
        if not ball or not self.prev_ball_center:
            return None
        
        ball_center = ball['center']
        
        # 1. 볼이 아래로 떨어지는지 확인
        dy = ball_center[1] - self.prev_ball_center[1]
        
        # 2. 볼이 림 근처에서 튕겨나왔는지 확인
        if len(self.ball_trajectory) >= 5:
            recent_traj = list(self.ball_trajectory)[-5:]
            y_coords = [pos[1] for pos in recent_traj]
            
            # 볼이 위로 올라갔다가 아래로 떨어지는 패턴 (리바운드의 특징)
            if (y_coords[0] > y_coords[2] and  # 처음보다 중간이 위
                y_coords[2] < y_coords[-1]):   # 중간보다 마지막이 아래
                
                # 3. 가장 가까운 선수 찾기
                best_player = None
                min_distance = float('inf')
                
                for player in players:
                    player_center = [(player['bbox'][0] + player['bbox'][2])/2, 
                                   (player['bbox'][1] + player['bbox'][3])/2]
                    distance = np.sqrt((ball_center[0] - player_center[0])**2 + 
                                     (ball_center[1] - player_center[1])**2)
                    if distance < min_distance:
                        min_distance = distance
                        best_player = player
                
                # 4. 선수가 볼 근처에 있고, 볼 소유권이 변경되었는지 확인
                if (best_player and min_distance < 80 and 
                    current_possessor != self.prev_ball_possessor):
                    return best_player
        
        return None

    def detect_assist_advanced(self, ball, players, current_possessor, current_team):
        """고급 어시스트 감지 - 시간 간격과 패턴 분석"""
        if not ball or not self.prev_ball_possessor:
            return None
        
        # 1. 최근에 득점이 발생했는지 확인 (5프레임 이내)
        if (self.last_score_frame and 
            self.current_frame - self.last_score_frame <= 5):
            
            # 2. 득점 직전에 볼을 소유했던 선수가 다른 팀인지 확인
            if (self.prev_ball_possessor_team != current_team and 
                self.prev_ball_possessor_team is not None):
                
                # 3. 어시스트 조건: 슛 시도 후 3프레임 이내에 득점
                if (self.last_shot_frame and 
                    self.last_score_frame - self.last_shot_frame <= 3):
                    
                    # 4. 이전 볼 소유자 찾기
                    for player in players:
                        if (player['team_id'] == self.prev_ball_possessor_team and 
                            self.iou(player['bbox'], ball['bbox']) > self.possession_thresh):
                            return player
        
        return None

    def update_shot_clock(self, events, current_possessor, current_team):
        """3대3 농구 샷클락 업데이트"""
        # 샷클락 리셋 조건들
        reset_conditions = [
            any(event['type'] == 'score' for event in events),
            any(event['type'] == 'rebound' for event in events),
            any(event['type'] == 'shot' for event in events)
        ]
        
        if any(reset_conditions):
            self.shot_clock = 12
            self.shot_clock_active = False
            self.shot_clock_start_frame = None
            return
        
        # 볼 소유권이 변경되었을 때 샷클락 시작
        if (current_possessor is not None and 
            (self.prev_ball_possessor != current_possessor or 
             self.prev_ball_possessor_team != current_team)):
            
            if not self.shot_clock_active:
                self.shot_clock_active = True
                self.shot_clock_start_frame = self.current_frame
        
        # 샷클락 감소 (프레임당 약 0.033초 가정, 30fps)
        if self.shot_clock_active and self.shot_clock_start_frame:
            frames_elapsed = self.current_frame - self.shot_clock_start_frame
            time_elapsed = frames_elapsed / 30.0  # 초 단위
            self.shot_clock = max(0, 12 - time_elapsed)
            
            # 샷클락 위반
            if self.shot_clock <= 0:
                events.append({
                    'type': 'shot_clock_violation',
                    'team': current_team,
                    'player': current_possessor
                })
                self.shot_clock = 12
                self.shot_clock_active = False
                self.shot_clock_start_frame = None

    def match_players(self, detection_players, tracking_players):
        """첫 번째 모델의 선수들과 두 번째 모델의 트래킹 선수들을 매칭"""
        matches = {}
        
        for det_player in detection_players:
            best_match = None
            best_iou = 0
            
            for track_player in tracking_players:
                iou_val = self.iou(det_player['bbox'], track_player['bbox'])
                if iou_val > self.player_match_thresh and iou_val > best_iou:
                    best_iou = iou_val
                    best_match = track_player['track_id']
            
            if best_match:
                matches[det_player['player_idx']] = {
                    'track_id': best_match,
                    'team_id': det_player['team_id'],
                    'bbox': det_player['bbox']
                }
        
        return matches

    def analyze_frame(self, detection_data, tracking_data, frame_id=None):
        """
        두 모델의 출력을 병렬 처리하여 이벤트 분석 (고급 버전)
        
        Args:
            detection_data: 첫 번째 모델 출력 (frame_id, class_id, x_center, y_center, width, height, team_id)
            tracking_data: 두 번째 모델 출력 (frame_id, track_id, x_center, y_center, width, height)
            frame_id: 현재 프레임 ID
        """
        if frame_id:
            self.current_frame = frame_id
            
        events = []
        current_possessor = None
        current_team = None
        
        # 데이터 분리
        ball = None
        hoop = None
        detection_players = []
        tracking_players = []
        
        # 첫 번째 모델 데이터 처리
        for det in detection_data:
            bbox = self.convert_yolo_to_bbox(det['x_center'], det['y_center'], 
                                           det['width'], det['height'])
            
            if det['class_id'] == 0:  # 공
                ball = {
                    'center': (det['x_center'], det['y_center']),
                    'bbox': bbox
                }
            elif det['class_id'] == 2:  # 림
                hoop = bbox
            elif det['class_id'] == 1:  # 선수
                detection_players.append({
                    'player_idx': len(detection_players),
                    'team_id': det['team_id'],
                    'bbox': bbox
                })
        
        # 두 번째 모델 데이터 처리
        for track in tracking_data:
            bbox = self.convert_yolo_to_bbox(track['x_center'], track['y_center'],
                                           track['width'], track['height'])
            tracking_players.append({
                'track_id': track['track_id'],
                'bbox': bbox
            })
        
        # 선수 매칭
        player_matches = self.match_players(detection_players, tracking_players)
        
        # 볼 소유권 판별
        if ball:
            max_iou = 0
            for player_idx, player_info in player_matches.items():
                iou_val = self.iou(player_info['bbox'], ball['bbox'])
                if iou_val > self.possession_thresh and iou_val > max_iou:
                    max_iou = iou_val
                    current_possessor = player_info['track_id']
                    current_team = player_info['team_id']
        
        # 볼 소유권 변경 시 개인 통계 업데이트
        if current_possessor and current_possessor != self.prev_ball_possessor:
            self.update_player_stats(current_possessor, 'possession')
        
        # 슛 릴리즈 감지 (볼이 선수로부터 떠남)
        if ball and current_possessor != self.prev_ball_possessor:
            if self.prev_ball_possessor is not None:
                self.shot_released = True
                self.shot_release_possessor = self.prev_ball_possessor
                self.shot_release_team = self.prev_ball_possessor_team
                self.shot_release_frame = self.current_frame
        
        # 볼 속도 및 가속도 계산
        if ball and self.prev_ball_center:
            velocity = self.calculate_ball_velocity(ball['center'], self.prev_ball_center)
            if velocity is not None:
                self.ball_velocity_history.append(velocity)
                
                if len(self.ball_velocity_history) >= 2:
                    prev_velocity = list(self.ball_velocity_history)[-2]
                    acceleration = self.calculate_ball_acceleration(velocity, prev_velocity)
                    if acceleration is not None:
                        self.ball_acceleration_history.append(acceleration)
        
        # 고급 이벤트 감지
        # 1. 고급 슛 감지
        shot_detected, shot_pos = self.detect_shot_advanced(ball, hoop, current_possessor, current_team)
        if shot_detected:
            events.append({
                'type': 'shot',
                'team': self.shot_release_team,
                'player': self.shot_release_possessor,
                'position': shot_pos
            })
            # 개인별 슛 시도 통계 업데이트
            self.update_player_stats(self.shot_release_possessor, 'shot')
            if self.shot_release_team == 0:
                self.team_a_shots += 1
            else:
                self.team_b_shots += 1
            self.shot_released = False
            self.last_shot_frame = self.current_frame
        
        # 2. 고급 득점 감지
        score_detected, score_pos = self.detect_score_advanced(ball, hoop)
        if score_detected:
            # 득점 이벤트가 감지되면, 같은 프레임에 슛 이벤트가 이미 없다면 추가
            has_shot = any(e['type'] == 'shot' for e in events)
            if not has_shot:
                events.append({
                    'type': 'shot',
                    'team': current_team,
                    'player': current_possessor,
                    'position': score_pos
                })
                # 개인별 슛 시도 통계 업데이트
                if current_possessor:
                    self.update_player_stats(current_possessor, 'shot')
                if current_team == 0:
                    self.team_a_shots += 1
                else:
                    self.team_b_shots += 1
            events.append({
                'type': 'score',
                'team': current_team,
                'player': current_possessor,
                'position': score_pos
            })
            # 개인별 득점 통계 업데이트
            if current_possessor:
                self.update_player_stats(current_possessor, 'score')
            if current_team == 0:
                self.team_a_score += 2  # 3x3 농구는 2점
            else:
                self.team_b_score += 2
            self.last_score_frame = self.current_frame
        
        # 3. 고급 리바운드 감지
        rebound_player = self.detect_rebound_advanced(ball, detection_players, current_possessor)
        if rebound_player:
            events.append({
                'type': 'rebound',
                'team': rebound_player['team_id'],
                'player': player_matches.get(rebound_player['player_idx'], {}).get('track_id')
            })
            # 개인별 리바운드 통계 업데이트
            rebound_track_id = player_matches.get(rebound_player['player_idx'], {}).get('track_id')
            if rebound_track_id:
                self.update_player_stats(rebound_track_id, 'rebound')
            if rebound_player['team_id'] == 0:
                self.team_a_rebounds += 1
            else:
                self.team_b_rebounds += 1
        
        # 4. 고급 어시스트 감지
        assist_player = self.detect_assist_advanced(ball, detection_players, current_possessor, current_team)
        if assist_player:
            events.append({
                'type': 'assist',
                'team': assist_player['team_id'],
                'player': player_matches.get(assist_player['player_idx'], {}).get('track_id')
            })
            # 개인별 어시스트 통계 업데이트
            assist_track_id = player_matches.get(assist_player['player_idx'], {}).get('track_id')
            if assist_track_id:
                self.update_player_stats(assist_track_id, 'assist')
            if assist_player['team_id'] == 0:
                self.team_a_assists += 1
            else:
                self.team_b_assists += 1
        
        # 샷클락 업데이트
        self.update_shot_clock(events, current_possessor, current_team)
        
        # 상태 업데이트
        if ball:
            self.prev_ball_center = ball['center']
            self.ball_trajectory.append(ball['center'])
        
        self.prev_ball_possessor = current_possessor
        self.prev_ball_possessor_team = current_team
        self.prev_hoop_detected = hoop is not None
        
        return {
            'possessor': current_possessor,
            'team': current_team,
            'events': events,
            'player_matches': player_matches,
            'shot_clock': self.shot_clock
        }

    def get_statistics(self):
        """현재까지의 통계 반환"""
        return {
            'team_a_score': self.team_a_score,
            'team_b_score': self.team_b_score,
            'team_a_rebounds': self.team_a_rebounds,
            'team_b_rebounds': self.team_b_rebounds,
            'team_a_assists': self.team_a_assists,
            'team_b_assists': self.team_b_assists,
            'team_a_shots': self.team_a_shots,
            'team_b_shots': self.team_b_shots
        }

    def get_player_statistics(self):
        """개인별 통계 반환"""
        return self.player_stats
