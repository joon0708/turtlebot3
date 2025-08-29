# TurtleBot3 Node - 4-Wheel Extended Version

This package provides the core node for the 4-Wheel TurtleBot3 system, handling motor control, sensor data processing, and odometry calculation for four motors instead of the standard two.

## 4-Wheel Motor System

### Motor Configuration
The system supports four Dynamixel motors with the following configuration:

| Motor | ID | Position Address | Velocity Address | Current Address | Profile Acc Address |
|-------|----|------------------|------------------|-----------------|-------------------|
| Front Left | 1 | 136 | 128 | 120 | 174 |
| Front Right | 2 | 140 | 132 | 124 | 178 |
| Rear Left | 3 | 141 | 133 | 125 | 179 |
| Rear Right | 4 | 142 | 134 | 126 | 180 |

### Control Table Extensions
The control table has been extended to support four motors:

```cpp
// Position control (4 bytes each)
ControlItem present_position_front_left = {136, RAM, 4, READ};
ControlItem present_position_front_right = {140, RAM, 4, READ};
ControlItem present_position_rear_left = {141, RAM, 4, READ};
ControlItem present_position_rear_right = {142, RAM, 4, READ};

// Velocity control (4 bytes each)
ControlItem present_velocity_front_left = {128, RAM, 4, READ};
ControlItem present_velocity_front_right = {132, RAM, 4, READ};
ControlItem present_velocity_rear_left = {133, RAM, 4, READ};
ControlItem present_velocity_rear_right = {134, RAM, 4, READ};

// Current monitoring (4 bytes each)
ControlItem present_current_front_left = {120, RAM, 4, READ};
ControlItem present_current_front_right = {124, RAM, 4, READ};
ControlItem present_current_rear_left = {125, RAM, 4, READ};
ControlItem present_current_rear_right = {126, RAM, 4, READ};
```

## Modified Components

### 1. Joint State Handling
- **Joint Count**: Extended from 2 to 4 joints
- **Joint Names**: 
  - `wheel_left_joint` (Front Left)
  - `wheel_right_joint` (Front Right)
  - `wheel_rear_left_joint` (Rear Left)
  - `wheel_rear_right_joint` (Rear Right)

### 2. Odometry Calculation
- **4-Wheel Odometry**: Uses all four wheels for position calculation
- **Translational Motion**: Average of all four wheel movements
- **Rotational Motion**: Uses front wheels for rotation calculation
- **Enhanced Accuracy**: Better position tracking with four wheels

### 3. Sensor State Messages
- **Extended Encoder Data**: All four motor encoders included
- **Enhanced Error Reporting**: Individual motor error states
- **Comprehensive Status**: Complete 4-wheel system status

## Topics

### Published Topics
- `/joint_states` (sensor_msgs/JointState): 4-wheel joint states
- `/odom` (nav_msgs/Odometry): 4-wheel odometry data
- `/sensor_state` (turtlebot3_msgs/SensorState): Extended sensor data
- `/imu` (sensor_msgs/Imu): IMU data
- `/battery_state` (sensor_msgs/BatteryState): Battery information

### Subscribed Topics
- `/cmd_vel` (geometry_msgs/Twist): Velocity commands
- `/cmd_vel_stamped` (geometry_msgs/TwistStamped): Timestamped velocity commands

## Parameters

### Motor Parameters
- `motors.profile_acceleration_constant`: 214.577
- `motors.profile_acceleration`: 0.0

### Wheel Parameters
- `wheels.separation`: Wheel separation distance
- `wheels.radius`: Wheel radius

### OpenCR Parameters
- `opencr.id`: 200
- `opencr.baud_rate`: 1000000
- `opencr.protocol_version`: 2.0

## Hardware Requirements

- **OpenCR 1.0**: Modified firmware for 4 motors
- **4x Dynamixel Motors**: XL430-W250 or compatible
- **Power Supply**: Sufficient power for 4 motors
- **Wiring**: Proper motor connections with unique IDs

## Building

```bash
# Build the package
colcon build --packages-select turtlebot3_node

# Source the workspace
source install/setup.bash
```

## Usage

```bash
# Launch the 4-wheel TurtleBot3 node
ros2 launch turtlebot3_bringup robot.launch.py

# Or run directly
ros2 run turtlebot3_node turtlebot3_node
```

## Compatibility

This package is compatible with:
- ROS2 Humble
- ROS2 Iron
- ROS2 Rolling
- OpenCR 1.0 with 4-motor firmware

## License

Apache License 2.0
