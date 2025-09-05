# Location Manager

TurtleBot3를 위한 위치 관리 시스템입니다. 자주 사용하는 위치를 저장하고, 저장된 위치로 자동 네비게이션을 수행할 수 있습니다.

## 🚀 주요 기능

- **위치 저장**: 좌표 기반 또는 현재 로봇 위치 기반 저장
- **영구 저장**: YAML 파일로 위치 정보 영구 보존
- **자동 네비게이션**: 저장된 위치로 자동 이동
- **위치 관리**: 저장, 삭제, 목록 조회 등
- **Navigation2 연동**: ROS2 Navigation2와 완벽 호환

## 📋 시스템 요구사항

- **ROS2 Humble** 이상
- **TurtleBot3** (Waffle Pi, Burger 등)
- **Navigation2** 패키지
- **Cartographer** (SLAM)

## 🛠️ 설치 및 빌드

### 1. 패키지 빌드
```bash
# 워크스페이스에서 빌드
colcon build --packages-select location_manager

# 환경 설정
source install/setup.bash
```

### 2. 의존성 확인
```bash
# 필요한 패키지들이 설치되어 있는지 확인
ros2 pkg list | grep turtlebot3
ros2 pkg list | grep nav2
```

## 🚀 사용 방법

### 1. 시스템 실행
```bash
# 위치 관리 + 네비게이션 전체 실행
ros2 launch location_manager location_navigation.launch.py
```

### 2. 위치 저장 명령어

#### **좌표로 위치 저장**
```bash
# 기본 위치 저장 (x, y, yaw)
ros2 topic pub /location_command std_msgs/msg/String "data: 'save 회의실 2.5 1.0'" --once

# 방향까지 포함하여 저장
ros2 topic pub /location_command std_msgs/msg/String "data: 'save 출구 0.0 3.0 1.57'" --once
```

#### **현재 위치 저장**
```bash
# 로봇이 현재 있는 위치를 저장
ros2 topic pub /location_command std_msgs/msg/String "data: 'save_here 부엌'" --once
ros2 topic pub /location_command std_msgs/msg/String "data: 'save_here 거실'" --once
```

### 3. 위치 관리 명령어

#### **저장된 위치로 이동**
```bash
# 저장된 위치로 네비게이션
ros2 topic pub /location_command std_msgs/msg/String "data: 'go home'" --once
ros2 topic pub /location_command std_msgs/msg/String "data: 'go 회의실'" --once
```

#### **위치 목록 및 관리**
```bash
# 저장된 위치 목록 보기
ros2 topic pub /location_command std_msgs/msg/String "data: 'list'" --once

# 특정 위치 삭제
ros2 topic pub /location_command std_msgs/msg/String "data: 'delete point_a'" --once

# 모든 위치 삭제
ros2 topic pub /location_command std_msgs/msg/String "data: 'clear'" --once

# 상태 확인
ros2 topic pub /location_command std_msgs/msg/String "data: 'status'" --once
```

## 📁 파일 구조

```
location_manager/
├── location_manager/
│   ├── __init__.py
│   └── location_manager.py     # 메인 노드
├── launch/
│   └── location_navigation.launch.py  # 실행 파일
├── config/                     # 설정 파일 (자동 생성)
│   └── saved_locations.yaml   # 저장된 위치 정보
├── package.xml
├── setup.py
└── README.md
```

## 🔧 설정

### **환경 변수**
```bash
# TurtleBot3 모델 설정
export TURTLEBOT3_MODEL=waffle_pi_4wheel

# ROS 도메인 ID 설정 (필요시)
export ROS_DOMAIN_ID=10
```

### **포트 설정**
```bash
# LIDAR 포트 (기본값: /dev/ttyUSB0)
ros2 launch location_manager location_navigation.launch.py lidar_port:=/dev/ttyUSB1

# OpenCR 포트 (기본값: /dev/ttyACM1)
ros2 launch location_manager location_navigation.launch.py usb_port:=/dev/ttyACM0
```

## 📊 저장된 위치 형식

### **YAML 파일 구조**
```yaml
locations:
  home:
    name: "Home"
    description: "시작 위치"
    x: 0.0
    y: 0.0
    z: 0.0
    yaw: 0.0
    created: "2024-01-01T12:00:00"
  
  회의실:
    name: "회의실"
    description: "회의실 입구"
    x: 2.5
    y: 1.0
    z: 0.0
    yaw: 1.57
    created: "2024-01-01T12:30:00"
```

## 🔍 문제 해결

### **TF 오류**
```
Failed to get current location: Make sure TF is available and robot is localized
```
- Navigation2가 실행 중인지 확인
- 로봇이 로컬라이즈되어 있는지 확인
- TF 트리 상태 확인: `ros2 run tf2_tools view_frames`

### **위치 저장 실패**
- 로봇이 맵에서 위치를 파악할 수 있는지 확인
- LIDAR 센서가 정상 작동하는지 확인

### **네비게이션 실패**
- Navigation2 상태 확인
- 맵이 제대로 로드되었는지 확인
- 목표 위치가 맵 내에 있는지 확인

## 📈 향후 개발 계획

- [ ] **GUI 제어 프로그램** (별도 프로젝트)
- [ ] **센서 기반 자동 저장** (버튼, RFID, 초음파 등)
- [ ] **위치 그룹화 및 카테고리**
- [ ] **위치 간 경로 최적화**
- [ ] **모바일 앱 연동**

## 🤝 기여하기

버그 리포트, 기능 제안, 코드 기여를 환영합니다!

## 📄 라이선스

Apache 2.0 License

## 📞 지원

문제가 발생하거나 질문이 있으시면 이슈를 등록해 주세요.


동작 되는것 확인
