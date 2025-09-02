#!/usr/bin/env python3

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():
    # 환경 변수 설정
    TURTLEBOT3_MODEL = os.environ.get('TURTLEBOT3_MODEL', 'waffle_pi_4wheel')
    
    # Launch 파라미터
    use_sim_time = LaunchConfiguration('use_sim_time', default='false')
    lidar_port = LaunchConfiguration('lidar_port', default='/dev/ttyUSB0')
    usb_port = LaunchConfiguration('usb_port', default='/dev/ttyACM1')
    map_completion_threshold = LaunchConfiguration('map_completion_threshold', default='80.0')
    exploration_speed = LaunchConfiguration('exploration_speed', default='0.2')
    exploration_angular_speed = LaunchConfiguration('exploration_angular_speed', default='0.5')
    
    return LaunchDescription([
        # Launch 파라미터 선언
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation (Gazebo) clock if true'),
        
        DeclareLaunchArgument(
            'lidar_port',
            default_value='/dev/ttyUSB0',
            description='Connected USB port with LIDAR sensor'),
        
        DeclareLaunchArgument(
            'usb_port',
            default_value='/dev/ttyACM1',
            description='Connected USB port with OpenCR'),
            
        DeclareLaunchArgument(
            'map_completion_threshold',
            default_value='80.0',
            description='Map completion threshold (0-100%)'),
            
        DeclareLaunchArgument(
            'exploration_speed',
            default_value='0.2',
            description='Exploration linear speed'),
            
        DeclareLaunchArgument(
            'exploration_angular_speed',
            default_value='0.5',
            description='Exploration angular speed'),
        
        # 1. 하드웨어 브링업 (모터 + 센서 + TF)
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([os.path.join(
                get_package_share_directory('turtlebot3_hardware_bringup'), 'launch', 'hardware.launch.py')]),
            launch_arguments={
                'lidar_port': lidar_port,
                'usb_port': usb_port,
                'use_sim_time': use_sim_time
            }.items(),
        ),
        
        # 2. Cartographer (SLAM)
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([os.path.join(
                get_package_share_directory('turtlebot3_cartographer'), 'launch', 'cartographer.launch.py')]),
            launch_arguments={
                'use_sim_time': use_sim_time,
                'use_rviz': 'false'
            }.items(),
        ),
        
        # 3. Navigation2
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([os.path.join(
                get_package_share_directory('turtlebot3_navigation2'), 'launch', 'navigation2.launch.py')]),
            launch_arguments={
                'use_sim_time': use_sim_time,
                'start_rviz': 'false'
            }.items(),
        ),
        
        # 4. 자동 맵핑 노드
        Node(
            package='auto_mapping_navigation',
            executable='auto_mapper',
            name='auto_mapper',
            output='screen',
            parameters=[{
                'map_completion_threshold': map_completion_threshold,
                'exploration_speed': exploration_speed,
                'exploration_angular_speed': exploration_angular_speed
            }],
            env={
                'ROS_DOMAIN_ID': '10',
                'TURTLEBOT3_MODEL': TURTLEBOT3_MODEL
            }),
            

    ])

