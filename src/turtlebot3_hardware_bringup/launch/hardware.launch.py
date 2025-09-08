#!/usr/bin/env python3

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.substitutions import LaunchConfiguration, Command
from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource


def generate_launch_description():
    # 환경 변수 설정 - 4바퀴 시스템용
    TURTLEBOT3_MODEL = os.environ.get('TURTLEBOT3_MODEL', 'waffle_pi_4wheel')
    
    # Launch 파라미터
    use_sim_time = LaunchConfiguration('use_sim_time', default='false')
    lidar_port = LaunchConfiguration('lidar_port', default='/dev/ttyUSB0')
    usb_port = LaunchConfiguration('usb_port', default='/dev/ttyACM0')
    namespace = LaunchConfiguration('namespace', default='')
    use_4wheel = LaunchConfiguration('use_4wheel', default='true')
    
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
            'namespace',
            default_value='',
            description='Namespace for nodes'),

        DeclareLaunchArgument(
            'use_4wheel',
            default_value='true',
            description='Use 4-wheel configuration if true'),
        
        # TurtleBot3 State Publisher (TF) - 직접 노드 실행으로 변경
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            output='screen',
            parameters=[{
                'use_sim_time': use_sim_time,
                'robot_description': Command([
                    'xacro ',
                    os.path.join(
                        get_package_share_directory('turtlebot3_description'),
                        'urdf', 'turtlebot3_' + TURTLEBOT3_MODEL + '.urdf'
                    )
                ])
            }],
            env={
                'TURTLEBOT3_MODEL': TURTLEBOT3_MODEL,
                'AMENT_PREFIX_PATH': '/opt/ros/humble:/root/turtlebot3/install',
                'LD_LIBRARY_PATH': '/opt/ros/humble/lib:/root/turtlebot3/install/lib:/root/turtlebot3/install/custom_turtlebot3_msgs/lib:/opt/ros/humble/lib/aarch64-linux-gnu:/lib/aarch64-linux-gnu:/usr/lib/aarch64-linux-gnu:/usr/lib',
                'ROS_LOG_DIR': '/root/.ros/log',
                'ROS_DOMAIN_ID': '10',
                'ROS_VERSION': '2',
                'ROS_DISTRO': 'humble'
            }),
        
        # LD08 LIDAR Node (LDS-02) - 직접 실행
        Node(
            package='ld08_driver',
            executable='ld08_driver',
            name='ld08_driver',
            parameters=[{
                'port': lidar_port,
                'frame_id': 'base_scan',
            }],
            output='screen',
            env={
                'TURTLEBOT3_MODEL': TURTLEBOT3_MODEL,
                'AMENT_PREFIX_PATH': '/opt/ros/humble:/root/turtlebot3/install',
                'LD_LIBRARY_PATH': '/opt/ros/humble/lib:/root/turtlebot3/install/lib:/root/turtlebot3/install/custom_turtlebot3_msgs/lib:/opt/ros/humble/lib/aarch64-linux-gnu:/lib/aarch64-linux-gnu:/usr/lib/aarch64-linux-gnu:/usr/lib',
                'ROS_LOG_DIR': '/root/.ros/log',
                'ROS_DOMAIN_ID': '10',
                'ROS_VERSION': '2',
                'ROS_DISTRO': 'humble'
            }),
        
        # TurtleBot3 Node (Motor Control) - 직접 실행
        Node(
            package='turtlebot3_node',
            executable='turtlebot3_ros',
            name='turtlebot3_ros',  # 기본 이름 사용
            output='screen',
            parameters=[{
                'use_sim_time': use_sim_time,
                'namespace': '',
                'opencr': {
                    'id': 200,
                    'baud_rate': 1000000,
                    'protocol_version': 2.0
                },
                'wheels': {
                    'separation': 0.287,
                    'radius': 0.033,
                    'front_separation': 0.287,
                    'rear_separation': 0.287,
                    'wheelbase': 0.287
                },
                'motors': {
                    'profile_acceleration_constant': 214.577,
                    'profile_acceleration': 0.0,
                    'front_left_id': 1,
                    'front_right_id': 2,
                    'rear_left_id': 3,
                    'rear_right_id': 4,
                    'front_left_position_addr': 136,
                    'front_right_position_addr': 140,
                    'rear_left_position_addr': 141,
                    'rear_right_position_addr': 142,
                    'front_left_velocity_addr': 128,
                    'front_right_velocity_addr': 132,
                    'rear_left_velocity_addr': 133,
                    'rear_right_velocity_addr': 134,
                    'front_left_current_addr': 120,
                    'front_right_current_addr': 124,
                    'rear_left_current_addr': 125,
                    'rear_right_current_addr': 126,
                    'front_left_accel_addr': 174,
                    'front_right_accel_addr': 178,
                    'rear_left_accel_addr': 179,
                    'rear_right_accel_addr': 180
                },
                'sensors': {
                    'bumper_1': 0,
                    'bumper_2': 0,
                    'illumination': 0,
                    'ir': 0,
                    'sonar': 1,  # 기존 초음파 센서 활성화
                    'ultrasonic_left': 1,   # 왼쪽 초음파 센서 활성화
                    'ultrasonic_front': 1,  # 앞쪽 초음파 센서 활성화
                    'ultrasonic_right': 1   # 오른쪽 초음파 센서 활성화
                },
                'odometry': {
                    'frame_id': 'odom',
                    'child_frame_id': 'base_footprint',
                    'publish_tf': True,
                    'use_imu': True,
                    'use_4_wheel_odometry': True,
                    'front_wheels_weight': 0.5,
                    'rear_wheels_weight': 0.5
                }
            }],
            arguments=['-i', usb_port],
            env={
                'TURTLEBOT3_MODEL': TURTLEBOT3_MODEL,
                'AMENT_PREFIX_PATH': '/opt/ros/humble:/root/turtlebot3/install',
                'LD_LIBRARY_PATH': '/opt/ros/humble/lib:/root/turtlebot3/install/lib:/root/turtlebot3/install/custom_turtlebot3_msgs/lib:/opt/ros/humble/lib/aarch64-linux-gnu:/lib/aarch64-linux-gnu:/usr/lib/aarch64-linux-gnu:/usr/lib',
                'ROS_LOG_DIR': '/root/.ros/log',
                'ROS_DOMAIN_ID': '10',
                'ROS_VERSION': '2',
                'ROS_DISTRO': 'humble'
            }),
        
        # 초음파 센서 발행 (Python 스크립트 직접 실행)
        ExecuteProcess(
            cmd=['python3', '/root/turtlebot3/src/ultrasonic_sensor_bridge/ultrasonic_sensor_bridge/ultrasonic_publisher.py'],
            output='screen',
            env={
                'TURTLEBOT3_MODEL': TURTLEBOT3_MODEL,
                'PYTHONPATH': '/root/turtlebot3/src:' + os.environ.get('PYTHONPATH', ''),
                'LD_LIBRARY_PATH': os.environ.get('LD_LIBRARY_PATH', ''),
                'PATH': os.environ.get('PATH', ''),
                'ROS_DOMAIN_ID': '10',
                'ROS_VERSION': '2',
                'ROS_DISTRO': 'humble',
                'ROS_LOG_DIR': '/root/.ros/log',
                'HOME': '/root'
            }
        ),
        
        # 초음파 센서 LaserScan 변환 (Python 스크립트 직접 실행)
        ExecuteProcess(
            cmd=['python3', '/root/turtlebot3/src/ultrasonic_sensor_bridge/ultrasonic_sensor_bridge/ultrasonic_to_laserscan.py'],
            output='screen',
            env={
                'TURTLEBOT3_MODEL': TURTLEBOT3_MODEL,
                'PYTHONPATH': '/root/turtlebot3/src:' + os.environ.get('PYTHONPATH', ''),
                'LD_LIBRARY_PATH': os.environ.get('LD_LIBRARY_PATH', ''),
                'PATH': os.environ.get('PATH', ''),
                'ROS_DOMAIN_ID': '10',
                'ROS_VERSION': '2',
                'ROS_DISTRO': 'humble',
                'ROS_LOG_DIR': '/root/.ros/log',
                'HOME': '/root'
            }
        ),
        
    ])
