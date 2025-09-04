#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from nav_msgs.msg import OccupancyGrid
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy


class MapTopicRelay(Node):
    """
    맵 토픽을 리맵핑하는 노드
    
    Cartographer의 맵 토픽을 /map으로 전달하여
    RViz2에서 맵이 덮어씌워지는 문제를 해결합니다.
    """
    
    def __init__(self):
        super().__init__('map_topic_relay')
        
        # QoS 설정
        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.VOLATILE,
            depth=10
        )
        
        # 파라미터 선언
        self.declare_parameter('input_topic', '/cartographer_map')
        self.declare_parameter('output_topic', '/map')
        
        # 파라미터 로드
        input_topic = self.get_parameter('input_topic').value
        output_topic = self.get_parameter('output_topic').value
        
        # 구독자 및 발행자
        self.map_sub = self.create_subscription(
            OccupancyGrid,
            input_topic,
            self.map_callback,
            qos_profile
        )
        
        self.map_pub = self.create_publisher(
            OccupancyGrid,
            output_topic,
            qos_profile
        )
        
        self.get_logger().info(
            f'MapTopicRelay 노드가 초기화되었습니다. '
            f'입력 토픽: {input_topic}, 출력 토픽: {output_topic}'
        )
    
    def map_callback(self, msg: OccupancyGrid):
        """맵 메시지를 받아서 출력 토픽으로 전달합니다."""
        try:
            # 메시지를 그대로 전달
            self.map_pub.publish(msg)
            
            # 로그 출력 (너무 자주 출력하지 않도록 제한)
            if hasattr(self, '_last_log_time'):
                current_time = self.get_clock().now().nanoseconds
                if current_time - self._last_log_time > 5_000_000_000:  # 5초마다
                    self.get_logger().debug(f'맵 메시지 전달: {msg.header.frame_id}')
                    self._last_log_time = current_time
            else:
                self._last_log_time = self.get_clock().now().nanoseconds
                self.get_logger().info(f'맵 메시지 전달 시작: {msg.header.frame_id}')
                
        except Exception as e:
            self.get_logger().error(f'맵 메시지 전달 중 오류: {e}')


def main(args=None):
    rclpy.init(args=args)
    
    try:
        node = MapTopicRelay()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f'오류 발생: {e}')
    finally:
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
