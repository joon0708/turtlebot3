#!/usr/bin/env python3

import os
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument, 
    IncludeLaunchDescription,
    ExecuteProcess,
    TimerAction
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import (
    LaunchConfiguration, 
    PathJoinSubstitution,
    TextSubstitution
)
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    """
    적응형 SLAM/Localization 모드 전환 시스템을 위한 런치 파일
    
    이 런치 파일은 다음을 포함합니다:
    1. MapComparator: 맵 비교 알고리즘
    2. MapSimilarityChecker: 유사도 분석 및 모드 전환 결정
    3. ModeSwitcher: 실제 모드 전환 수행
    4. Cartographer: SLAM/Localization 엔진
    """
    
    # 환경 변수 설정
    TURTLEBOT3_MODEL = os.environ.get('TURTLEBOT3_MODEL', 'waffle_pi_4wheel')
    
    # 패키지 경로 설정
    map_mode_manager_pkg = get_package_share_directory('map_mode_manager')
    turtlebot3_cartographer_pkg = get_package_share_directory('turtlebot3_cartographer')
    
    # 런치 인자 설정
    use_sim_time = LaunchConfiguration('use_sim_time')
    cartographer_config_dir = LaunchConfiguration('cartographer_config_dir')
    cartographer_config_basename = LaunchConfiguration('cartographer_config_basename')
    
    # 기본값 설정
    default_cartographer_config_dir = os.path.join(
        turtlebot3_cartographer_pkg, 'config'
    )
    default_cartographer_config_basename = 'turtlebot3_lds_2d.lua'
    
    # 런치 인자 선언
    declare_use_sim_time_cmd = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use simulation (Gazebo) clock if true'
    )
    
    declare_cartographer_config_dir_cmd = DeclareLaunchArgument(
        'cartographer_config_dir',
        default_value=default_cartographer_config_dir,
        description='Cartographer configuration directory'
    )
    
    declare_cartographer_config_basename_cmd = DeclareLaunchArgument(
        'cartographer_config_basename',
        default_value=default_cartographer_config_basename,
        description='Cartographer configuration basename'
    )
    
    # MapComparator 노드
    map_comparator_node = Node(
        package='map_mode_manager',
        executable='map_comparator',
        name='map_comparator',
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time,
            'scan_sampling_ratio': 0.1,
            'map_resolution': 0.05,
            'comparison_area_size': 5.0,
            'min_scan_points': 10,
            'max_scan_range': 3.5,
        }],
        env={
            'TURTLEBOT3_MODEL': TURTLEBOT3_MODEL,
            'ROS_DOMAIN_ID': '10',
            'ROS_VERSION': '2',
            'ROS_DISTRO': 'humble'
        }
    )
    
    # MapSimilarityChecker 노드
    map_similarity_checker_node = Node(
        package='map_mode_manager',
        executable='map_similarity_checker',
        name='map_similarity_checker',
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time,
            'similarity_threshold': 0.8,
            'check_interval': 5.0,
            'mode_switch_delay': 2.0,
            'min_samples_for_decision': 3,
            'similarity_window_size': 10,
            'stability_threshold': 0.1,
        }],
        env={
            'TURTLEBOT3_MODEL': TURTLEBOT3_MODEL,
            'ROS_DOMAIN_ID': '10',
            'ROS_VERSION': '2',
            'ROS_DISTRO': 'humble'
        }
    )
    
    # ModeSwitcher 노드 - ExecuteProcess로 직접 실행
    mode_switcher_node = Node(
        package='map_mode_manager',
        executable='mode_switcher',
        name='mode_switcher',
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time,
            'slam_config_file': 'turtlebot3_lds_2d.lua',
            'localization_config_file': 'turtlebot3_lds_2d_localization.lua',
            'cartographer_node_name': 'cartographer_node',
            'config_directory': default_cartographer_config_dir,
            'mode_switch_timeout': 10.0,
            'enable_parameter_validation': True,
        }],
        env={
            'TURTLEBOT3_MODEL': TURTLEBOT3_MODEL,
            'ROS_DOMAIN_ID': '10',
            'ROS_VERSION': '2',
            'ROS_DISTRO': 'humble'
        }
    )
    
    # Cartographer 노드 (적응형 모드)
    cartographer_node = Node(
        package='cartographer_ros',
        executable='cartographer_node',
        name='cartographer_node',
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time,
            'configuration_basename': cartographer_config_basename,
        }],
        arguments=[
            '-configuration_directory', cartographer_config_dir,
            '-configuration_basename', cartographer_config_basename,
        ],
        env={
            'ROS_DOMAIN_ID': '10',
            'ROS_VERSION': '2',
            'ROS_DISTRO': 'humble'
        }
    )
    
    # Cartographer OccupancyGrid 노드
    cartographer_occupancy_grid_node = Node(
        package='cartographer_ros',
        executable='cartographer_occupancy_grid_node',
        name='cartographer_occupancy_grid_node',
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time,
            'publish_period_sec': 1.0,
        }],
        env={
            'ROS_DOMAIN_ID': '10',
            'ROS_VERSION': '2',
            'ROS_DISTRO': 'humble'
        }
    )
    
    # RViz2 노드 (선택적)
    rviz_config_file = os.path.join(
        map_mode_manager_pkg, 'config', 'adaptive_cartographer.rviz'
    )
    
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config_file],
        parameters=[{
            'use_sim_time': use_sim_time,
        }],
        condition=IfCondition(LaunchConfiguration('use_rviz')),
        env={
            'ROS_DOMAIN_ID': '10',
            'ROS_VERSION': '2',
            'ROS_DISTRO': 'humble'
        }
    )
    
    # RViz 사용 여부 인자
    declare_use_rviz_cmd = DeclareLaunchArgument(
        'use_rviz',
        default_value='false',
        description='Launch RViz2 if true'
    )
    
    # 시스템 상태 모니터링 노드 (선택적) - 향후 구현 예정이므로 주석 처리
    # system_monitor_node = ExecuteProcess(
    #     cmd=['python3', os.path.join(
    #         get_package_share_directory('map_mode_manager'),
    #         '..', '..', 'src', 'map_mode_manager', 'map_mode_manager', 'system_monitor.py'
    #     )],
    #     output='screen',
    #     condition=IfCondition(LaunchConfiguration('enable_monitoring')),
    #     env={
    #         'TURTLEBOT3_MODEL': TURTLEBOT3_MODEL,
    #         'ROS_DOMAIN_ID': '10',
    #         'ROS_VERSION': '2',
    #         'ROS_DISTRO': 'humble'
    #     }
    # )
    
    # 모니터링 활성화 인자
    declare_enable_monitoring_cmd = DeclareLaunchArgument(
        'enable_monitoring',
        default_value='false',
        description='Enable system monitoring if true'
    )
    
    # 지연된 시작을 위한 타이머 액션
    # MapComparator와 MapSimilarityChecker는 먼저 시작
    delayed_cartographer = TimerAction(
        period=3.0,
        actions=[cartographer_node]
    )
    
    delayed_occupancy_grid = TimerAction(
        period=5.0,
        actions=[cartographer_occupancy_grid_node]
    )
    
    # 런치 설명 생성
    ld = LaunchDescription()
    
    # 런치 인자 추가
    ld.add_action(declare_use_sim_time_cmd)
    ld.add_action(declare_cartographer_config_dir_cmd)
    ld.add_action(declare_cartographer_config_basename_cmd)
    ld.add_action(declare_use_rviz_cmd)
    ld.add_action(declare_enable_monitoring_cmd)
    
    # 핵심 노드들 추가 (즉시 시작)
    ld.add_action(map_comparator_node)
    ld.add_action(map_similarity_checker_node)
    ld.add_action(mode_switcher_node)
    
    # 지연된 시작 노드들 추가
    ld.add_action(delayed_cartographer)
    ld.add_action(delayed_occupancy_grid)
    
    # 선택적 노드들 추가
    ld.add_action(rviz_node)
    # ld.add_action(system_monitor_node)  # 향후 구현 예정
    
    return ld
