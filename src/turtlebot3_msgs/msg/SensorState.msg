########################################
# CONSTANTS
########################################
# Bumper states (states are combined, when multiple bumpers are pressed)
uint8 BUMPER_FORWARD  = 1
uint8 BUMPER_BACKWARD = 2

# Cliff sensor states (states are combined, when multiple cliff sensors are triggered)
uint8 CLIFF = 1

# Ultrasonic sensor states (3 individual sensors)
uint8 ULTRASONIC_LEFT = 1
uint8 ULTRASONIC_FRONT = 2
uint8 ULTRASONIC_RIGHT = 3

# Illumination sensor (states are combined, when multiple illumination sensors are triggered) 
uint8 ILLUMINATION = 1

# Button states (states are combined, when multiple buttons are pressed)
uint8 BUTTON0 = 1
uint8 BUTTON1 = 2

# Motor errors
uint8 ERROR_LEFT_MOTOR  = 1
uint8 ERROR_RIGHT_MOTOR = 2
uint8 ERROR_REAR_LEFT_MOTOR = 3
uint8 ERROR_REAR_RIGHT_MOTOR = 4

# Motor torque
uint8 TORQUE_ON  = 1
uint8 TORQUE_OFF = 2

########################################
# Messages
########################################
std_msgs/Header  header
uint8   bumper
float32 cliff
float32 illumination
uint8   led
uint8  button
bool   torque
int32  left_encoder    # (-2,147,483,648 ~ 2,147,483,647)
int32  right_encoder   # (-2,147,483,648 ~ 2,147,483,647)
int32  rear_left_encoder    # (-2,147,483,648 ~ 2,147,483,647)
int32  rear_right_encoder   # (-2,147,483,648 ~ 2,147,483,647)
float32  battery

# Additional ultrasonic sensors (3 sensors)
float32 ultrasonic_left   # Left ultrasonic sensor (m)
float32 ultrasonic_front  # Front ultrasonic sensor (m)
float32 ultrasonic_right  # Right ultrasonic sensor (m)
