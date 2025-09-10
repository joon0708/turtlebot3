from setuptools import setup, find_packages
import glob
import os

package_name = 'map_mode_manager'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', glob.glob('launch/*.launch.py')),
        ('share/' + package_name + '/config', glob.glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='TurtleBot3 User',
    maintainer_email='user@example.com',
    description='Adaptive SLAM/Localization mode switching system for TurtleBot3',
    license='Apache License 2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'map_fusion_node = map_mode_manager.map_fusion_node:main',
            'incremental_map_updater = map_mode_manager.incremental_map_updater:main',
            'map_comparator = map_mode_manager.map_comparator:main',
            'map_similarity_checker = map_mode_manager.map_similarity_checker:main',
            'mode_switcher = map_mode_manager.mode_switcher:main',
            'initial_pose_setter = map_mode_manager.initial_pose_setter:main',
            'navigation_map_updater = map_mode_manager.navigation_map_updater:main',
            'map_updater = map_mode_manager.map_updater:main',
        ],
    },
)
