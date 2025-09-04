#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseWithCovarianceStamped
from std_msgs.msg import String
import tf2_ros
import tf2_geometry_msgs
from geometry_msgs.msg import TransformStamped
import math

class InitialPoseSetter(Node):
    """2D Pose Estimate를 받아서 카토그래퍼의 초기 위치를 설정하는 노드"""
    
    def __init__(self):
        super().__init__('initial_pose_setter')
        
        # 파라미터
        self.declare_parameter('use_sim_time', False)
        
        # 구독자
        self.initial_pose_sub = self.create_subscription(
            PoseWithCovarianceStamped,
            '/initialpose',
            self.initial_pose_callback,
            10
        )
        
        # 발행자
        self.cartographer_initial_pose_pub = self.create_publisher(
            PoseWithCovarianceStamped,
            '/cartographer_initial_pose',
            10
        )
        
        # TF 버퍼 및 리스너
        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)
        
        self.get_logger().info('초기 위치 설정 노드가 시작되었습니다.')
        self.get_logger().info('2D Pose Estimate를 /initialpose에서 수신하여 카토그래퍼에 전달합니다.')
    
    def initial_pose_callback(self, msg: PoseWithCovarianceStamped):
        """2D Pose Estimate 콜백"""
        self.get_logger().info(f'초기 위치 수신: x={msg.pose.pose.position.x:.2f}, y={msg.pose.pose.position.y:.2f}, yaw={self.quaternion_to_yaw(msg.pose.pose.orientation):.2f}')
        
        # 카토그래퍼용 초기 위치 메시지 생성
        cartographer_pose = PoseWithCovarianceStamped()
        cartographer_pose.header = msg.header
        cartographer_pose.pose = msg.pose
        
        # 카토그래퍼에 초기 위치 전달
        self.cartographer_initial_pose_pub.publish(cartographer_pose)
        
        self.get_logger().info('카토그래퍼에 초기 위치를 전달했습니다.')
    
    def quaternion_to_yaw(self, quaternion):
        """쿼터니언을 yaw 각도로 변환"""
        x = quaternion.x
        y = quaternion.y
        z = quaternion.z
        w = quaternion.w
        
        # Roll (x-axis rotation)
        sinr_cosp = 2 * (w * x + y * z)
        cosr_cosp = 1 - 2 * (x * x + y * y)
        roll = math.atan2(sinr_cosp, cosr_cosp)
        
        # Pitch (y-axis rotation)
        sinp = 2 * (w * y - z * x)
        if abs(sinp) >= 1:
            pitch = math.copysign(math.pi / 2, sinp)  # use 90 degrees if out of range
        else:
            pitch = math.asin(sinp)
        
        # Yaw (z-axis rotation)
        siny_cosp = 2 * (w * z + x * y)
        cosy_cosp = 1 - 2 * (y * y + z * z)
        yaw = math.atan2(siny_cosp, cosy_cosp)
        
        return yaw

def main(args=None):
    rclpy.init(args=args)
    
    node = InitialPoseSetter()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
