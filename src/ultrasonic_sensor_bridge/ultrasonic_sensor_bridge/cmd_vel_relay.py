#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

class CmdVelRelay(Node):
    def __init__(self):
        super().__init__('cmd_vel_relay')
        
        # /cmd_vel_safe를 구독하고 /cmd_vel로 발행
        self.subscription = self.create_subscription(
            Twist, '/cmd_vel_safe', self.cmd_vel_callback, 10)
        
        self.publisher = self.create_publisher(Twist, '/cmd_vel', 10)
        
        self.get_logger().info('CmdVel Relay started: /cmd_vel_safe -> /cmd_vel')
    
    def cmd_vel_callback(self, msg):
        """안전한 cmd_vel을 /cmd_vel로 전달"""
        self.publisher.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    
    relay = CmdVelRelay()
    
    try:
        rclpy.spin(relay)
    except KeyboardInterrupt:
        pass
    finally:
        relay.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
