#!/usr/bin/env python3

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.substitutions import LaunchConfiguration
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
import launch

def generate_launch_description():
    # 환경 변수 설정
    TURTLEBOT3_MODEL = os.environ.get('TURTLEBOT3_MODEL', 'waffle_pi_4wheel')
    
    # Launch 파라미터
    use_sim_time = LaunchConfiguration('use_sim_time', default='false')
    lidar_port = LaunchConfiguration('lidar_port', default='/dev/ttyUSB0')
    usb_port = LaunchConfiguration('usb_port', default='/dev/ttyACM0')
    enable_rfid = LaunchConfiguration('enable_rfid', default='false')
    enable_ultrasonic_safety = LaunchConfiguration('enable_ultrasonic_safety', default='true')
    safety_distance = LaunchConfiguration('safety_distance', default='0.25')
    slow_distance = LaunchConfiguration('slow_distance', default='0.30')
    warning_distance = LaunchConfiguration('warning_distance', default='0.35')
    stop_duration = LaunchConfiguration('stop_duration', default='3.0')
    
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
            default_value='/dev/ttyACM0',
            description='Connected USB port with OpenCR'),
        
        DeclareLaunchArgument(
            'enable_rfid',
            default_value='false',
            description='Enable RFID tag detection and navigation'),
        
        DeclareLaunchArgument(
            'enable_ultrasonic_safety',
            default_value='true',
            description='Enable ultrasonic safety controller'),
        
        DeclareLaunchArgument(
            'safety_distance',
            default_value='0.25',
            description='Stop distance in meters (default: 25cm)'),
        
        DeclareLaunchArgument(
            'slow_distance',
            default_value='0.30',
            description='Slow down distance in meters (default: 30cm)'),
        
        DeclareLaunchArgument(
            'warning_distance',
            default_value='0.35',
            description='Warning distance in meters (default: 35cm)'),
        
        DeclareLaunchArgument(
            'stop_duration',
            default_value='3.0',
            description='Stop duration in seconds (default: 3.0s)'),
        
        # 1. 하드웨어 브링업 (모터 + 센서 + TF) - 한 번만
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([os.path.join(
                get_package_share_directory('turtlebot3_hardware_bringup'), 'launch', 'hardware.launch.py')]),
            launch_arguments={
                'lidar_port': lidar_port,
                'usb_port': usb_port,
                'use_sim_time': use_sim_time
            }.items(),
        ),
        
        # 2. Cartographer (SLAM) - 하드웨어 제외 (일시적으로 비활성화)
        # IncludeLaunchDescription(
        #     PythonLaunchDescriptionSource([os.path.join(
        #         get_package_share_directory('turtlebot3_cartographer'), 'launch', 'cartographer_only.launch.py')]),
        #     launch_arguments={
        #         'use_sim_time': use_sim_time
        #     }.items(),
        # ),
        
        # 3. Navigation2 - 하드웨어 제외
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([os.path.join(
                get_package_share_directory('turtlebot3_navigation2'), 'launch', 'navigation2_only.launch.py')]),
            launch_arguments={
                'use_sim_time': use_sim_time
            }.items(),
        ),
        
        # 4. 위치 관리 노드 - ExecuteProcess로 실행
        ExecuteProcess(
            cmd=[os.path.join(
                get_package_share_directory('location_manager'),
                '..', '..', 'bin', 'location_manager'
            )],
            output='screen',
            env={
                'TURTLEBOT3_MODEL': TURTLEBOT3_MODEL,
                'PYTHONPATH': os.environ.get('PYTHONPATH', ''),
                'LD_LIBRARY_PATH': os.environ.get('LD_LIBRARY_PATH', ''),
                'PATH': os.environ.get('PATH', ''),
                'ROS_DOMAIN_ID': '10',
                'ROS_VERSION': '2',
                'ROS_DISTRO': 'humble',
                'ROS_LOG_DIR': '/root/.ros/log'
            }
        ),
        
        # 5. RFID 태그 퍼블리셔 (조건부)
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([os.path.join(
                get_package_share_directory('rfid_tag_publisher'), 'launch', 'rfid_tag_publisher.launch.py')]),
            condition=launch.conditions.IfCondition(enable_rfid),
        ),
        
        # 6. RFID 위치 매핑 노드 (조건부)
        Node(
            package='rfid_location_mapper',
            executable='rfid_location_mapper',
            name='rfid_location_mapper',
            output='screen',
            condition=launch.conditions.IfCondition(enable_rfid),
        ),
        
        # 7. LCD 컨트롤러 (위치 정보 표시)
        Node(
            package='lcd_controller',
            executable='lcd_controller',
            name='lcd_controller',
            output='screen',
        ),
        
        # 8. 초음파 센서 퍼블리셔 (조건부)
        Node(
            package='ultrasonic_sensor_bridge',
            executable='ultrasonic_publisher_ros',
            name='ultrasonic_publisher',
            output='screen',
            condition=launch.conditions.IfCondition(enable_ultrasonic_safety),
        ),
        
        # 9. 초음파 안전 제어기 (조건부)
        Node(
            package='ultrasonic_sensor_bridge',
            executable='ultrasonic_safety_controller',
            name='ultrasonic_safety_controller',
            output='screen',
            parameters=[{
                'safety_distance': safety_distance,
                'slow_distance': slow_distance,
                'warning_distance': warning_distance,
                'stop_duration': stop_duration,
            }],
            condition=launch.conditions.IfCondition(enable_ultrasonic_safety),
        ),
        
        # 10. cmd_vel 토픽 리맵핑 (안전 제어 사용 시)
        Node(
            package='ultrasonic_sensor_bridge',
            executable='cmd_vel_relay',
            name='cmd_vel_relay',
            output='screen',
            condition=launch.conditions.IfCondition(enable_ultrasonic_safety),
        ),
        
        
    ])