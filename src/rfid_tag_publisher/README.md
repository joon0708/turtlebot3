# RFID Tag Publisher

TurtleBot3용 RFID 태그 퍼블리셔 패키지입니다. MFRC522 RFID 리더를 사용하여 RFID 태그를 읽고 ROS2 토픽으로 발행합니다.

## 설치

### 의존성 설치

```bash
# SPI 및 GPIO 라이브러리 설치
sudo apt-get install python3-spidev python3-gpiod

# 또는 pip로 설치
pip3 install spidev gpiod
```

### 패키지 빌드

```bash
# 워크스페이스에서 빌드
colcon build --packages-select rfid_tag_publisher
source install/setup.bash
```

## 사용법

### 1. 독립적으로 실행

```bash
# 기본 설정으로 실행
ros2 launch rfid_tag_publisher rfid_tag_publisher.launch.py

# 파라미터 커스터마이징
ros2 launch rfid_tag_publisher rfid_tag_publisher.launch.py \
    bus:=0 \
    device:=0 \
    hold_ms:=80 \
    cooldown:=1.0 \
    grace_ms:=200 \
    whitelist:="AA:BB:CC:DD,11:22:33:44" \
    rst_bcm:=24
```

### 2. TurtleBot3 robot.launch.py와 함께 실행

```bash
# 기본 설정으로 실행
ros2 launch turtlebot3_bringup robot.launch.py

# RFID 파라미터 커스터마이징
ros2 launch turtlebot3_bringup robot.launch.py \
    rfid_bus:=0 \
    rfid_device:=0 \
    rfid_hold_ms:=80 \
    rfid_cooldown:=1.0 \
    rfid_grace_ms:=200 \
    rfid_whitelist:="AA:BB:CC:DD,11:22:33:44" \
    rfid_rst_bcm:=24
```

## 파라미터

- `bus` (int): SPI 버스 번호 (기본값: 0)
- `device` (int): SPI 디바이스 번호 (기본값: 0)
- `hold_ms` (int): 태그 인식 후 발행까지의 홀드 시간 (밀리초, 기본값: 80)
- `cooldown` (float): 연속 발행 간의 쿨다운 시간 (초, 기본값: 1.0)
- `grace_ms` (int): 태그가 사라진 후 유지하는 시간 (밀리초, 기본값: 200)
- `whitelist` (string): 허용된 태그 UID 목록 (쉼표로 구분, 기본값: "")
- `rst_bcm` (int): 리셋 핀의 BCM 번호 (기본값: 24)

## 토픽

### 발행 토픽
- `/rfid/tag` (std_msgs/String): 읽은 RFID 태그의 UID

## 하드웨어 연결

MFRC522 RFID 리더를 다음과 같이 연결하세요:

- VCC → 3.3V
- GND → GND
- SDA → GPIO24 (BCM 24)
- SCK → SPI0_SCLK (BCM 11)
- MOSI → SPI0_MOSI (BCM 10)
- MISO → SPI0_MISO (BCM 9)
- RST → GPIO24 (BCM 24, 기본값)

## 라이센스

Apache License 2.0
