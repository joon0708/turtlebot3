#!/usr/bin/env python3

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    lidar_port = LaunchConfiguration('lidar_port', default='/dev/ttyUSB0')
    
    return LaunchDescription([
        DeclareLaunchArgument(
            'lidar_port',
            default_value='/dev/ttyUSB0',
            description='Connected USB port with LIDAR sensor'),
        
        # LD08 LIDAR Node (LDS-02)
        Node(
            package='ld08_driver',
            executable='ld08_driver',
            name='ld08_driver',
            parameters=[{
                'port': lidar_port,
                'frame_id': 'base_scan',
            }],
            output='screen',
            emulate_tty=True,
            env={
                'ROS_DOMAIN_ID': '10',
                'LD_LIBRARY_PATH': '/opt/ros/humble/lib',
                'ROS_LOG_DIR': '/root/.ros/log'
            }),
    ])
