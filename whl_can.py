#!/usr/bin/env python

# Copyright 2025 daohu527 <daohu527@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import threading
import time
import keyboard
import logging

from cyber.python.cyber_py3 import cyber
from modules.common_msgs.control_msgs import control_cmd_pb2

CONTROL_TOPIC = "/apollo/control"

SPEED_DELTA = 0.1
STEERING_ANGLE_DELTA = 1


class KeyboardController:
    """Keyboard control class for listening and handling keyboard input using keyboard.read_event()."""

    def __init__(self):
        self.running = True
        self.control_cmd_msg = control_cmd_pb2.ControlCommand()
        self.speed = 0
        self.steering_angle = 0
        self.lock = threading.Lock()

        # Key mapping: call the corresponding function after pressing the key
        self.control_map = {
            "w": self.move_forward,
            "s": self.move_backward,
            "a": self.turn_left,
            "d": self.turn_right,
        }

        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def get_control_cmd(self):
        """Returns the latest control command message."""
        with self.lock:
            return self.control_cmd_msg

    def start(self):
        """Starts the keyboard listening thread using keyboard.read_event()."""
        threading.Thread(target=self._listen_keyboard, daemon=True).start()
        self.logger.info("Keyboard control started, press Esc to exit.")

    def stop(self):
        """Stops keyboard listening."""
        with self.lock:
            self.running = False
        self.logger.info("Keyboard control stopped.")

    def _listen_keyboard(self):
        """Loop reads keyboard events and processes the corresponding control logic."""
        while self.running:
            event = keyboard.read_event()  # Blocking call, wait for the next keyboard event
            if event.event_type == keyboard.KEY_DOWN:
                if event.name == "esc":
                    self.stop()
                    break
                elif event.name in self.control_map:
                    with self.lock:
                        self.control_map[event.name]()
            self.fill_control_cmd()

    def fill_control_cmd(self):
        """Updates the current speed and steering_angle to the protobuf message."""
        with self.lock:
            self.control_cmd_msg.speed = self.speed
            self.control_cmd_msg.steering_angle = self.steering_angle

    def move_forward(self):
        """Forward control: increase speed."""
        self.speed += SPEED_DELTA
        self.logger.info("Forward: speed increased to %s", self.speed)

    def move_backward(self):
        """Backward control: decrease speed."""
        self.speed -= SPEED_DELTA
        self.logger.info("Backward: speed decreased to %s", self.speed)

    def turn_left(self):
        """Turn left control: increase steering angle."""
        self.steering_angle += STEERING_ANGLE_DELTA
        self.logger.info(
            "Turn left: steering angle increased to %s", self.steering_angle)

    def turn_right(self):
        """Turn right control: decrease steering angle."""
        self.steering_angle -= STEERING_ANGLE_DELTA
        self.logger.info(
            "Turn right: steering angle decreased to %s", self.steering_angle)


if __name__ == "__main__":
    cyber.init()
    node = cyber.Node("whl_can")
    writer = node.create_writer(CONTROL_TOPIC, control_cmd_pb2.ControlCommand)

    controller = KeyboardController()
    controller.start()

    try:
        while controller.running:
            time.sleep(0.1)
            cmd = controller.get_control_cmd()
            writer.write(cmd)
    except KeyboardInterrupt:
        controller.stop()

    logging.info("Program exited.")
