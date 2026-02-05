"""
Motor (Stepper) Comprehensive Test Suite

This script systematically tests all functions and features available in the
ECEGMotor class. Each test is clearly labeled and demonstrates different
motor control capabilities.

Author: Aiden Cherniske
Date: 2026-01-30
"""

import board
import busio
import time

from motorFunctions import ECEGMotor


# Test configuration
PAUSE_BETWEEN_TESTS = 2.0  # seconds between tests
MOVEMENT_DELAY = 0.5  # seconds to pause after movements to observe


def print_test_header(test_name, description=""):
    """Print a formatted test header."""
    print("\n" + "=" * 60)
    print(f"TEST: {test_name}")
    if description:
        print(f"Description: {description}")
    print("=" * 60)


def pause(duration=None):
    """Pause for a specified duration."""
    duration = duration or PAUSE_BETWEEN_TESTS
    time.sleep(duration)


def print_motor_status(motor):
    """Print current motor position."""
    print(f"  Current Position: Step {motor.current_step}, {motor.current_degree:.1f}°")


def test_initialization(i2c):
    """Test motor initialization."""
    print_test_header("Motor Initialization", "Initialize motor controller")
    
    try:
        motor = ECEGMotor(i2c)
        print("  ✓ Motor initialized successfully")
        print_motor_status(motor)
        return motor
    except Exception as e:
        print(f"  ✗ Motor initialization failed: {e}")
        return None


def test_homing(motor):
    """Test motor homing sequence."""
    print_test_header("Motor Homing", "Find home position using Hall sensor")
    
    print("  Starting homing sequence...")
    try:
        motor.find_home()
        print("  ✓ Homing complete")
        print_motor_status(motor)
        pause()
        return True
    except Exception as e:
        print(f"  ✗ Homing failed: {e}")
        return False


def test_absolute_position_degrees(motor):
    """Test absolute positioning in degrees."""
    print_test_header("Absolute Position (Degrees)", "Move to specific degree positions")
    
    positions = [0, 45, 90, 135, 180, 225, 270, 315, 0]
    
    for pos in positions:
        print(f"  Moving to {pos}°...")
        motor.set_position_degrees(pos)
        time.sleep(MOVEMENT_DELAY)
        print_motor_status(motor)
    
    print("  ✓ Absolute degree positioning test complete")
    pause()


def test_absolute_position_steps(motor):
    """Test absolute positioning in steps."""
    print_test_header("Absolute Position (Steps)", "Move to specific step positions")
    
    # Test quarter rotation increments (50 steps = 90 degrees)
    positions = [0, 50, 100, 150, 200, 150, 100, 50, 0]
    
    for pos in positions:
        print(f"  Moving to step {pos} ({motor._steps_to_degrees(pos):.1f}°)...")
        motor.set_position_steps(pos)
        time.sleep(MOVEMENT_DELAY)
        print_motor_status(motor)
    
    print("  ✓ Absolute step positioning test complete")
    pause()


def test_relative_movement_degrees(motor):
    """Test relative movement in degrees."""
    print_test_header("Relative Movement (Degrees)", "Move relative to current position")
    
    # Start at home
    motor.set_position_degrees(0)
    print("  Starting at home (0°)")
    print_motor_status(motor)
    time.sleep(MOVEMENT_DELAY)
    
    # Move in increments
    movements = [30, 30, 30, -45, -45, 90, -90]
    
    for move in movements:
        direction = "CW" if move > 0 else "CCW"
        print(f"  Moving {abs(move)}° {direction}...")
        motor.move_arm_degrees(move)
        time.sleep(MOVEMENT_DELAY)
        print_motor_status(motor)
    
    print("  ✓ Relative degree movement test complete")
    pause()


def test_relative_movement_steps(motor):
    """Test relative movement in steps."""
    print_test_header("Relative Movement (Steps)", "Move relative steps from current position")
    
    # Start at home
    motor.set_position_steps(0)
    print("  Starting at home (step 0)")
    print_motor_status(motor)
    time.sleep(MOVEMENT_DELAY)
    
    # Move in step increments
    movements = [10, 20, 30, -25, -15, 40, -60]
    
    for move in movements:
        direction = "CW" if move > 0 else "CCW"
        print(f"  Moving {abs(move)} steps {direction}...")
        motor.move_arm_steps(move)
        time.sleep(MOVEMENT_DELAY)
        print_motor_status(motor)
    
    print("  ✓ Relative step movement test complete")
    pause()


def test_reset_position(motor):
    """Test reset to home position."""
    print_test_header("Reset Position", "Return to home from various positions")
    
    test_positions = [90, 180, 270, 45, 315, 135]
    
    for pos in test_positions:
        print(f"  Moving to {pos}°...")
        motor.set_position_degrees(pos)
        time.sleep(MOVEMENT_DELAY)
        print_motor_status(motor)
        
        print(f"  Resetting to home...")
        motor.reset_position()
        time.sleep(MOVEMENT_DELAY)
        print_motor_status(motor)
        print()
    
    print("  ✓ Reset position test complete")
    pause()


def test_full_rotation_cw(motor):
    """Test full clockwise rotation."""
    print_test_header("Full Rotation (CW)", "Complete 360° clockwise rotation")
    
    motor.set_position_degrees(0)
    print("  Starting full CW rotation...")
    
    for angle in range(0, 361, 15):
        motor.set_position_degrees(angle % 360)
        print(f"  Position: {angle}°")
        time.sleep(0.3)
    
    print("  ✓ Full CW rotation complete")
    pause()


def test_full_rotation_ccw(motor):
    """Test full counter-clockwise rotation."""
    print_test_header("Full Rotation (CCW)", "Complete 360° counter-clockwise rotation")
    
    motor.set_position_degrees(0)
    print("  Starting full CCW rotation...")
    
    for angle in range(360, -1, -15):
        motor.set_position_degrees(angle)
        print(f"  Position: {angle}°")
        time.sleep(0.3)
    
    print("  ✓ Full CCW rotation complete")
    pause()


def test_position_wrapping(motor):
    """Test position wrapping at boundaries."""
    print_test_header("Position Wrapping", "Test behavior at 0°/360° boundary")
    
    # Test wrapping with relative movements
    motor.set_position_degrees(10)
    print("  Starting at 10°")
    print_motor_status(motor)
    time.sleep(MOVEMENT_DELAY)
    
    print("  Moving -30° (should wrap to ~340°)...")
    motor.move_arm_degrees(-30)
    time.sleep(MOVEMENT_DELAY)
    print_motor_status(motor)
    
    print("  Moving +30° (should return to ~10°)...")
    motor.move_arm_degrees(30)
    time.sleep(MOVEMENT_DELAY)
    print_motor_status(motor)
    
    print("  ✓ Position wrapping test complete")
    pause()


def test_shortest_path(motor):
    """Test that motor takes shortest path."""
    print_test_header("Shortest Path", "Verify motor uses optimal path")
    
    # Test case 1: From 10° to 350° (should go CCW ~20° instead of CW 340°)
    motor.set_position_degrees(10)
    print("  Starting at 10°")
    print_motor_status(motor)
    time.sleep(MOVEMENT_DELAY)
    
    print("  Moving to 350° (should go CCW ~20°, not CW 340°)...")
    motor.set_position_degrees(350)
    time.sleep(MOVEMENT_DELAY)
    print_motor_status(motor)
    print()
    
    # Test case 2: From 350° to 10° (should go CW ~20° instead of CCW 340°)
    print("  Moving to 10° (should go CW ~20°, not CCW 340°)...")
    motor.set_position_degrees(10)
    time.sleep(MOVEMENT_DELAY)
    print_motor_status(motor)
    
    print("  ✓ Shortest path test complete")
    pause()


def test_precision_positioning(motor):
    """Test positioning precision."""
    print_test_header("Precision Positioning", "Test accuracy of positioning")
    
    motor.set_position_degrees(0)
    print("  Testing precision at various positions...")
    print()
    
    test_angles = [0, 1.8, 3.6, 5.4, 90, 180, 270, 359.5]
    
    for target_angle in test_angles:
        motor.set_position_degrees(target_angle)
        time.sleep(MOVEMENT_DELAY)
        actual_angle = motor.current_degree
        error = abs(target_angle - actual_angle)
        print(f"  Target: {target_angle:6.1f}° → Actual: {actual_angle:6.1f}° → Error: {error:.1f}°")
    
    print()
    print("  ✓ Precision positioning test complete")
    print(f"  Note: Minimum step size is {360/motor.STEPS_PER_REVOLUTION}° per step")
    pause()


def test_continuous_back_and_forth(motor):
    """Test continuous back-and-forth motion."""
    print_test_header("Continuous Motion", "Oscillate between two positions")
    
    print("  Oscillating between 45° and 315° (5 cycles)...")
    
    motor.set_position_degrees(45)
    time.sleep(MOVEMENT_DELAY)
    
    for cycle in range(5):
        print(f"  Cycle {cycle + 1}/5")
        
        motor.set_position_degrees(315)
        time.sleep(0.8)
        print_motor_status(motor)
        
        motor.set_position_degrees(45)
        time.sleep(0.8)
        print_motor_status(motor)
    
    print("  ✓ Continuous motion test complete")
    pause()


def test_boundary_validation(motor):
    """Test input validation for boundary cases."""
    print_test_header("Boundary Validation", "Test input validation and error handling")
    
    print("  Testing invalid degree inputs...")
    
    # These should fail gracefully
    test_cases = [
        ("Negative degrees < -360", -400),
        ("Positive degrees > 360", 400),
        ("Large negative", -1000),
        ("Large positive", 1000),
    ]
    
    for name, value in test_cases:
        print(f"  {name} ({value}°): ", end="")
        motor.move_arm_degrees(value)  # Should print error and do nothing
    
    print("\n  Testing invalid step inputs...")
    test_step_cases = [
        ("Negative steps", -10),
        ("Steps > 200", 250),
    ]
    
    for name, value in test_step_cases:
        print(f"  {name} ({value}): ", end="")
        motor.move_arm_steps(value)  # Should print error and do nothing
    
    print("\n  ✓ Boundary validation test complete")
    pause()


def test_properties(motor):
    """Test motor properties."""
    print_test_header("Motor Properties", "Test property accessors")
    
    motor.set_position_degrees(90)
    time.sleep(MOVEMENT_DELAY)
    
    print(f"  current_step property: {motor.current_step}")
    print(f"  current_degree property: {motor.current_degree:.1f}°")
    print(f"  STEPS_PER_REVOLUTION: {motor.STEPS_PER_REVOLUTION}")
    print(f"  Degrees per step: {360/motor.STEPS_PER_REVOLUTION}°")
    print()
    
    print("  Testing deprecated getter methods (backward compatibility)...")
    print(f"  get_current_step(): {motor.get_current_step()}")
    print(f"  get_current_degree(): {motor.get_current_degree():.1f}°")
    
    print("  ✓ Properties test complete")
    pause()


def run_all_tests(motor):
    """Run all motor tests in sequence."""
    tests = [
        test_homing,
        test_absolute_position_degrees,
        test_absolute_position_steps,
        test_relative_movement_degrees,
        test_relative_movement_steps,
        test_reset_position,
        test_full_rotation_cw,
        test_full_rotation_ccw,
        test_position_wrapping,
        test_shortest_path,
        test_precision_positioning,
        test_continuous_back_and_forth,
        test_boundary_validation,
        test_properties,
    ]
    
    total_tests = len(tests)
    
    for i, test_func in enumerate(tests, 1):
        print(f"\n{'#' * 60}")
        print(f"Running test {i}/{total_tests}")
        print(f"{'#' * 60}")
        
        try:
            test_func(motor)
        except KeyboardInterrupt:
            print("\n\nTest interrupted by user.")
            raise
        except Exception as e:
            print(f"\nERROR in {test_func.__name__}: {e}")
            import traceback
            traceback.print_exc()
            pause(3.0)


def main():
    """Main test execution."""
    print("\n" + "#" * 60)
    print("Motor (Stepper) Comprehensive Test Suite")
    print("#" * 60)
    print(f"Pause between tests: {PAUSE_BETWEEN_TESTS}s")
    print(f"Movement delay: {MOVEMENT_DELAY}s")
    print("#" * 60)
    
    # Initialize I2C bus
    print("\nInitializing I2C bus...")
    i2c = busio.I2C(board.SCL, board.SDA)
    time.sleep(0.5)
    print("I2C bus initialized")
    
    # Initialize motor
    motor = test_initialization(i2c)
    if motor is None:
        print("\nFailed to initialize motor. Exiting.")
        return
    
    # Run all tests
    try:
        run_all_tests(motor)
        
        print("\n" + "#" * 60)
        print("All tests completed successfully!")
        print("#" * 60)
        
        # Return to home at the end
        print("\nReturning to home position...")
        motor.reset_position()
        print("Motor at home position.")
        
    except KeyboardInterrupt:
        print("\n\nTest suite interrupted by user.")
        print("Returning motor to home position...")
        try:
            motor.reset_position()
        except:
            pass
    except Exception as e:
        print(f"\n\nTest suite error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()