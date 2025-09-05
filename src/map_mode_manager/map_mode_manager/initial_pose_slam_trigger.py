#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseWithCovarianceStamped
from std_msgs.msg import String
import time

class InitialPoseSLAMTrigger(Node):
    """영점 지정 시 SLAM 모드로 전환하는 노드"""
    
    def __init__(self):
        super().__init__('initial_pose_slam_trigger')
        
        # 파라미터
        self.declare_parameter('slam_switch_delay', 3.0)  # 영점 지정 후 SLAM 전환 지연 시간
        self.slam_switch_delay = self.get_parameter('slam_switch_delay').value
        
        # 상태 변수
        self.initial_pose_received = False
        self.slam_triggered = False
        
        # 구독자
        self.initial_pose_sub = self.create_subscription(
            PoseWithCovarianceStamped,
            '/initialpose',
            self.initial_pose_callback,
            10
        )
        
        # 발행자
        self.mode_switch_pub = self.create_publisher(
            String,
            '/mode_switch_request',
            10
        )
        
        # 타이머 (영점 지정 후 SLAM 전환)
        self.slam_switch_timer = None
        
        self.get_logger().info('Initial Pose SLAM Trigger 노드가 시작되었습니다.')
        self.get_logger().info('영점이 지정되면 {}초 후 SLAM 모드로 전환됩니다.'.format(self.slam_switch_delay))
    
    def initial_pose_callback(self, msg: PoseWithCovarianceStamped):
        """영점 지정 콜백"""
        if not self.initial_pose_received:
            self.initial_pose_received = True
            self.get_logger().info('영점이 지정되었습니다!')
            self.get_logger().info('위치: ({:.2f}, {:.2f})'.format(
                msg.pose.pose.position.x, 
                msg.pose.pose.position.y
            ))
            
            # SLAM 모드 전환 타이머 시작
            self.slam_switch_timer = self.create_timer(
                self.slam_switch_delay,
                self.trigger_slam_mode
            )
        else:
            self.get_logger().warn('영점이 이미 지정되었습니다. SLAM 모드 전환을 다시 시도합니다.')
            # 기존 타이머 취소 후 새로 시작
            if self.slam_switch_timer:
                self.slam_switch_timer.cancel()
            self.slam_switch_timer = self.create_timer(
                self.slam_switch_delay,
                self.trigger_slam_mode
            )
    
    def trigger_slam_mode(self):
        """SLAM 모드로 전환"""
        if not self.slam_triggered:
            self.slam_triggered = True
            
            # SLAM 모드 전환 요청 발행
            mode_msg = String()
            mode_msg.data = 'SLAM'
            self.mode_switch_pub.publish(mode_msg)
            
            self.get_logger().info('SLAM 모드로 전환 요청을 발행했습니다!')
            
            # 타이머 정리
            if self.slam_switch_timer:
                self.slam_switch_timer.cancel()
                self.slam_switch_timer = None

def main(args=None):
    rclpy.init(args=args)
    node = InitialPoseSLAMTrigger()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        node.get_logger().error(f'오류 발생: {e}')
    finally:
        try:
            node.destroy_node()
        except:
            pass
        try:
            rclpy.shutdown()
        except:
            pass

if __name__ == '__main__':
    main()
