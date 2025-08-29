# TurtleBot3 - 4-Wheel Extended Version
<img src="https://raw.githubusercontent.com/ROBOTIS-GIT/emanual/master/assets/images/platform/turtlebot3/logo_turtlebot3.png" width="300">

## Overview
This is an extended version of TurtleBot3 that supports **4-wheel drive system** instead of the standard 2-wheel differential drive. The system has been modified to handle four motors (Front Left, Front Right, Rear Left, Rear Right) for enhanced stability and maneuverability.

### Motor Configuration
- **Front Left Motor**: ID 1, Address 136 (Position), 128 (Velocity), 120 (Current)
- **Front Right Motor**: ID 2, Address 140 (Position), 132 (Velocity), 124 (Current)  
- **Rear Left Motor**: ID 3, Address 141 (Position), 133 (Velocity), 125 (Current)
- **Rear Right Motor**: ID 4, Address 142 (Position), 134 (Velocity), 126 (Current)

### Software Modifications
- Extended control table for 4 motors
- Modified joint state handling (4 joints instead of 2)
- Updated odometry calculation for 4-wheel system
- Enhanced sensor state messages

- Active Branches: noetic, humble, jazzy, main(rolling)
- Legacy Branches: *-devel

## Open Source Projects Related to TurtleBot3
- [turtlebot3](https://github.com/ROBOTIS-GIT/turtlebot3)
- [turtlebot3_msgs](https://github.com/ROBOTIS-GIT/turtlebot3_msgs)
- [turtlebot3_simulations](https://github.com/ROBOTIS-GIT/turtlebot3_simulations)
- [turtlebot3_manipulation](https://github.com/ROBOTIS-GIT/turtlebot3_manipulation)
- [turtlebot3_manipulation_simulations](https://github.com/ROBOTIS-GIT/turtlebot3_manipulation_simulations)
- [turtlebot3_applications](https://github.com/ROBOTIS-GIT/turtlebot3_applications)
- [turtlebot3_applications_msgs](https://github.com/ROBOTIS-GIT/turtlebot3_applications_msgs)
- [turtlebot3_machine_learning](https://github.com/ROBOTIS-GIT/turtlebot3_machine_learning)
- [turtlebot3_autorace](https://github.com/ROBOTIS-GIT/turtlebot3_autorace)
- [turtlebot3_home_service_challenge](https://github.com/ROBOTIS-GIT/turtlebot3_home_service_challenge)
- [hls_lfcd_lds_driver](https://github.com/ROBOTIS-GIT/hls_lfcd_lds_driver)
- [ld08_driver](https://github.com/ROBOTIS-GIT/ld08_driver)
- [open_manipulator](https://github.com/ROBOTIS-GIT/open_manipulator)
- [dynamixel_sdk](https://github.com/ROBOTIS-GIT/DynamixelSDK)
- [OpenCR-Hardware](https://github.com/ROBOTIS-GIT/OpenCR-Hardware)
- [OpenCR](https://github.com/ROBOTIS-GIT/OpenCR)

## Documentation, Videos, and Community

### Official Documentation
- ⚙️ **[ROBOTIS DYNAMIXEL](https://dynamixel.com/)**
- 📚 **[ROBOTIS e-Manual for Dynamixel SDK](http://emanual.robotis.com/docs/en/software/dynamixel/dynamixel_sdk/overview/)**
- 📚 **[ROBOTIS e-Manual for TurtleBot3](http://turtlebot3.robotis.com/)**
- 📚 **[ROBOTIS e-Manual for OpenMANIPULATOR-X](https://emanual.robotis.com/docs/en/platform/openmanipulator_x/overview/)**

### Learning Resources
- 🎥 **[ROBOTIS YouTube Channel](https://www.youtube.com/@ROBOTISCHANNEL)**
- 🎥 **[ROBOTIS Open Source YouTube Channel](https://www.youtube.com/@ROBOTISOpenSourceTeam)**
- 🎥 **[ROBOTIS TurtleBot3 YouTube Playlist](https://www.youtube.com/playlist?list=PLRG6WP3c31_XI3wlvHlx2Mp8BYqgqDURU)**
- 🎥 **[ROBOTIS OpenMANIPULATOR YouTube Playlist](https://www.youtube.com/playlist?list=PLRG6WP3c31_WpEsB6_Rdt3KhiopXQlUkb)**

### Community & Support
- 💬 **[ROBOTIS Community Forum](https://forum.robotis.com/)**
- 💬 **[TurtleBot category from ROS Community](https://discourse.ros.org/c/turtlebot/)**
