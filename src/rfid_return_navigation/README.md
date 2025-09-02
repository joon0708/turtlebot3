# RFID Return Navigation

TurtleBot3용 RFID 태그 감지 기반 복귀 네비게이션 패키지입니다. RFID 태그가 감지되면 지정된 복귀 목표로 자동으로 이동합니다.

## 기능

- RFID 태그 감지 시 자동 복귀 네비게이션
- 쿨다운 시스템으로 중복 실행 방지
- 네비게이션 실패 시 자동 재시도
- Nav2의 navigate_to_pose 액션 서버 활용
- 파라미터 기반 설정

## 설치

### 패키지 빌드

```bash
# 워크스페이스에서 빌드
colcon build --packages-select rfid_return_navigation
source install/setup.bash
```

## 사용법

### 1. 독립적으로 실행

```bash
# 기본 설정으로 실행 (원점으로 복귀)
ros2 launch rfid_return_navigation rfid_return_navigation.launch.py

# 복귀 목표 커스터마이징
ros2 launch rfid_return_navigation rfid_return_navigation.launch.py \
    return_x:=1.5 \
    return_y:=-0.5 \
    return_z:=0.0 \
    return_w:=1.0 \
    cooldown_sec:=3.0 \
    max_retries:=5
```

### 2. TurtleBot3 Navigation2와 함께 실행

```bash
# 기본 설정으로 실행
ros2 launch turtlebot3_navigation2 navigation2.launch.py

# 복귀 목표 커스터마이징
ros2 launch turtlebot3_navigation2 navigation2.launch.py \
    return_x:=1.5 \
    return_y:=-0.5 \
    return_z:=0.0 \
    return_w:=1.0 \
    cooldown_sec:=3.0 \
    max_retries:=5
```

## 파라미터

- `return_x` (float): 복귀 목표의 X 좌표 (기본값: 0.0)
- `return_y` (float): 복귀 목표의 Y 좌표 (기본값: 0.0)
- `return_z` (float): 복귀 목표의 Z 방향 quaternion (기본값: 0.0)
- `return_w` (float): 복귀 목표의 W 방향 quaternion (기본값: 1.0)
- `rfid_topic` (string): RFID 태그 토픽 이름 (기본값: "/rfid/tag")
- `frame_id` (string): 좌표계 프레임 ID (기본값: "map")
- `cooldown_sec` (float): RFID 태그 감지 후 쿨다운 시간 (초, 기본값: 5.0)
- `max_retries` (int): 네비게이션 실패 시 최대 재시도 횟수 (기본값: 3)
- `retry_delay_sec` (float): 재시도 간 딜레이 시간 (초, 기본값: 1.0)

## 토픽

### 구독 토픽
- `/rfid/tag` (std_msgs/String): RFID 태그의 UID

### 액션 클라이언트
- `navigate_to_pose` (nav2_msgs/action/NavigateToPose): Nav2 네비게이션 액션

## 동작 방식

1. **RFID 태그 감지**: `/rfid/tag` 토픽에서 RFID 태그 UID를 수신
2. **쿨다운 체크**: 설정된 쿨다운 시간 내에 중복 실행 방지
3. **네비게이션 상태 체크**: 이미 네비게이션 중이면 무시
4. **복귀 목표 전송**: Nav2의 navigate_to_pose 액션으로 복귀 목표 전송
5. **결과 처리**: 
   - 성공: 복귀 완료
   - 실패: 설정된 횟수만큼 재시도 후 포기

## 복귀 목표 설정 방법

### RViz2에서 복귀 목표 설정

1. RViz2에서 "2D Pose Estimate" 툴 사용
2. 원하는 복귀 위치에서 클릭하여 방향 설정
3. 터미널에서 다음 명령으로 현재 위치 확인:
   ```bash
   ros2 topic echo /amcl_pose
   ```
4. 얻은 x, y, z, w 값을 파라미터로 설정

### 예시 설정

```bash
# 시작점으로 복귀
return_x:=0.0 return_y:=0.0 return_z:=0.0 return_w:=1.0

# 특정 위치로 복귀 (예: x=1.5, y=-0.5, 방향 90도)
return_x:=1.5 return_y:=-0.5 return_z:=0.707 return_w:=0.707
```

## 주의사항

1. **Nav2 실행 필요**: 이 패키지는 Nav2가 실행 중이어야 합니다
2. **맵 필요**: 복귀 목표는 map 좌표계 기준이므로 맵이 로드되어야 합니다
3. **RFID 태그 퍼블리셔**: `/rfid/tag` 토픽을 발행하는 노드가 필요합니다
4. **쿨다운 설정**: 너무 짧은 쿨다운은 중복 실행을, 너무 긴 쿨다운은 반응 지연을 야기할 수 있습니다

## 라이센스

Apache License 2.0
