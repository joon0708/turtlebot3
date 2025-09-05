#!/usr/bin/env python3

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    # 환경 변수 설정
    TURTLEBOT3_MODEL = os.environ.get('TURTLEBOT3_MODEL', 'waffle_pi_4wheel')
    
    # Launch 파라미터
    use_sim_time = LaunchConfiguration('use_sim_time', default='false')
    
    return LaunchDescription([
        # Launch 파라미터 선언
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation (Gazebo) clock if true'),
        
        # 카토그래퍼 노드 (SLAM)
        Node(
            package='cartographer_ros',
            executable='cartographer_node',
            name='cartographer_node',
            output='screen',
            parameters=[{
                'use_sim_time': use_sim_time,
            }],
            arguments=[
                '-configuration_directory', os.path.join(
                    get_package_share_directory('turtlebot3_cartographer'), 'config'),
                '-configuration_basename', 'turtlebot3_lds_2d.lua',
            ],
            env={
                'RCLCPP_LOG_LEVEL': 'INFO',
                'RCUTILS_LOGGING_USE_STDOUT': '1',
                'RCUTILS_LOGGING_BUFFERED_STREAM': '1',
                'ROS_DOMAIN_ID': '10',
                'LD_LIBRARY_PATH': '/opt/ros/humble/lib:/opt/ros/humble/lib/aarch64-linux-gnu:' + os.environ.get('LD_LIBRARY_PATH', ''),
                'AMENT_PREFIX_PATH': '/opt/ros/humble',
                'ROS_LOG_DIR': '/tmp/ros_logs',  # 로깅 디렉토리 명시적 설정
                'HOME': '/root'  # 홈 디렉토리 설정
            }
        ),
        
        # 카토그래퍼 맵 발행 노드
        Node(
            package='cartographer_ros',
            executable='cartographer_occupancy_grid_node',
            name='cartographer_occupancy_grid_node',
            output='screen',
            parameters=[{
                'use_sim_time': use_sim_time,
            }],
            arguments=['-resolution', '0.05', '-publish_period_sec', '1.0'],
            env={
                'ROS_DOMAIN_ID': '10',
                'LD_LIBRARY_PATH': '/opt/ros/humble/lib:/opt/ros/humble/lib/aarch64-linux-gnu:' + os.environ.get('LD_LIBRARY_PATH', ''),
                'AMENT_PREFIX_PATH': '/opt/ros/humble',
                'ROS_LOG_DIR': '/tmp/ros_logs',  # 로깅 디렉토리 명시적 설정
                'HOME': '/root'  # 홈 디렉토리 설정
            }
        ),
    ])
