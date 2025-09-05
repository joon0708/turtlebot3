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
                'configuration_basename': 'turtlebot3_lds_2d.lua'  # 기본 설정 사용 (정상 작동 확인됨)
            }],
            arguments=[
                '-configuration_directory', os.path.join(
                    get_package_share_directory('turtlebot3_cartographer'), 'config'),
                '-configuration_basename', 'turtlebot3_lds_2d.lua',  # 기본 SLAM 모드
            ],
            remappings=[
                ('/tf', '/cartographer_tf'),  # 카토그래퍼 TF를 별도 토픽으로 발행
                ('/tf_static', '/cartographer_tf_static')
            ],
            env={
                'RCLCPP_LOG_LEVEL': 'INFO',  # INFO 레벨로 변경
                'RCUTILS_LOGGING_USE_STDOUT': '1',
                'RCUTILS_LOGGING_BUFFERED_STREAM': '1',
                'ROS_DOMAIN_ID': '10',  # 도메인 ID 명시적 설정
                'LD_LIBRARY_PATH': '/opt/ros/humble/lib:/opt/ros/humble/lib/aarch64-linux-gnu:' + os.environ.get('LD_LIBRARY_PATH', ''),
                'AMENT_PREFIX_PATH': '/opt/ros/humble',
                'ROS_LOG_DIR': '/tmp/ros_logs',  # 로깅 디렉토리 명시적 설정
                'HOME': '/root'  # 홈 디렉토리 설정
            }
        ),
        
        # 2.5. 초기 위치 설정 노드 (기본 카토그래퍼에서는 수동 설정 필요)
        # ExecuteProcess(
        #     cmd=['python3', os.path.join(
        #         get_package_share_directory('map_mode_manager'),
        #         '..', '..', '..', '..', 'src', 'map_mode_manager', 
        #         'map_mode_manager', 'initial_pose_setter.py'
        #     )],
        #     output='screen',
        #     env={
        #         'TURTLEBOT3_MODEL': TURTLEBOT3_MODEL,
        #         'PYTHONPATH': os.environ.get('PYTHONPATH', ''),
        #         'LD_LIBRARY_PATH': os.environ.get('LD_LIBRARY_PATH', ''),
        #         'PATH': os.environ.get('PATH', ''),
        #         'ROS_DOMAIN_ID': '10',
        #         'ROS_VERSION': '2',
        #         'ROS_DISTRO': 'humble'
        #     }
        # ),
        
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
                ('/map', '/cartographer_map'),
                ('/tf', '/cartographer_tf'),  # 카토그래퍼 TF 토픽 사용
                ('/tf_static', '/cartographer_tf_static')
            ],
            env={
                'ROS_DOMAIN_ID': '10',  # 도메인 ID 명시적 설정
                'LD_LIBRARY_PATH': '/opt/ros/humble/lib:/opt/ros/humble/lib/aarch64-linux-gnu:' + os.environ.get('LD_LIBRARY_PATH', ''),
                'AMENT_PREFIX_PATH': '/opt/ros/humble',
                'ROS_LOG_DIR': '/tmp/ros_logs',  # 로깅 디렉토리 명시적 설정
                'HOME': '/root'  # 홈 디렉토리 설정
            }
        ),
        
        # 3.5. TF 브리지 (카토그래퍼 TF를 메인 TF로 변환)
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='cartographer_to_main_tf_bridge',
            output='screen',
            arguments=['0', '0', '0', '0', '0', '0', 'map', 'cartographer_map'],
            env={
                'ROS_DOMAIN_ID': '10'
            }
        ),
        
        # 4. Navigation2 (기존 맵 사용, AMCL 포함 - 맵 비교를 위해, TF 브로드캐스트 비활성화)
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([os.path.join(
                get_package_share_directory('turtlebot3_navigation2'), 'launch', 'navigation2_only.launch.py')]),
            launch_arguments={
                'use_sim_time': use_sim_time,
                'map': os.path.join(
                    get_package_share_directory('turtlebot3_navigation2'), 'map', 'map.yaml'),
                'amcl_tf_broadcast': 'false',  # AMCL TF 브로드캐스트 비활성화
                'amcl_use_map_topic': 'true',  # 맵 토픽 사용
                'amcl_global_frame_id': 'map',  # 글로벌 프레임 명시
                'amcl_odom_frame_id': 'odom',   # 오도메트리 프레임 명시
                'amcl_base_frame_id': 'base_footprint',  # 베이스 프레임 명시
                'amcl_initial_pose_x': '0.0',   # 초기 위치 설정
                'amcl_initial_pose_y': '0.0',
                'amcl_initial_pose_a': '0.0'
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
