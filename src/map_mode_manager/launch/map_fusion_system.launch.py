#!/usr/bin/env python3

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, TimerAction, IncludeLaunchDescription
from launch.substitutions import LaunchConfiguration
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():
    # 환경 변수 설정
    TURTLEBOT3_MODEL = os.environ.get('TURTLEBOT3_MODEL', 'waffle_pi_4wheel')
    
    # Launch 파라미터
    use_sim_time = LaunchConfiguration('use_sim_time', default='false')
    lidar_port = LaunchConfiguration('lidar_port', default='/dev/ttyUSB0')
    usb_port = LaunchConfiguration('usb_port', default='/dev/ttyACM0')
    
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
        
        # 2. 실시간 맵 생성 (카토그래퍼 SLAM) - 새로운 맵 생성
        Node(
            package='cartographer_ros',
            executable='cartographer_node',
            name='cartographer_node',
            output='screen',
            parameters=[{
                'use_sim_time': use_sim_time,
                'publish_tf': True,  # TF 브로드캐스트 활성화 (카토그래퍼가 TF 담당)
            }],
            arguments=[
                '-configuration_directory', os.path.join(
                    get_package_share_directory('turtlebot3_cartographer'), 'config'),
                '-configuration_basename', 'turtlebot3_lds_2d_with_initial_pose.lua',  # 초기 위치 설정 가능한 SLAM 모드
            ]
        ),
        
        # 2.5. 초기 위치 설정 노드 (ExecuteProcess로 직접 실행)
        ExecuteProcess(
            cmd=['python3', os.path.join(
                get_package_share_directory('map_mode_manager'),
                '..', '..', '..', '..', 'src', 'map_mode_manager', 
                'map_mode_manager', 'initial_pose_setter.py'
            )],
            output='screen',
            env={
                'TURTLEBOT3_MODEL': TURTLEBOT3_MODEL,
                'PYTHONPATH': os.environ.get('PYTHONPATH', ''),
                'LD_LIBRARY_PATH': os.environ.get('LD_LIBRARY_PATH', ''),
                'PATH': os.environ.get('PATH', ''),
                'ROS_DOMAIN_ID': '10',
                'ROS_VERSION': '2',
                'ROS_DISTRO': 'humble'
            }
        ),
        
        # 3. 카토그래퍼 맵을 /cartographer_map 토픽으로 발행
        Node(
            package='cartographer_ros',
            executable='cartographer_occupancy_grid_node',
            name='cartographer_occupancy_grid_node',
            output='screen',
            parameters=[{
                'use_sim_time': use_sim_time,
            }],
            arguments=['-resolution', '0.05', '-publish_period_sec', '1.0'],
            remappings=[
                ('/map', '/cartographer_map')
            ]
        ),
        
        # 4. Navigation2 (기존 맵 사용, AMCL 포함 - 맵 비교를 위해, TF 브로드캐스트 비활성화)
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([os.path.join(
                get_package_share_directory('turtlebot3_navigation2'), 'launch', 'navigation2_only.launch.py')]),
            launch_arguments={
                'use_sim_time': use_sim_time,
                'map': os.path.join(
                    get_package_share_directory('turtlebot3_navigation2'), 'map', 'map.yaml'),
                'amcl_tf_broadcast': 'false'  # AMCL TF 브로드캐스트 비활성화
            }.items(),
        ),
        
        # 5. 맵 비교 및 통합 노드 (지연 시작)
        TimerAction(
            period=5.0,
            actions=[
                ExecuteProcess(
                    cmd=['python3', os.path.join(
                        get_package_share_directory('map_mode_manager'),
                        '..', '..', '..', '..', 'src', 'map_mode_manager', 
                        'map_mode_manager', 'map_fusion_node.py'
                    )],
                    output='screen',
                    env={
                        'TURTLEBOT3_MODEL': TURTLEBOT3_MODEL,
                        'PYTHONPATH': os.environ.get('PYTHONPATH', ''),
                        'LD_LIBRARY_PATH': os.environ.get('LD_LIBRARY_PATH', ''),
                        'PATH': os.environ.get('PATH', ''),
                        'ROS_DOMAIN_ID': '10',
                        'ROS_VERSION': '2',
                        'ROS_DISTRO': 'humble'
                    }
                )
            ]
        ),
        
        # 6. 점진적 맵 업데이트 노드 (지연 시작)
        TimerAction(
            period=7.0,
            actions=[
                ExecuteProcess(
                    cmd=['python3', os.path.join(
                        get_package_share_directory('map_mode_manager'),
                        '..', '..', '..', '..', 'src', 'map_mode_manager', 
                        'map_mode_manager', 'incremental_map_updater.py'
                    )],
                    output='screen',
                    env={
                        'TURTLEBOT3_MODEL': TURTLEBOT3_MODEL,
                        'PYTHONPATH': os.environ.get('PYTHONPATH', ''),
                        'LD_LIBRARY_PATH': os.environ.get('LD_LIBRARY_PATH', ''),
                        'PATH': os.environ.get('PATH', ''),
                        'ROS_DOMAIN_ID': '10',
                        'ROS_VERSION': '2',
                        'ROS_DISTRO': 'humble'
                    }
                )
            ]
        ),
        
        # 7. 기존 map_mode_manager 노드들 (지연 시작)
        TimerAction(
            period=8.0,
            actions=[
                ExecuteProcess(
                    cmd=['python3', os.path.join(
                        get_package_share_directory('map_mode_manager'),
                        '..', '..', '..', '..', 'src', 'map_mode_manager', 
                        'map_mode_manager', 'map_comparator.py'
                    )],
                    output='screen',
                    env={
                        'TURTLEBOT3_MODEL': TURTLEBOT3_MODEL,
                        'PYTHONPATH': os.environ.get('PYTHONPATH', ''),
                        'LD_LIBRARY_PATH': os.environ.get('LD_LIBRARY_PATH', ''),
                        'PATH': os.environ.get('PATH', ''),
                        'ROS_DOMAIN_ID': '10',
                        'ROS_VERSION': '2',
                        'ROS_DISTRO': 'humble'
                    }
                )
            ]
        ),
        
        TimerAction(
            period=9.0,
            actions=[
                ExecuteProcess(
                    cmd=['python3', os.path.join(
                        get_package_share_directory('map_mode_manager'),
                        '..', '..', '..', '..', 'src', 'map_mode_manager', 
                        'map_mode_manager', 'map_similarity_checker.py'
                    )],
                    output='screen',
                    env={
                        'TURTLEBOT3_MODEL': TURTLEBOT3_MODEL,
                        'PYTHONPATH': os.environ.get('PYTHONPATH', ''),
                        'LD_LIBRARY_PATH': os.environ.get('LD_LIBRARY_PATH', ''),
                        'PATH': os.environ.get('PATH', ''),
                        'ROS_DOMAIN_ID': '10',
                        'ROS_VERSION': '2',
                        'ROS_DISTRO': 'humble'
                    }
                )
            ]
        ),
        
        TimerAction(
            period=10.0,
            actions=[
                ExecuteProcess(
                    cmd=['python3', os.path.join(
                        get_package_share_directory('map_mode_manager'),
                        '..', '..', '..', '..', 'src', 'map_mode_manager', 
                        'map_mode_manager', 'mode_switcher.py'
                    )],
                    output='screen',
                    env={
                        'TURTLEBOT3_MODEL': TURTLEBOT3_MODEL,
                        'PYTHONPATH': os.environ.get('PYTHONPATH', ''),
                        'LD_LIBRARY_PATH': os.environ.get('LD_LIBRARY_PATH', ''),
                        'PATH': os.environ.get('PATH', ''),
                        'ROS_DOMAIN_ID': '10',
                        'ROS_VERSION': '2',
                        'ROS_DISTRO': 'humble'
                    }
                )
            ]
        ),
    ])
