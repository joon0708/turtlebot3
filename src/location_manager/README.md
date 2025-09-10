# Location Manager

TurtleBot3를 위한 위치 관리 시스템입니다. 자주 사용하는 위치를 저장하고, 저장된 위치로 자동 네비게이션을 수행할 수 있습니다.

## 🚀 주요 기능

- **위치 저장**: 좌표 기반 또는 현재 로봇 위치 기반 저장
- **영구 저장**: YAML 파일로 위치 정보 영구 보존
- **자동 네비게이션**: 저장된 위치로 자동 이동
- **위치 관리**: 저장, 삭제, 목록 조회 등
- **Navigation2 연동**: ROS2 Navigation2와 완벽 호환
- **RFID 연동**: RFID 태그를 통한 자동 위치 이동 (선택적)
- **통합 상태 모니터링**: 두 시스템의 상태를 하나의 토픽으로 확인
- **LCD 디스플레이**: 현재 향하는 위치와 상태 정보를 LCD에 실시간 표시

## 📋 시스템 요구사항

- **ROS2 Humble** 이상
- **TurtleBot3** (Waffle Pi, Burger 등)
- **Navigation2** 패키지
- **Cartographer** (SLAM)
- **LCD 디스플레이** (선택적, I2C 연결)

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

#### **기본 실행 (위치 관리만)**
```bash
# 위치 관리 + 네비게이션 전체 실행
ros2 launch location_manager location_manager_complete.launch.py
```

#### **RFID 기능 포함 실행**
```bash
# RFID 기능과 함께 실행
ros2 launch location_manager location_manager_complete.launch.py enable_rfid:=true
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

#### **명령 응답 확인**
```bash
# 위치 관리 명령의 응답을 실시간으로 확인
ros2 topic echo /location_status

# RFID 관련 응답 확인 (RFID 활성화 시)
ros2 topic echo /rfid_status

# 통합 상태 확인 (두 시스템의 응답을 하나의 토픽으로)
ros2 topic echo /integrated_status
```

### 4. RFID 태그 사용법 (선택적)

#### **RFID 시스템 활성화**
```bash
# RFID 기능과 함께 실행
ros2 launch location_manager location_manager_complete.launch.py enable_rfid:=true
```

#### **RFID 태그 ID 확인**
```bash
# RFID 태그를 찍으면 ID가 표시됩니다
ros2 topic echo /rfid/tag
```

#### **RFID 태그와 위치 매핑**
```bash
# RFID 태그를 특정 위치에 매핑 (대소문자 구분 없음)
ros2 topic pub /rfid_command std_msgs/msg/String "data: 'map D3:64:15:0E home'" --once
ros2 topic pub /rfid_command std_msgs/msg/String "data: 'map d3:64:15:0e table1'" --once

# RFID 매핑 목록 확인
ros2 topic pub /rfid_command std_msgs/msg/String "data: 'list'" --once

# RFID 매핑 제거
ros2 topic pub /rfid_command std_msgs/msg/String "data: 'unmap D3:64:15:0E'" --once
```

#### **RFID 자동 복귀**
- RFID 태그를 찍으면 자동으로 매핑된 위치로 이동합니다
- 위치가 저장되어 있어야 RFID 매핑이 가능합니다

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
│   └── location_manager_complete.launch.py  # 통합 실행 파일
├── config/                     # 설정 파일 (자동 생성)
│   └── saved_locations.yaml   # 저장된 위치 정보
├── package.xml
├── setup.py
└── README.md

rfid_location_mapper/
├── rfid_location_mapper/
│   ├── __init__.py
│   └── rfid_location_mapper.py # RFID 매핑 노드
├── launch/
│   └── rfid_location_mapper.launch.py
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
ros2 launch location_manager location_manager_complete.launch.py lidar_port:=/dev/ttyUSB1

# OpenCR 포트 (기본값: /dev/ttyACM0)
ros2 launch location_manager location_manager_complete.launch.py usb_port:=/dev/ttyACM1

# RFID 기능과 함께 포트 설정
ros2 launch location_manager location_manager_complete.launch.py enable_rfid:=true lidar_port:=/dev/ttyUSB1
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

## 🤝 기여하기

버그 리포트, 기능 제안, 코드 기여를 환영합니다!

## 📄 라이선스

Apache 2.0 License

## 📞 지원

문제가 발생하거나 질문이 있으시면 이슈를 등록해 주세요.


## 🎯 주요 토픽

### **명령 토픽**
- `/location_command` - 위치 관리 명령
- `/rfid_command` - RFID 매핑 명령

### **상태 토픽**
- `/location_status` - 위치 관리 상태
- `/rfid_status` - RFID 시스템 상태
- `/integrated_status` - 통합 상태 (두 시스템의 응답을 하나로)

### **RFID 토픽**
- `/rfid/tag` - RFID 태그 ID 발행

### **네비게이션 토픽**
- `/goal_pose` - 네비게이션 목표 위치

### **LCD 토픽**
- `/lcd/display` - LCD 전체 화면 텍스트 표시
- `/lcd/clear` - LCD 화면 지우기
- `/lcd/backlight` - LCD 백라이트 제어
