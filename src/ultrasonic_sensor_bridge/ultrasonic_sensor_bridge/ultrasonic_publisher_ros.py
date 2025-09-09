#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Range
from custom_turtlebot3_msgs.msg import SensorState


class UltrasonicPublisherROS(Node):
    def __init__(self):
        super().__init__('ultrasonic_publisher_ros')
        
        # 초음파 센서 토픽 발행
        self.left_pub = self.create_publisher(Range, '/ultrasonic/left', 10)
        self.front_pub = self.create_publisher(Range, '/ultrasonic/front', 10)
        self.right_pub = self.create_publisher(Range, '/ultrasonic/right', 10)
        
        # turtlebot3_ros에서 센서 데이터 구독
        self.sensor_state_sub = self.create_subscription(
            SensorState, 
            '/sensor_state', 
            self.sensor_state_callback, 
            10
        )
        
        self.get_logger().info('Ultrasonic Publisher ROS started - subscribing to turtlebot3_ros')
    
    def sensor_state_callback(self, msg):
        """turtlebot3_ros에서 센서 데이터를 받아서 초음파 센서 데이터로 변환"""
        try:
            # custom_turtlebot3_msgs/SensorState에서 초음파 센서 데이터 추출
            left_val = msg.ultrasonic_left  # 이미 미터 단위
            front_val = msg.ultrasonic_front
            right_val = msg.ultrasonic_right
            
            # 디버깅용 로그 - 원본 값과 변환된 값 모두 출력
            self.get_logger().info(f'Raw from turtlebot3_ros: L={msg.ultrasonic_left:.6f}, F={msg.ultrasonic_front:.6f}, R={msg.ultrasonic_right:.6f}')
            self.get_logger().info(f'Converted values: L={left_val:.3f}, F={front_val:.3f}, R={right_val:.3f}')
            
            # Range 메시지로 발행
            self.publish_range_msg(self.left_pub, left_val, 'ultrasonic_left')
            self.publish_range_msg(self.front_pub, front_val, 'ultrasonic_front')
            self.publish_range_msg(self.right_pub, right_val, 'ultrasonic_right')
                
        except Exception as e:
            self.get_logger().error(f'Error processing sensor state: {e}')
    
    def publish_range_msg(self, publisher, range_value, frame_id):
        """Range 메시지 발행"""
        msg = Range()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = frame_id
        msg.radiation_type = 0  # ULTRASOUND
        msg.field_of_view = 0.1  # 10 degrees
        msg.min_range = 0.02  # 2cm
        msg.max_range = 4.0   # 4m
        msg.range = range_value
        
        publisher.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    
    publisher = UltrasonicPublisherROS()
    
    try:
        rclpy.spin(publisher)
    except KeyboardInterrupt:
        pass
    finally:
        publisher.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
