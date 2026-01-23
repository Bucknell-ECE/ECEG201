"""
Author: Matt Lamparter
Based on previous work by James Howe
Updated 2025.11.14
Refactored by Aiden Cherniske 2026.01.23

A class for controlling a stepper motor with position tracking and homing.

This library is based on the Adafruit product 2927:
https://www.adafruit.com/product/2927

Hardware:
- NEMA 8 stepper: 200 steps per revolution (1.8 degrees per step)
- Hall effect sensor at 3 o'clock position for homing

Requires an I2C bus instance to be passed during initialization.
"""

import board
import time
from digitalio import DigitalInOut, Direction
from adafruit_motorkit import MotorKit
from adafruit_motor import stepper


class ECEGMotor:
    """
    Manages stepper motor position tracking and movement.
    
    The motor can be controlled in steps or degrees, with automatic
    position wrapping and a Hall sensor-based homing routine.
    """
    
    # Motor specifications
    STEPS_FOR_FULL = 200  # Steps per full rotation
    
    # Homing constants
    HALL_CLEARANCE_STEPS = 20       # Steps to clear initial Hall sensor edge
    HALL_SEARCH_MAX_STEPS = 45      # Max steps to search for Hall sensor edge
    HALL_SEARCH_DELAY = 0.5         # Delay between steps (seconds)
    HALL_HYSTERESIS_OFFSET = 4      # Steps to offset for Hall sensor hysteresis
    MOTOR_SETTLE_DELAY = 0.5        # Time for motor to settle after homing (seconds)
    STEPS_TO_12_OCLOCK = STEPS_FOR_FULL // 4  # Quarter rotation

    def __init__(self, i2c_bus):
        """
        Initialize the motor controller.

        Args:
            i2c_bus: An initialized I2C bus instance
        """
        self._kit = MotorKit(i2c=i2c_bus)
        self._stepper = self._kit.stepper1
        self._stepper.release()
        self._current_step = 0

        # Hall sensor setup (hardwired to D16/A2)
        self._hall = DigitalInOut(board.D16)
        self._hall.direction = Direction.INPUT

        print("Motor initialization complete")

    def find_home(self):
        """
        Locate home position using Hall effect sensor.

        Process:
        1. Rotate CW until Hall sensor edge detected
        2. Back up past the edge
        3. Slowly find both edges of sensor active zone
        4. Center on the active zone
        5. Rotate to 12 o'clock position (home)
        """
        print("Finding home position...")

        # Find initial edge
        self._find_initial_edge()

        # Clear past the edge
        self._move_steps(self.HALL_CLEARANCE_STEPS, stepper.BACKWARD)

        # Find precise edge boundaries
        edge1, edge2 = self._find_hall_edges()

        # Center on Hall sensor
        self._center_on_hall(edge1, edge2)

        # Move to 12 o'clock position
        self._move_steps(self.STEPS_TO_12_OCLOCK, stepper.BACKWARD)
        time.sleep(self.MOTOR_SETTLE_DELAY)

        self._current_step = 0
        print("Homing complete. Motor at home position.")

    def _find_initial_edge(self):
        """Rotate CW until Hall sensor edge is detected."""
        while True:
            self._stepper.onestep(direction=stepper.BACKWARD, style=stepper.DOUBLE)
            if self._hall.value == 0:
                print("Initial edge detected")
                break

    def _find_hall_edges(self):
        """
        Locate both edges of Hall sensor active zone.

        Returns:
            tuple: (edge1, edge2) in steps
        """
        edge1 = 0
        edge2 = 0
        step_count = 0

        for i in range(self.HALL_SEARCH_MAX_STEPS):
            is_hall_active = not self._hall.value

            # Check for edge2 (exit from active zone)
            if not is_hall_active and edge1 != 0 and edge2 == 0:
                edge2 = step_count - 1
                print("Edge 2 found")
                break

            # Check for edge1 (entry into active zone)
            if is_hall_active and edge1 == 0:
                edge1 = step_count
                print("Edge 1 found")

            self._stepper.onestep(direction=stepper.BACKWARD, style=stepper.DOUBLE)
            step_count += 1
            time.sleep(self.HALL_SEARCH_DELAY)

            # Timeout check
            if i == self.HALL_SEARCH_MAX_STEPS - 1 and edge2 == 0:
                print("Warning: Edge 2 never found")

        return edge1, edge2

    def _center_on_hall(self, edge1, edge2):
        """
        Center motor on Hall sensor active zone.

        Args:
            edge1: Step count of first edge
            edge2: Step count of second edge
        """
        center_offset = edge2 - edge1 - self.HALL_HYSTERESIS_OFFSET
        self._move_steps(center_offset, stepper.FORWARD)
        time.sleep(0.1)

    def _move_steps(self, steps, direction):
        """
        Move motor a specific number of steps in a given direction.

        Args:
            steps: Number of steps to move
            direction: stepper.FORWARD or stepper.BACKWARD
        """
        step_delta = -1 if direction == stepper.FORWARD else 1

        for _ in range(steps):
            self._stepper.onestep(direction=direction, style=stepper.DOUBLE)
            self._current_step += step_delta

    def check_and_update_step_count(self):
        """Normalize step count to valid range using modulo arithmetic."""
        self._current_step %= self.STEPS_FOR_FULL

    def get_current_step(self):
        """
        Get current position in steps from home.

        Returns:
            int: Current step count (0 to STEPS_FOR_FULL-1)
        """
        return self._current_step

    def get_stepper(self):
        """
        Get direct access to stepper motor object.

        Returns:
            Stepper motor instance from MotorKit
        """
        return self._stepper

    def get_current_degree(self):
        """
        Get current position in degrees from home.

        Returns:
            float: Position in degrees (0.0 to 360.0)
        """
        return (self._current_step / self.STEPS_FOR_FULL) * 360.0

    def set_position_degrees(self, pos):
        """
        Move to absolute position specified in degrees.

        Args:
            pos: Target position in degrees (0-360)
        """
        if not 0 <= pos <= 360:
            print("Error: Position must be between 0 and 360 degrees")
            return

        goal_steps = int((pos / 360) * self.STEPS_FOR_FULL)
        steps_to_take = goal_steps - self._current_step

        direction = stepper.FORWARD if steps_to_take < 0 else stepper.BACKWARD
        self._move_steps(abs(steps_to_take), direction)

    def set_position_steps(self, pos):
        """
        Move to absolute position specified in steps.

        Args:
            pos: Target position in steps (0 to STEPS_FOR_FULL)
        """
        if not 0 <= pos <= self.STEPS_FOR_FULL:
            print(f"Error: Position must be between 0 and {self.STEPS_FOR_FULL} steps")
            return

        pos = int(pos)
        steps_to_take = pos - self._current_step

        direction = stepper.FORWARD if steps_to_take < 0 else stepper.BACKWARD
        self._move_steps(abs(steps_to_take), direction)

    def reset_position(self):
        """
        Return to home position using shortest path.

        Chooses CCW if in right half (0-180°), CW if in left half (180-360°).
        """
        if self._current_step <= self.STEPS_FOR_FULL // 2:
            # Right half: move CCW to home
            self._move_steps(self._current_step, stepper.FORWARD)
        else:
            # Left half: move CW to home
            steps_to_move = self.STEPS_FOR_FULL - self._current_step
            self._move_steps(steps_to_move, stepper.BACKWARD)

        self._current_step = 0

    def move_arm_steps(self, amount):
        """
        Move motor relative to current position (in steps).

        Args:
            amount: Steps to move (negative=CCW, positive=CW)
        """
        amount = int(amount)

        if abs(amount) > self.STEPS_FOR_FULL:
            print(f"Error: Movement exceeds {self.STEPS_FOR_FULL} steps")
            return

        direction = stepper.FORWARD if amount < 0 else stepper.BACKWARD
        self._move_steps(abs(amount), direction)
        self.check_and_update_step_count()

    def move_arm_degrees(self, degrees):
        """
        Move motor relative to current position (in degrees).

        Args:
            degrees: Degrees to move (negative=CCW, positive=CW, -360 to 360)
        """
        if abs(degrees) > 360:
            print("Error: Movement must be between -360 and 360 degrees")
            return

        requested_steps = int((degrees / 360) * self.STEPS_FOR_FULL)
        direction = stepper.FORWARD if requested_steps < 0 else stepper.BACKWARD
        self._move_steps(abs(requested_steps), direction)
        self.check_and_update_step_count()