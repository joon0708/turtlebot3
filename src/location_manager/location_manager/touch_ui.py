#!/usr/bin/env python3

import os
import sys
from typing import Optional

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from PyQt5 import QtCore, QtGui, QtWidgets


class TouchNavUI(QtWidgets.QWidget):
    """PyQt5 touch-friendly UI that publishes /location_command strings."""

    def __init__(self, ros_node: Node):
        super().__init__()
        self.ros_node = ros_node
        self.publisher = self.ros_node.create_publisher(String, '/location_command', 10)

        self.setWindowTitle('TurtleBot3 Touch Navigator')
        self.setAttribute(QtCore.Qt.WA_AcceptTouchEvents, True)
        self.setMinimumSize(640, 400)

        # Use a large, touch-friendly font
        base_font = QtGui.QFont()
        base_font.setPointSize(18)
        self.setFont(base_font)

        # Main layout
        root_layout = QtWidgets.QVBoxLayout()
        root_layout.setContentsMargins(16, 16, 16, 16)
        root_layout.setSpacing(16)

        title = QtWidgets.QLabel('Select Destination')
        title_font = QtGui.QFont(base_font)
        title_font.setPointSize(22)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(QtCore.Qt.AlignCenter)
        root_layout.addWidget(title)

        grid = QtWidgets.QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(16)

        # Buttons
        self.home_btn = self._create_button('HOME', '#2e7d32')
        self.table1_btn = self._create_button('TABLE 1', '#1565c0')
        self.table2_btn = self._create_button('TABLE 2', '#6a1b9a')
        self.table3_btn = self._create_button('TABLE 3', '#c62828')

        grid.addWidget(self.home_btn, 0, 0)
        grid.addWidget(self.table1_btn, 0, 1)
        grid.addWidget(self.table2_btn, 1, 0)
        grid.addWidget(self.table3_btn, 1, 1)

        root_layout.addLayout(grid)

        # Status label
        self.status_lbl = QtWidgets.QLabel('Ready')
        self.status_lbl.setAlignment(QtCore.Qt.AlignCenter)
        root_layout.addWidget(self.status_lbl)

        # Close/Exit button row
        bottom_row = QtWidgets.QHBoxLayout()
        bottom_row.addStretch(1)
        self.exit_btn = self._create_button('EXIT', '#424242')
        self.exit_btn.clicked.connect(self._on_exit)
        self.exit_btn.setFixedHeight(64)
        bottom_row.addWidget(self.exit_btn, 0)
        root_layout.addLayout(bottom_row)

        self.setLayout(root_layout)

        # Connect button signals
        self.home_btn.clicked.connect(lambda: self._send_command('home'))
        self.table1_btn.clicked.connect(lambda: self._send_command('table1'))
        self.table2_btn.clicked.connect(lambda: self._send_command('table2'))
        self.table3_btn.clicked.connect(lambda: self._send_command('table3'))

    def _create_button(self, text: str, color_hex: str) -> QtWidgets.QPushButton:
        btn = QtWidgets.QPushButton(text)
        btn.setCursor(QtCore.Qt.PointingHandCursor)
        btn.setMinimumSize(220, 120)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color_hex};
                color: white;
                border: none;
                border-radius: 12px;
                padding: 16px;
            }}
            QPushButton:pressed {{
                background-color: #00000033;
            }}
        """)
        font = btn.font()
        font.setPointSize(24)
        font.setBold(True)
        btn.setFont(font)
        return btn

    def _send_command(self, location_name: str) -> None:
        """Publish 'go <location>' to /location_command."""
        msg = String()
        msg.data = f'go {location_name}'
        self.publisher.publish(msg)
        self.status_lbl.setText(f'Sent: {msg.data}')
        if self.ros_node is not None:
            self.ros_node.get_logger().info(f'UI published: {msg.data}')

    def _on_exit(self) -> None:
        QtWidgets.QApplication.quit()


class TouchUINode(Node):
    """ROS2 node hosting the PyQt app."""

    def __init__(self):
        super().__init__('touch_ui')
        self.get_logger().info('Touch UI node started')


def main(args: Optional[list] = None) -> None:
    # Initialize ROS first so publishers are ready when UI starts
    rclpy.init(args=args)
    node = TouchUINode()

    # Create the Qt application
    app = QtWidgets.QApplication(sys.argv)
    window = TouchNavUI(node)
    window.showFullScreen() if os.environ.get('TB3_UI_FULLSCREEN', '1') == '1' else window.show()

    # Use a timer to periodically spin the ROS executor so callbacks (if any) work
    timer = QtCore.QTimer()
    timer.timeout.connect(lambda: rclpy.spin_once(node, timeout_sec=0.0))
    timer.start(10)

    # Run the UI event loop
    try:
        app.exec_()
    finally:
        try:
            node.destroy_node()
        except Exception:
            pass
        rclpy.shutdown()


if __name__ == '__main__':
    main()


