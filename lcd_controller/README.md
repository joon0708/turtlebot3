# LCD Controller

TurtleBot3용 LCD 컨트롤러 패키지입니다. ROS2 토픽으로 받은 명령을 LCD에 바로 실행합니다.

## 기능

- **텍스트 표시**: 토픽으로 받은 텍스트를 LCD에 표시
- **화면 지우기**: LCD 화면 전체 지우기
- **백라이트 제어**: 백라이트 켜기/끄기
- **커서 제어**: 커서 위치 설정 및 모드 변경
- **줄 지우기**: 특정 줄만 지우기
- **실시간 제어**: ROS 토픽으로 즉시 LCD 제어

## 하드웨어 연결

### I2C LCD 모듈 핀 연결

I2C LCD 모듈 (16x2 또는 20x4)을 Raspberry Pi에 다음과 같이 연결하세요:

| LCD 모듈 핀 | Raspberry Pi 핀 | 설명 |
|------------|----------------|------|
| VCC | 3.3V | 전원 공급 |
| GND | GND | 접지 |
| SDA | GPIO2 (BCM 2) | I2C 데이터 라인 |
| SCL | GPIO3 (BCM 3) | I2C 클럭 라인 |

### 연결 다이어그램

```
LCD 모듈 (I2C)          Raspberry Pi
┌─────────────┐        ┌─────────────┐
│             │        │             │
│ VCC ────────┼────────┤ 3.3V        │
│             │        │             │
│ GND ────────┼────────┤ GND         │
│             │        │             │
│ SDA ────────┼────────┤ GPIO2 (SDA) │
│             │        │             │
│ SCL ────────┼────────┤ GPIO3 (SCL) │
│             │        │             │
└─────────────┘        └─────────────┘
```

### I2C 주소 확인

LCD 모듈의 I2C 주소를 확인하려면:

```bash
# I2C 장치 스캔
i2cdetect -y 1

# 또는
i2cdetect -y 0
```

일반적인 I2C LCD 주소:
- **0x27**: 대부분의 I2C LCD 모듈
- **0x3F**: 일부 LCD 모듈
- **0x20**: PCF8574 기반 모듈

### 지원되는 LCD 모듈

- **16x2 I2C LCD**: 16자 x 2줄 표시
- **20x4 I2C LCD**: 20자 x 4줄 표시
- **PCF8574 기반**: I2C 확장 칩 사용
- **MCP23008 기반**: I2C 확장 칩 사용

## 설치

### 의존성 설치
```bash
# RPLCD 라이브러리 설치
pip3 install RPLCD

# I2C 도구 설치
sudo apt install python3-smbus i2c-tools

# I2C 활성화
sudo raspi-config
# Interface Options → I2C → Enable
```

### 패키지 빌드
```bash
colcon build --packages-select lcd_controller

```

## 사용법

### 1. LCD 컨트롤러 실행
```bash
# Launch 파일 사용 (권장)
ros2 launch lcd_controller lcd_controller.launch.py

# 직접 실행
ros2 run lcd_controller lcd_controller
```

## 토픽

### 입력 토픽 (Subscribers)
- `/lcd/display` (std_msgs/String): LCD에 표시할 텍스트 (화면 지우고 새로 표시)
- `/lcd/clear` (std_msgs/String): LCD 화면 지우기 (빈 문자열 전송)
- `/lcd/backlight` (std_msgs/Bool): 백라이트 켜기/끄기
- `/lcd/set_cursor` (std_msgs/String): 커서 위치 설정 ("row,col" 형식)
- `/lcd/write` (std_msgs/String): 현재 커서 위치에 텍스트 쓰기
- `/lcd/clear_line` (std_msgs/UInt8): 특정 줄 지우기 (줄 번호)
- `/lcd/cursor_mode` (std_msgs/String): 커서 모드 설정 ("hide", "visible", "blink")

## 사용 예시

### 1. 텍스트 표시
```bash
ros2 topic pub /lcd/display std_msgs/msg/String "data: 'Hello World!'"
```

### 2. 화면 지우기
```bash
ros2 topic pub /lcd/clear std_msgs/msg/String "data: ''"
```

### 3. 백라이트 제어
```bash
# 백라이트 끄기
ros2 topic pub /lcd/backlight std_msgs/msg/Bool "data: false"

# 백라이트 켜기
ros2 topic pub /lcd/backlight std_msgs/msg/Bool "data: true"
```

### 4. 커서 제어
```bash
# 커서 위치 설정 (0행 5열)
ros2 topic pub /lcd/set_cursor std_msgs/msg/String "data: '0,5'"

# 현재 위치에 텍스트 쓰기
ros2 topic pub /lcd/write std_msgs/msg/String "data: 'Test'"

# 0번째 줄 지우기
ros2 topic pub /lcd/clear_line std_msgs/msg/UInt8 "data: 0"

# 커서 모드 설정
ros2 topic pub /lcd/cursor_mode std_msgs/msg/String "data: 'blink'"
```

### 5. 실시간 상태 표시
```bash
# 배터리 상태
ros2 topic pub /lcd/display std_msgs/msg/String "data: 'Battery: 85%'"

# 시스템 상태
ros2 topic pub /lcd/display std_msgs/msg/String "data: 'Status: Ready'"

# 속도 정보
ros2 topic pub /lcd/display std_msgs/msg/String "data: 'Speed: 0.5m/s'"
```

### 6. Python 스크립트에서 사용
```python
import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Bool, UInt8

class LCDPublisher(Node):
    def __init__(self):
        super().__init__('lcd_publisher')
        self.display_pub = self.create_publisher(String, '/lcd/display', 10)
        self.clear_pub = self.create_publisher(String, '/lcd/clear', 10)
        self.backlight_pub = self.create_publisher(Bool, '/lcd/backlight', 10)
        self.cursor_pub = self.create_publisher(String, '/lcd/set_cursor', 10)
        self.write_pub = self.create_publisher(String, '/lcd/write', 10)
        
    def display_message(self, text):
        msg = String()
        msg.data = text
        self.display_pub.publish(msg)
    
    def clear_screen(self):
        msg = String()
        msg.data = ""
        self.clear_pub.publish(msg)
    
    def set_cursor(self, row, col):
        msg = String()
        msg.data = f"{row},{col}"
        self.cursor_pub.publish(msg)

# 사용 예시
lcd_pub = LCDPublisher()
lcd_pub.display_message("Hello from Python!")
lcd_pub.set_cursor(0, 5)
lcd_pub.display_message("Cursor Test")
```

## 파라미터

- `use_sim_time` (bool): 시뮬레이션 시간 사용 여부 (기본값: false)

**참고**: I2C 설정은 RPLCD 라이브러리에서 자동으로 처리됩니다.

## I2C 설정 확인

```bash
# I2C 장치 스캔
i2cdetect -y 1

# I2C 활성화 확인
ls /dev/i2c*
```

## 문제 해결

### RPLCD 모듈 없음
```bash
# RPLCD 라이브러리 설치 (필수)
pip3 install RPLCD
```

### I2C 권한 문제
```bash
sudo usermod -a -G i2c $USER
# 재로그인 필요
```

### LCD가 응답하지 않음
1. I2C 주소 확인: `i2cdetect -y 1`
2. 배선 확인
3. 전원 공급 확인

### LCD가 깨끗하게 표시되지 않음
1. 대비 조정 (LCD 모듈의 가변저항)
2. 전원 전압 확인 (3.3V 권장)
3. I2C 클럭 속도 조정

### 특수 문자 표시 문제
```python
# UTF-8 인코딩 확인
import sys
sys.stdout.reconfigure(encoding='utf-8')
```

## 라이센스

이 프로젝트는 MIT 라이센스 하에 배포됩니다.
