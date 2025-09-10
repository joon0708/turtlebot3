#!/usr/bin/env python3

from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    return LaunchDescription([
        # Launch arguments
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation (Gazebo) clock if true'
        ),
        
        # Ultrasonic Publisher Node (Direct OpenCR Connection)
        Node(
            package='ultrasonic_sensor_bridge',
            executable='ultrasonic_publisher_direct',
            name='ultrasonic_publisher_direct',
            output='screen',
            parameters=[{
                'use_sim_time': LaunchConfiguration('use_sim_time'),
            }],
            remappings=[
                # 토픽 리매핑 (필요시)
            ],
        ),
    ])
