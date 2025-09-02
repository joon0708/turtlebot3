#!/usr/bin/env python3

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'bus',
            default_value='0',
            description='SPI bus number'),

        DeclareLaunchArgument(
            'device',
            default_value='0',
            description='SPI device number'),

        DeclareLaunchArgument(
            'hold_ms',
            default_value='80',
            description='Hold time in milliseconds'),

        DeclareLaunchArgument(
            'cooldown',
            default_value='1.0',
            description='Cooldown time in seconds'),

        DeclareLaunchArgument(
            'grace_ms',
            default_value='200',
            description='Grace period in milliseconds'),

        DeclareLaunchArgument(
            'whitelist',
            default_value='',
            description='Comma-separated list of whitelisted UIDs'),

        DeclareLaunchArgument(
            'rst_bcm',
            default_value='24',
            description='BCM line number for reset pin'),

        Node(
            package='rfid_tag_publisher',
            executable='rfid_tag_publisher',
            name='rfid_tag_publisher',
            parameters=[{
                'bus': LaunchConfiguration('bus'),
                'device': LaunchConfiguration('device'),
                'hold_ms': LaunchConfiguration('hold_ms'),
                'cooldown': LaunchConfiguration('cooldown'),
                'grace_ms': LaunchConfiguration('grace_ms'),
                'whitelist': LaunchConfiguration('whitelist'),
                'rst_bcm': LaunchConfiguration('rst_bcm'),
            }],
            output='screen'),
    ])
