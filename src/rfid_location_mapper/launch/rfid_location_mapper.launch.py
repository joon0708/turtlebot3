#!/usr/bin/env python3

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        # Launch 파라미터 선언
        DeclareLaunchArgument(
            'cooldown',
            default_value='2.0',
            description='RFID tag cooldown time in seconds'),
        
        # RFID Location Mapper 노드
        Node(
            package='rfid_location_mapper',
            executable='rfid_location_mapper',
            name='rfid_location_mapper',
            output='screen',
            parameters=[{
                'cooldown': LaunchConfiguration('cooldown'),
            }],
        ),
    ])
