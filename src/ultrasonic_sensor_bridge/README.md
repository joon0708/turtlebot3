# 초음파 센서 브리지 (Ultrasonic Sensor Bridge)

이 패키지는 TurtleBot3의 초음파 센서 데이터를 ROS2의 `sensor_msgs/Range` 형식으로 변환하는 브리지 노드를 제공합니다.

## 기능

- OpenCR에서 보내는 3개의 초음파 센서 데이터를 ROS2로 변환
- 왼쪽, 앞쪽, 오른쪽 초음파 센서 지원
- DYNAMIXEL SDK를 통한 직접 OpenCR 제어 테이블 읽기
- ROS1이 없는 환경에서도 시뮬레이션 모드로 동작
- 실시간 데이터 변환 및 발행
- nan 값 필터링으로 안정적인 데이터 제공

## 토픽

### 출력 토픽
- `/ultrasonic/left` (sensor_msgs/Range) - 왼쪽 초음파 센서 (OpenCR 주소 190)
- `/ultrasonic/front` (sensor_msgs/Range) - 앞쪽 초음파 센서 (OpenCR 주소 194)
- `/ultrasonic/right` (sensor_msgs/Range) - 오른쪽 초음파 센서 (OpenCR 주소 198)

## 사용법

### 1. 빌드 및 설치

```bash
# 워크스페이스에서 빌드
colcon build --packages-select ultrasonic_sensor_bridge

# 환경 설정
source install/setup.bash
```

### 2. 실행 방법

#### Launch 파일 사용 (권장)
```bash
ros2 launch ultrasonic_sensor_bridge ultrasonic_publisher.launch.py
```

#### 직접 실행
```bash
ros2 run ultrasonic_sensor_bridge ultrasonic_publisher
```

### 3. 토픽 확인

```bash
# ROS2 토픽 리스트 확인
ros2 topic list | grep ultrasonic

# 토픽 데이터 확인
ros2 topic echo /ultrasonic/left
ros2 topic echo /ultrasonic/front
ros2 topic echo /ultrasonic/right

# 토픽 정보 확인
ros2 topic info /ultrasonic/left
```

## 설정

### 센서 파라미터

기본 센서 설정:
- 최소 거리: 0.02m (2cm)
- 최대 거리: 4.0m
- 시야각: 0.1rad (약 5.7도)
- 발행 주파수: 10Hz

### 시뮬레이션 데이터

시뮬레이션 모드에서 사용되는 기본 거리값:
- 왼쪽 센서: 1.5m
- 앞쪽 센서: 2.0m
- 오른쪽 센서: 1.8m

## 구현 방식

DYNAMIXEL SDK를 사용하여 OpenCR의 제어 테이블에서 직접 3개 초음파 센서 값을 읽어서 `sensor_msgs/Range` 메시지로 발행합니다.

**특징:**
- OpenCR 주소 190, 194, 198에서 직접 읽기
- nan 값 필터링으로 안정적인 데이터 제공
- 10Hz 주기로 데이터 발행
- 기존 turtlebot3_node와 독립적으로 동작

## 수정된 파일들

이 패키지가 정상적으로 작동하기 위해서는 다음 파일들이 수정되어야 합니다:

### turtlebot3_node 패키지 수정사항

#### 1. `turtlebot3_node/include/turtlebot3_node/control_table.hpp`
```cpp
// 추가된 초음파 센서 제어 테이블 항목들
ControlItem ultrasonic_left{190, 4};    // 왼쪽 초음파 센서
ControlItem ultrasonic_front{194, 4};   // 앞쪽 초음파 센서  
ControlItem ultrasonic_right{198, 4};   // 오른쪽 초음파 센서
```

#### 2. `turtlebot3_node/src/sensors/sensor_state.cpp`
```cpp
// 3개 초음파 센서 값 읽기 (추가됨)
float ultrasonic_left = dxl_sdk_wrapper->get_data_from_device<float>(
    extern_control_table.ultrasonic_left.addr,
    extern_control_table.ultrasonic_left.length);

float ultrasonic_front = dxl_sdk_wrapper->get_data_from_device<float>(
    extern_control_table.ultrasonic_front.addr,
    extern_control_table.ultrasonic_front.length);

float ultrasonic_right = dxl_sdk_wrapper->get_data_from_device<float>(
    extern_control_table.ultrasonic_right.addr,
    extern_control_table.ultrasonic_right.length);

// 현재는 front 센서 값만 sonar 필드에 저장 (임시 해결책)
msg->sonar = ultrasonic_front;
```

### 수정 이유
- 기존 `turtlebot3_node`는 단일 `sonar` 센서만 지원
- 3개 초음파 센서를 지원하도록 확장
- `ultrasonic_publisher`가 이 수정된 코드를 활용하여 개별 센서 데이터 발행

### 빌드 순서
```bash
# 1. turtlebot3_node 먼저 빌드
colcon build --packages-select turtlebot3_node

# 2. ultrasonic_sensor_bridge 빌드
colcon build --packages-select ultrasonic_sensor_bridge

# 3. 환경 설정
source install/setup.bash
```

## OpenCR 설정

DYNAMIXEL SDK가 자동으로 OpenCR의 제어 테이블에서 초음파 센서 값을 읽습니다. 추가 설정이 필요하지 않습니다.

**OpenCR 제어 테이블 주소:**
- 왼쪽 초음파 센서: 주소 190
- 앞쪽 초음파 센서: 주소 194
- 오른쪽 초음파 센서: 주소 198

## 문제 해결

### 토픽이 수신되지 않는 경우
1. OpenCR이 연결되어 있는지 확인
2. USB 포트 권한 확인
3. DYNAMIXEL SDK가 정상적으로 설치되었는지 확인

### 빌드 오류가 발생하는 경우
```bash
# 의존성 설치
sudo apt update
sudo apt install ros-humble-sensor-msgs ros-humble-turtlebot3-msgs

# Python 의존성 설치
pip3 install pyserial

# 워크스페이스 재빌드
colcon build --packages-select ultrasonic_sensor_bridge --cmake-clean-cache
```

### DYNAMIXEL SDK 관련 문제
```bash
# DYNAMIXEL SDK 설치 확인
pip3 install dynamixel-sdk

# Python 경로 확인
python3 -c "import dynamixel_sdk; print('DYNAMIXEL SDK available')"
```

## 라이선스

Apache License 2.0
