#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from nav2_msgs.action import NavigateToPose
from actionlib_msgs.msg import GoalStatus
from geometry_msgs.msg import PoseStamped
from std_msgs.msg import String
import time
from typing import Dict, List, Optional

class RFIDReturnNavigation(Node):
    """
    RFID 태그 감지 시 복귀 목표를 전송하는 ROS 2 노드
    Nav2의 navigate_to_pose 액션 서버를 사용하여 RFID 태그에 따라 복귀 목표를 전송합니다.
    """
    def __init__(self):
        super().__init__('rfid_return_navigation')
        self.get_logger().info('RFIDReturnNavigation 노드 초기화 중')

        # 파라미터 선언
        self.declare_parameter('return_x', 0.0)
        self.declare_parameter('return_y', 0.0)
        self.declare_parameter('return_z', 0.0)
        self.declare_parameter('return_w', 1.0)
        self.declare_parameter('rfid_topic', '/rfid/tag')
        self.declare_parameter('frame_id', 'map')
        self.declare_parameter('cooldown_sec', 5.0)
        self.declare_parameter('max_retries', 3)
        self.declare_parameter('retry_delay_sec', 1.0)

        # 파라미터 가져오기
        self.return_x = self.get_parameter('return_x').value
        self.return_y = self.get_parameter('return_y').value
        self.return_z = self.get_parameter('return_z').value
        self.return_w = self.get_parameter('return_w').value
        self.rfid_topic = self.get_parameter('rfid_topic').value
        self.frame_id = self.get_parameter('frame_id').value
        self.cooldown_sec = self.get_parameter('cooldown_sec').value
        self.max_retries = self.get_parameter('max_retries').value
        self.retry_delay_sec = self.get_parameter('retry_delay_sec').value

        # Nav2의 navigate_to_pose 액션 서버에 연결하는 ActionClient 생성
        self._action_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')
        self.get_logger().info('navigate_to_pose 액션 서버에 연결 대기 중...')
        self._action_client.wait_for_server()
        self.get_logger().info('navigate_to_pose 액션 서버에 연결되었습니다')

        # RFID 태그 구독자 생성
        self.rfid_subscription = self.create_subscription(
            String,
            self.rfid_topic,
            self.rfid_callback,
            10
        )
        self.get_logger().info(f'RFID 태그 토픽 구독 중: {self.rfid_topic}')

        # 상태 변수
        self.last_rfid_time = 0.0
        self.is_navigating = False
        self.retry_count = 0
        self.current_goal_handle = None

        # 복귀 목표 설정
        self.return_goal = {
            'x': self.return_x,
            'y': self.return_y,
            'z': self.return_z,
            'w': self.return_w
        }

        self.get_logger().info(f'복귀 목표 설정: x={self.return_x}, y={self.return_y}, z={self.return_z}, w={self.return_w}')

    def rfid_callback(self, msg: String):
        """
        RFID 태그 메시지를 받았을 때 호출되는 콜백 함수
        """
        current_time = time.time()
        
        # 쿨다운 체크
        if current_time - self.last_rfid_time < self.cooldown_sec:
            self.get_logger().debug(f'쿨다운 중: {self.cooldown_sec - (current_time - self.last_rfid_time):.1f}초 남음')
            return

        # 이미 네비게이션 중이면 무시
        if self.is_navigating:
            self.get_logger().debug('이미 네비게이션 중입니다. RFID 태그 무시')
            return

        self.get_logger().info(f'RFID 태그 감지: {msg.data}')
        self.last_rfid_time = current_time
        
        # 복귀 목표 전송
        self.send_return_goal()

    def send_return_goal(self):
        """
        복귀 목표를 Nav2 액션 서버로 전송
        """
        if self.is_navigating:
            self.get_logger().warn('이미 네비게이션 중입니다')
            return

        goal_msg = NavigateToPose.Goal()
        goal_msg.pose.header.frame_id = self.frame_id
        goal_msg.pose.header.stamp = self.get_clock().now().to_msg()
        
        # position (위치) 설정
        goal_msg.pose.pose.position.x = self.return_goal['x']
        goal_msg.pose.pose.position.y = self.return_goal['y']
        goal_msg.pose.pose.position.z = 0.0  # 2D 네비게이션이므로 z는 0.0으로 고정

        # orientation (방향) 설정
        goal_msg.pose.pose.orientation.x = 0.0
        goal_msg.pose.pose.orientation.y = 0.0
        goal_msg.pose.pose.orientation.z = self.return_goal['z']
        goal_msg.pose.pose.orientation.w = self.return_goal['w']

        self.get_logger().info(f'복귀 목표 전송 중: x: {self.return_goal["x"]:.2f}, y: {self.return_goal["y"]:.2f}')
        
        # 비동기적으로 목표 전송 및 콜백 함수 연결
        self._send_goal_future = self._action_client.send_goal_async(goal_msg)
        self._send_goal_future.add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        """
        액션 서버의 목표 수락 여부를 처리하는 콜백 함수
        """
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error('복귀 목표가 거부되었습니다')
            self.is_navigating = False
            return

        self.get_logger().info('복귀 목표가 수락되었습니다')
        self.is_navigating = True
        self.current_goal_handle = goal_handle
        self._get_result_future = goal_handle.get_result_async()
        self._get_result_future.add_done_callback(self.get_result_callback)

    def get_result_callback(self, future):
        """
        목표 달성 결과를 처리하는 콜백 함수
        """
        try:
            result = future.result()
            status = result.status
            if status == GoalStatus.SUCCEEDED:
                self.get_logger().info('복귀 목표 달성 성공!')
                self.is_navigating = False
                self.retry_count = 0
            else:
                self.get_logger().warn(f'복귀 목표 달성 실패: {status}')
                self.retry_count += 1

                if self.retry_count <= self.max_retries:
                    self.get_logger().warn(f'재시도 중... ({self.retry_count}/{self.max_retries})')
                    self.is_navigating = False
                    # 재시도 전 딜레이
                    time.sleep(self.retry_delay_sec)
                    self.send_return_goal()
                else:
                    self.get_logger().error(f'최대 재시도 횟수 초과. 복귀 목표 포기')
                    self.is_navigating = False
                    self.retry_count = 0
        except Exception as e:
            self.get_logger().error(f'결과 처리 중 오류 발생: {e}')
            self.is_navigating = False

    def cancel_current_goal(self):
        """
        현재 진행 중인 목표를 취소
        """
        if self.current_goal_handle and self.is_navigating:
            self.get_logger().info('현재 목표 취소 중...')
            self.current_goal_handle.cancel_goal_async()
            self.is_navigating = False

def main(args=None):
    try:
        # ROS 2 컨텍스트 초기화
        rclpy.init(args=args)
        navigator = RFIDReturnNavigation()
        
        # 노드를 계속 실행 (콜백 함수들이 처리될 수 있도록)
        rclpy.spin(navigator)
        
    except KeyboardInterrupt:
        # Ctrl+C 예외 처리
        if 'navigator' in locals():
            navigator.cancel_current_goal()
        pass
    except Exception as e:
        # 예상치 못한 다른 예외 처리
        print(f"예외 발생: {e}")
    finally:
        # 노드와 ROS 2 컨텍스트를 안전하게 종료
        if 'navigator' in locals() and navigator.get_name():
            navigator.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()
