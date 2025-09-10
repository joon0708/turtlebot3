#!/usr/bin/env python3

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch.conditions import IfCondition, UnlessCondition
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    # 패키지 디렉토리 가져오기
    pkg_share = get_package_share_directory('ultrasonic_sensor_bridge')
    
    # 런치 인수 선언
    use_direct_connection_arg = DeclareLaunchArgument(
        'use_direct_connection',
        default_value='true',
        description='Use direct OpenCR connection (true) or ROS sensor state (false)'
    )
    
    safety_distance_arg = DeclareLaunchArgument(
        'safety_distance',
        default_value='0.15',
        description='Safety distance in meters (default: 15cm)'
    )
    
    stop_duration_arg = DeclareLaunchArgument(
        'stop_duration',
        default_value='1.0',
        description='Stop duration in seconds (default: 1.0s)'
    )
    
    # 런치 설정 가져오기
    use_direct_connection = LaunchConfiguration('use_direct_connection')
    safety_distance = LaunchConfiguration('safety_distance')
    stop_duration = LaunchConfiguration('stop_duration')
    
    # 초음파 센서 퍼블리셔 노드 (조건부)
    ultrasonic_publisher_node = Node(
        package='ultrasonic_sensor_bridge',
        executable='ultrasonic_publisher',
        name='ultrasonic_publisher',
        output='screen',
        condition=IfCondition(use_direct_connection)
    )
    
    ultrasonic_publisher_ros_node = Node(
        package='ultrasonic_sensor_bridge',
        executable='ultrasonic_publisher_ros',
        name='ultrasonic_publisher_ros',
        output='screen',
        condition=UnlessCondition(use_direct_connection)
    )
    
    # 안전 제어 노드
    safety_controller_node = Node(
        package='ultrasonic_sensor_bridge',
        executable='ultrasonic_safety_controller',
        name='ultrasonic_safety_controller',
        output='screen',
        parameters=[{
            'safety_distance': safety_distance,
            'stop_duration': stop_duration,
        }]
    )
    
    return LaunchDescription([
        use_direct_connection_arg,
        safety_distance_arg,
        stop_duration_arg,
        ultrasonic_publisher_node,
        ultrasonic_publisher_ros_node,
        safety_controller_node,
    ])
