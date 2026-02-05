"""
Author: Matt Lamparter
Based on previous work by James Howe
Updated 2025.11.14
Refactored by Aiden Cherniske 2026.01.28

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
    
    Direction convention:
    - stepper.FORWARD = Counter-clockwise (CCW) = negative step delta
    - stepper.BACKWARD = Clockwise (CW) = positive step delta
    """
    
    # Motor specifications
    STEPS_PER_REVOLUTION = 200  # 1.8 degrees per step
    
    # Homing constants
    _HALL_CLEARANCE_STEPS = 20      # Steps to clear initial Hall sensor edge
    _HALL_SEARCH_MAX_STEPS = 45     # Max steps to search for Hall sensor edges
    _HALL_SEARCH_DELAY = 0.5        # Delay between steps during edge search (seconds)
    _HALL_HYSTERESIS_OFFSET = 4     # Steps to offset for Hall sensor hysteresis
    _MOTOR_SETTLE_DELAY = 0.5       # Time for motor to settle after homing (seconds)

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

        # Hall sensor setup (hardwired to D16/A2 on Feather)
        self._hall = DigitalInOut(board.D16)
        self._hall.direction = Direction.INPUT

        print("Motor initialization complete")

    @property
    def current_step(self):
        """Current position in steps from home (0 to STEPS_PER_REVOLUTION-1)."""
        return self._current_step

    @property
    def current_degree(self):
        """Current position in degrees from home (0.0 to 360.0)."""
        return (self._current_step / self.STEPS_PER_REVOLUTION) * 360.0

    @property
    def stepper(self):
        """
        Direct access to stepper motor object.
        
        Warning: Direct manipulation may desync position tracking.
        """
        return self._stepper

    def find_home(self):
        """
        Locate home position using Hall effect sensor.

        Homing sequence:
        1. Rotate CW until Hall sensor activates
        2. Move CCW past the sensor edge
        3. Slowly move CW to find precise sensor boundaries
        4. Center on the sensor active zone
        5. Rotate CCW to 12 o'clock position (home = 0 steps)
        
        The Hall sensor is physically located at the 3 o'clock position.
        Home (0 degrees) is defined as 12 o'clock position.
        """
        print("Finding home position...")

        edge1, edge2 = self._locate_hall_sensor_edges()
        self._move_to_home_from_hall(edge1, edge2)

        self._current_step = 0
        print("Homing complete. Motor at home position.")

    def _locate_hall_sensor_edges(self):
        """
        Find the boundaries of the Hall sensor active zone.
        
        Returns:
            tuple: (edge1, edge2) - step counts where sensor activates/deactivates
        """
        # Rotate CW until Hall sensor activates (value==0 means active)
        print("Searching for Hall sensor...")
        while self._hall.value:
            self._stepper.onestep(direction=stepper.BACKWARD, style=stepper.DOUBLE)
        print("Hall sensor detected!")

        # Move CCW to clear past the edge
        print("Clearing past sensor edge...")
        self._step_n_times(self._HALL_CLEARANCE_STEPS, stepper.FORWARD)

        # Slowly move CW to find both edges
        print("Mapping sensor boundaries...")
        return self._find_hall_edges()

    def _find_hall_edges(self):
        """
        Slowly scan CW through Hall sensor to find entry and exit edges.
        
        Returns:
            tuple: (edge1, edge2) positions in step count
        """
        edge1 = edge2 = None

        for step_count in range(self._HALL_SEARCH_MAX_STEPS):
            sensor_active = not self._hall.value  # Inverted logic: value==0 means active

            if sensor_active and edge1 is None:
                edge1 = step_count
                print(f"  Edge 1 found at step {edge1}")
            elif not sensor_active and edge1 is not None and edge2 is None:
                edge2 = step_count - 1
                print(f"  Edge 2 found at step {edge2}")
                break

            self._stepper.onestep(direction=stepper.BACKWARD, style=stepper.DOUBLE)
            time.sleep(self._HALL_SEARCH_DELAY)
        else:
            # Loop completed without break - edge2 never found
            print("Warning: Edge 2 never found! Using last position.")
            edge2 = self._HALL_SEARCH_MAX_STEPS - 1

        return edge1 or 0, edge2

    def _move_to_home_from_hall(self, edge1, edge2):
        """
        Move from current position (somewhere near Hall sensor) to home position.
        
        Args:
            edge1: Step count of Hall sensor entry edge
            edge2: Step count of Hall sensor exit edge
        """
        # Move CCW back to center of sensor zone
        center_offset = edge2 - edge1 - self._HALL_HYSTERESIS_OFFSET
        print(f"Centering on sensor ({center_offset} steps CCW)...")
        self._step_n_times(center_offset, stepper.FORWARD)
        time.sleep(0.1)

        # Move CCW from 3 o'clock to 12 o'clock (quarter rotation)
        steps_to_twelve = self.STEPS_PER_REVOLUTION // 4
        print(f"Moving to 12 o'clock position ({steps_to_twelve} steps CCW)...")
        self._step_n_times(steps_to_twelve, stepper.FORWARD)
        time.sleep(self._MOTOR_SETTLE_DELAY)

    def _step_n_times(self, n, direction):
        """Execute n steps in the given direction without updating position."""
        for _ in range(n):
            self._stepper.onestep(direction=direction, style=stepper.DOUBLE)

    def _move_motor(self, steps, direction):
        """
        Move motor a specific number of steps and update position counter.
        
        Args:
            steps: Number of steps to move (positive integer)
            direction: stepper.FORWARD (CCW) or stepper.BACKWARD (CW)
        """
        step_delta = -1 if direction == stepper.FORWARD else 1
        
        for _ in range(steps):
            self._stepper.onestep(direction=direction, style=stepper.DOUBLE)
            self._current_step += step_delta

    def _steps_to_degrees(self, steps):
        """Convert steps to degrees."""
        return (steps / self.STEPS_PER_REVOLUTION) * 360.0

    def _degrees_to_steps(self, degrees):
        """Convert degrees to steps (rounded to nearest integer)."""
        return round((degrees / 360.0) * self.STEPS_PER_REVOLUTION)

    def _normalize_step_count(self):
        """Wrap step count to valid range [0, STEPS_PER_REVOLUTION)."""
        self._current_step %= self.STEPS_PER_REVOLUTION

    def _validate_degrees(self, degrees, min_deg=0, max_deg=360):
        """Validate degree input is within range."""
        if not min_deg <= abs(degrees) <= max_deg:
            print(f"Error: Degrees must be between {min_deg} and {max_deg}")
            return False
        return True

    def _validate_steps(self, steps, max_steps=None):
        """Validate step input is within range."""
        max_steps = max_steps or self.STEPS_PER_REVOLUTION
        if not 0 <= steps <= max_steps:
            print(f"Error: Steps must be between 0 and {max_steps}")
            return False
        return True

    def set_position_degrees(self, target_degrees):
        """
        Move to absolute position specified in degrees.

        Args:
            target_degrees: Target position in degrees (0-360)
        """
        if not self._validate_degrees(target_degrees):
            return

        target_steps = self._degrees_to_steps(target_degrees)
        self._move_to_absolute_step(target_steps)

    def set_position_steps(self, target_steps):
        """
        Move to absolute position specified in steps.

        Args:
            target_steps: Target position in steps (0 to STEPS_PER_REVOLUTION)
        """
        target_steps = int(target_steps)
        if not self._validate_steps(target_steps):
            return

        self._move_to_absolute_step(target_steps)

    def _move_to_absolute_step(self, target_steps):
        """Helper: Move to absolute step position using shortest path."""
        steps_needed = target_steps - self._current_step
        
        if steps_needed == 0:
            return

        direction = stepper.FORWARD if steps_needed < 0 else stepper.BACKWARD
        self._move_motor(abs(steps_needed), direction)

    def move_arm_steps(self, steps):
        """
        Move motor relative to current position (in steps).

        Args:
            steps: Steps to move (negative=CCW, positive=CW)
        """
        steps = int(steps)

        if not self._validate_steps(abs(steps)):
            return

        if steps == 0:
            return

        direction = stepper.FORWARD if steps < 0 else stepper.BACKWARD
        self._move_motor(abs(steps), direction)
        self._normalize_step_count()

    def move_arm_degrees(self, degrees):
        """
        Move motor relative to current position (in degrees).

        Args:
            degrees: Degrees to move (negative=CCW, positive=CW, range: -360 to 360)
        """
        if not self._validate_degrees(degrees, min_deg=-360, max_deg=360):
            return

        steps = self._degrees_to_steps(degrees)
        self.move_arm_steps(steps)

    def reset_position(self):
        """
        Return to home position (0 degrees) using shortest path.
        
        Takes CCW path if in right half (0-180°), CW path if in left half (180-360°).
        """
        if self._current_step == 0:
            return

        # Choose shortest path
        if self._current_step <= self.STEPS_PER_REVOLUTION // 2:
            # Right half: move CCW to home
            steps, direction = self._current_step, stepper.FORWARD
        else:
            # Left half: move CW to home
            steps = self.STEPS_PER_REVOLUTION - self._current_step
            direction = stepper.BACKWARD

        self._move_motor(steps, direction)
        self._current_step = 0

    # Backwards compatibility aliases for old getter methods
    def get_current_step(self):
        """Deprecated: Use current_step property instead."""
        return self.current_step

    def get_current_degree(self):
        """Deprecated: Use current_degree property instead."""
        return self.current_degree

    def get_stepper(self):
        """Deprecated: Use stepper property instead."""
        return self.stepper