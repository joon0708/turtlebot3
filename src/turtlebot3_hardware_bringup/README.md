# TurtleBot3 Hardware Bringup Package

TurtleBot3의 기본 하드웨어 설정을 위한 패키지입니다. 라이더 센서와 TF 설정을 포함합니다.

## 기능

- **LD08 라이더 센서**: LDS-02 모델 지원
- **TF 설정**: robot_state_publisher를 통한 TF 브로드캐스팅
- **모듈화**: 개별 기능별로 분리된 launch 파일

## Launch 파일

### 1. hardware.launch.py
전체 하드웨어 설정 (라이더 + TF)
```bash
ros2 launch turtlebot3_hardware_bringup hardware.launch.py
```

### 2. hardware_4wheel.launch.py
4바퀴 시스템 전용 실행
```bash
ros2 launch turtlebot3_hardware_bringup hardware_4wheel.launch.py
```

### 3. lidar_only.launch.py
라이더 센서만 실행
```bash
ros2 launch turtlebot3_hardware_bringup lidar_only.launch.py
```

### 4. tf_only.launch.py
TF만 실행
```bash
ros2 launch turtlebot3_hardware_bringup tf_only.launch.py
```

## 파라미터

- `lidar_port`: 라이더 센서 포트 (기본값: `/dev/ttyUSB0`)
- `use_sim_time`: 시뮬레이션 시간 사용 (기본값: `false`)
- `namespace`: 노드 네임스페이스 (기본값: `''`)

## 사용 예시

### 다른 패키지에서 포함하기
```python
# cartographer.launch.py에서 사용
IncludeLaunchDescription(
    PythonLaunchDescriptionSource([os.path.join(
        get_package_share_directory('turtlebot3_hardware_bringup'), 'launch', 'hardware.launch.py')]),
    launch_arguments={'lidar_port': '/dev/ttyUSB1'}.items(),
),
```

### 환경 변수 설정
```bash
export ROS_DOMAIN_ID=10
export TURTLEBOT3_MODEL=waffle_pi
```

## 의존성

- `ld08_driver`: LD08 라이더 드라이버
- `turtlebot3_bringup`: TF 설정
- `robot_state_publisher`: TF 브로드캐스팅
- `turtlebot3_description`: URDF 모델
