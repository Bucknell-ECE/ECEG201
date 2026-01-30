"""
Device Initialization Test Script

This script tests the initialization of the stepper motor, NeoPixel ring,
and WiFi connectivity using the ECEGMotor, NeoPixelRing, and WifiManager classes.

After successful initialization, the device enters an idle state with a
breathing LED effect.

Author: Aiden Cherniske
Date: 2026-01-30
"""

import board
import busio
import time

from motorFunctions import ECEGMotor
from neopixelFunctions import NeoPixelRing
from wifiFunctions import WifiManager


# Configuration Constants
IDLE_COLOR = NeoPixelRing.COLOR_BLUE
IDLE_BRIGHTNESS_MIN = 0.02
IDLE_BRIGHTNESS_MAX = 0.15
IDLE_BREATH_PERIOD = 3.0 # seconds for a full breath cycle
IDLE_UPDATE_RATE = 0.03 # seconds between updates

TEST_API_URL = "https://jsonplaceholder.typicode.com/todos/1"

def initialize_motor(i2c):
    """
    Initialize the stepper motor and perform homing.
    
    Args:
        i2c: I2C bus instance
        
    Returns:
        ECEGMotor instance or None if initialization failed
    """
    print("Initializing stepper motor...")
    try:
        motor = ECEGMotor(i2c)
        print(f"Stepper motor initialized. "
              f"Current step: {motor.current_step}, "
              f"degree: {motor.current_degree:.1f}")
        
        # Perform homing sequence
        print("\nPerforming motor homing sequence...")
        motor.find_home()
        print(f"Motor homed successfully. "
              f"Current step: {motor.current_step}, "
              f"degree: {motor.current_degree:.1f}")
        
        return motor
    except Exception as e:
        print(f"Stepper motor initialization/homing failed: {e}")
        return None


def initialize_neopixel():
    """
    Initialize the NeoPixel ring.
    
    Returns:
        NeoPixelRing instance or None if initialization failed
    """
    print("Initializing NeoPixel ring...")
    try:
        ring = NeoPixelRing()
        ring.fill(NeoPixelRing.COLOR_GREEN)
        print("NeoPixel ring initialized and set to green.")
        return ring
    except Exception as e:
        print(f"NeoPixel ring initialization failed: {e}")
        return None


def initialize_wifi():
    """
    Initialize WiFi connection and test API access.
    
    Returns:
        WifiManager instance or None if initialization failed
    """
    print("Initializing WiFi...")
    try:
        wifi_manager = WifiManager(verbose=True, auto_connect=True)
        wifi_manager.print_status()
        print("WiFi initialized and status printed.")
        
        # Test API request
        test_api_request(wifi_manager)
        
        return wifi_manager
    except Exception as e:
        print(f"WiFi initialization failed: {e}")
        return None


def test_api_request(wifi_manager):
    """
    Test API request to verify internet connectivity.
    
    Args:
        wifi_manager: WifiManager instance
    """
    try:
        print(f"Testing API request to {TEST_API_URL}...")
        response = wifi_manager.get(TEST_API_URL)
        print("API request successful. Response:")
        print(response.text)
    except Exception as e:
        print(f"API request failed: {e}")


def run_idle_breathing(ring):
    """
    Run the idle breathing effect indefinitely.
    
    Uses a smooth sine wave for natural breathing motion.
    Press Ctrl+C to exit.
    
    Args:
        ring: NeoPixelRing instance
    """
    import math
    
    print("\n=== Entering Idle State ===")
    print(f"Breathing effect: {IDLE_COLOR}")
    print(f"Brightness range: {IDLE_BRIGHTNESS_MIN:.2f} - {IDLE_BRIGHTNESS_MAX:.2f}")
    print(f"Period: {IDLE_BREATH_PERIOD:.1f} seconds")
    print("Press Ctrl+C to exit\n")
    
    # Use the built-in breathing effect with infinite cycles
    try:
        steps = int(IDLE_BREATH_PERIOD / IDLE_UPDATE_RATE / 2)
        ring.breathing_effect(
            color=IDLE_COLOR,
            min_brightness=IDLE_BRIGHTNESS_MIN,
            max_brightness=IDLE_BRIGHTNESS_MAX,
            steps=steps,
            delay=IDLE_UPDATE_RATE,
            cycles=999999  # Effectively infinite
        )
    except KeyboardInterrupt:
        print("\nExiting idle state.")
        ring.clear()

def main():
    """Main initialization and test sequence."""
    print("\n" + "=" * 60)
    print("Device Initialization Test")
    print("=" * 60 + "\n")
    
    # Initialize I2C bus for motor
    print("Initializing I2C bus for stepper motor...")
    i2c = busio.I2C(board.SCL, board.SDA)
    time.sleep(0.5)
    
    # Initialize all components
    motor = initialize_motor(i2c)
    ring = initialize_neopixel()
    wifi = initialize_wifi()
    
    print("\n" + "=" * 60)
    print("Initialization Test Complete")
    print("=" * 60 + "\n")
    
    # Enter idle state if NeoPixel ring initialized successfully
    if ring is not None:
        run_idle_breathing(ring)
    else:
        print("Cannot enter idle state: NeoPixel ring not initialized")


if __name__ == "__main__":
    main()