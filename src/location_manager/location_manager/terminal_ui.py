#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

class TerminalUI(Node):
    """터미널 기반 UI for TurtleBot3 navigation."""

    def __init__(self):
        super().__init__('terminal_ui')
        self.publisher = self.create_publisher(String, '/location_command', 10)
        self.get_logger().info('Terminal UI started')
        
        # 메뉴 표시
        self.show_menu()

    def show_menu(self):
        """메뉴를 표시하고 사용자 입력을 받습니다."""
        while rclpy.ok():
            print("\n" + "="*50)
            print("TurtleBot3 Navigation Menu")
            print("="*50)
            print("1. HOME")
            print("2. TABLE 1") 
            print("3. TABLE 2")
            print("4. TABLE 3")
            print("5. EXIT")
            print("="*50)
            
            try:
                choice = input("Select destination (1-5): ").strip()
                
                if choice == '1':
                    self.send_command('home')
                elif choice == '2':
                    self.send_command('table1')
                elif choice == '3':
                    self.send_command('table2')
                elif choice == '4':
                    self.send_command('table3')
                elif choice == '5':
                    print("Exiting...")
                    break
                else:
                    print("Invalid choice. Please select 1-5.")
                    
            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except EOFError:
                print("\nExiting...")
                break

    def send_command(self, location_name: str):
        """위치 명령을 발행합니다."""
        msg = String()
        msg.data = f'go {location_name}'
        self.publisher.publish(msg)
        self.get_logger().info(f'Sent command: {msg.data}')
        print(f"Command sent: {msg.data}")

def main():
    rclpy.init()
    node = TerminalUI()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
