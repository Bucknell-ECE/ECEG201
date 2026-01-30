"""
NeoPixel Ring Comprehensive Test Suite

This script systematically tests all functions and animations available in the
NeoPixelRing class. Each test is clearly labeled and runs for a set duration
to demonstrate the effect.

Author: Aiden Cherniske
Date: 2026-01-30
"""

import time
import board

from neopixelFunctions import NeoPixelRing


# Test configuration
DISPLAY_DURATION = 3.0  # seconds to display each effect
PAUSE_BETWEEN_TESTS = 1.0  # seconds between tests


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


def test_basic_colors(ring):
    """Test basic color fills."""
    print_test_header("Basic Color Fills", "Testing primary color constants")
    
    colors = [
        ("Red", NeoPixelRing.COLOR_RED),
        ("Green", NeoPixelRing.COLOR_GREEN),
        ("Blue", NeoPixelRing.COLOR_BLUE),
        ("White", NeoPixelRing.COLOR_WHITE),
        ("Off/Black", NeoPixelRing.COLOR_OFF),
    ]
    
    for name, color in colors:
        print(f"  - {name}: {color}")
        ring.fill(color)
        pause(DISPLAY_DURATION)


def test_custom_colors(ring):
    """Test custom color tuples."""
    print_test_header("Custom Colors", "Testing various RGB combinations")
    
    colors = [
        ("Yellow", (255, 255, 0)),
        ("Cyan", (0, 255, 255)),
        ("Magenta", (255, 0, 255)),
        ("Orange", (255, 128, 0)),
        ("Purple", (128, 0, 255)),
        ("Pink", (255, 64, 128)),
    ]
    
    for name, color in colors:
        print(f"  - {name}: {color}")
        ring.fill(color)
        pause(DISPLAY_DURATION)


def test_brightness_levels(ring):
    """Test different brightness levels."""
    print_test_header("Brightness Levels", "Testing brightness control")
    
    ring.fill(NeoPixelRing.COLOR_WHITE)
    
    brightness_levels = [1.0, 0.75, 0.5, 0.25, 0.1, 0.05, 0.01]
    
    for brightness in brightness_levels:
        print(f"  - Brightness: {brightness:.2f}")
        ring.brightness = brightness
        pause(DISPLAY_DURATION)
    
    # Reset to default
    ring.brightness = NeoPixelRing.DEFAULT_BRIGHTNESS


def test_individual_leds(ring):
    """Test setting individual LED colors."""
    print_test_header("Individual LED Control", "Setting each LED separately")
    
    ring.clear()
    
    # Light up LEDs one by one in different colors
    colors = [
        NeoPixelRing.COLOR_RED,
        NeoPixelRing.COLOR_GREEN,
        NeoPixelRing.COLOR_BLUE,
    ]
    
    print(f"  - Lighting {ring.num_leds} LEDs individually...")
    for i in range(ring.num_leds):
        color = colors[i % len(colors)]
        ring.set_index(i, color)
        time.sleep(0.1)
    
    pause(DISPLAY_DURATION)
    
    # Clear one by one
    print("  - Clearing LEDs one by one...")
    for i in range(ring.num_leds):
        ring.set_index(i, NeoPixelRing.COLOR_OFF)
        time.sleep(0.1)


def test_clear_function(ring):
    """Test the clear function."""
    print_test_header("Clear Function", "Testing ring.clear()")
    
    ring.fill(NeoPixelRing.COLOR_RED)
    print("  - Ring filled with red")
    pause(DISPLAY_DURATION)
    
    ring.clear()
    print("  - Ring cleared")
    pause(DISPLAY_DURATION)


def test_bar_graph(ring):
    """Test bar graph function."""
    print_test_header("Bar Graph", "Progressive bar graph with fill mode")
    
    color = (0, 255, 128)
    
    # Fill mode: growing bar
    print("  - Growing bar (fill mode)...")
    for end_pos in range(1, ring.num_leds + 1):
        ring.bar_graph(color, end_pos, start_pos=0, fill_mode=True, clear=True)
        time.sleep(0.08)
    
    pause(DISPLAY_DURATION)
    
    # Non-fill mode: single LED moving
    print("  - Moving single LED (non-fill mode)...")
    for end_pos in range(1, ring.num_leds + 1):
        ring.bar_graph(color, end_pos, start_pos=0, fill_mode=False, clear=True)
        time.sleep(0.08)
    
    pause(DISPLAY_DURATION)


def test_gradient_bar(ring):
    """Test gradient bar graph."""
    print_test_header("Gradient Bar", "Color gradients across the ring")
    
    gradients = [
        ("Red to Green", NeoPixelRing.COLOR_RED, NeoPixelRing.COLOR_GREEN),
        ("Green to Blue", NeoPixelRing.COLOR_GREEN, NeoPixelRing.COLOR_BLUE),
        ("Blue to Red", NeoPixelRing.COLOR_BLUE, NeoPixelRing.COLOR_RED),
        ("Black to White", NeoPixelRing.COLOR_OFF, NeoPixelRing.COLOR_WHITE),
    ]
    
    for name, start_color, end_color in gradients:
        print(f"  - {name}")
        ring.gradient_bar(start_color, end_color, ring.num_leds, start_pos=0)
        pause(DISPLAY_DURATION)


def test_dot_on_background(ring):
    """Test dot on background function."""
    print_test_header("Dot on Background", "Single dot moving on colored background")
    
    background = (0, 0, 64)  # Dark blue
    dot_color = (255, 255, 0)  # Yellow
    
    print("  - Yellow dot on blue background...")
    for position in range(ring.num_leds):
        ring.dot_on_background(background, dot_color, position)
        time.sleep(0.1)
    
    pause(DISPLAY_DURATION)


def test_rotating_gradient(ring):
    """Test rotating gradient animation."""
    print_test_header("Rotating Gradient", "Gradient rotating around the ring")
    
    start_color = (255, 0, 0)  # Red
    end_color = (0, 0, 255)    # Blue
    
    print("  - Red to blue gradient rotating...")
    ring.rotating_gradient(start_color, end_color, duration=5.0, speed=0.03)


def test_snake_animation(ring):
    """Test snake animation."""
    print_test_header("Snake Animation", "Snake chasing its tail")
    
    colors = [
        ("Red snake", (255, 0, 0)),
        ("Green snake", (0, 255, 0)),
        ("Purple snake", (128, 0, 255)),
    ]
    
    for name, color in colors:
        print(f"  - {name}")
        ring.animate_snake(color=color, snake_length=6, start_pos=0, frames=ring.num_leds * 2)
        pause(1.0)


def test_theater_chase(ring):
    """Test theater chase animation."""
    print_test_header("Theater Chase", "Marquee-style chase effect")
    
    colors = [
        ("Red chase", (255, 0, 0)),
        ("Blue chase", (0, 0, 255)),
        ("White chase", (255, 255, 255)),
    ]
    
    for name, color in colors:
        print(f"  - {name}")
        ring.theater_chase(color, wait=0.1, iterations=10)
        pause(1.0)


def test_color_wheel(ring):
    """Test the color wheel utility."""
    print_test_header("Color Wheel", "Displaying color wheel positions")
    
    print("  - Stepping through color wheel...")
    for pos in range(0, 256, 16):
        color = NeoPixelRing.color_wheel(pos)
        print(f"    Position {pos}: {color}")
        ring.fill(color)
        time.sleep(0.2)
    
    pause(DISPLAY_DURATION)


def test_rainbow_cycle(ring):
    """Test rainbow cycle animation."""
    print_test_header("Rainbow Cycle", "Full spectrum rainbow animation")
    
    print("  - Rainbow cycling (3 iterations)...")
    ring.rainbow_cycle(wait=0.01, iterations=3)
    
    pause(DISPLAY_DURATION)


def test_breathing_effect(ring):
    """Test breathing effect."""
    print_test_header("Breathing Effect", "Pulsing brightness effect")
    
    colors = [
        ("Blue breathing", NeoPixelRing.COLOR_BLUE),
        ("Green breathing", NeoPixelRing.COLOR_GREEN),
        ("Purple breathing", (128, 0, 255)),
    ]
    
    for name, color in colors:
        print(f"  - {name}")
        ring.breathing_effect(
            color=color,
            min_brightness=0.05,
            max_brightness=0.5,
            steps=30,
            delay=0.03,
            cycles=2
        )
        pause(1.0)


def test_map_range(ring):
    """Test the map_range utility function."""
    print_test_header("Map Range Utility", "Mapping values between ranges")
    
    print("  - Mapping 0-100 to 0-24 LEDs...")
    
    ring.clear()
    
    # Map percentage to LED count
    for value in range(0, 101, 5):
        led_count = NeoPixelRing.map_range(
            value,
            from_range=(0, 100),
            to_range=(0, ring.num_leds),
            clamp=True
        )
        led_count = int(led_count)
        print(f"    {value}% -> {led_count} LEDs")
        ring.bar_graph((0, 255, 128), led_count, fill_mode=True)
        time.sleep(0.2)
    
    pause(DISPLAY_DURATION)


def test_inverted_breathing(ring):
    """Test inverted breathing effect."""
    print_test_header("Inverted Breathing", "Breathing effect starting bright")
    
    print("  - Inverted red breathing...")
    ring.breathing_effect(
        color=NeoPixelRing.COLOR_RED,
        min_brightness=0.05,
        max_brightness=0.5,
        steps=30,
        delay=0.03,
        cycles=3,
        invert=True
    )
    
    pause(DISPLAY_DURATION)


def test_multi_gradient_segments(ring):
    """Test multiple gradient segments."""
    print_test_header("Multi-Gradient Segments", "Multiple gradients in one ring")
    
    print("  - Creating 4 gradient segments...")
    
    segment_size = ring.num_leds // 4
    
    ring.clear()
    
    # Segment 1: Red to Green
    ring.gradient_bar(
        NeoPixelRing.COLOR_RED,
        NeoPixelRing.COLOR_GREEN,
        segment_size,
        start_pos=0,
        clear=False
    )
    
    # Segment 2: Green to Blue
    ring.gradient_bar(
        NeoPixelRing.COLOR_GREEN,
        NeoPixelRing.COLOR_BLUE,
        segment_size * 2,
        start_pos=segment_size,
        clear=False
    )
    
    # Segment 3: Blue to White
    ring.gradient_bar(
        NeoPixelRing.COLOR_BLUE,
        NeoPixelRing.COLOR_WHITE,
        segment_size * 3,
        start_pos=segment_size * 2,
        clear=False
    )
    
    # Segment 4: White to Red
    ring.gradient_bar(
        NeoPixelRing.COLOR_WHITE,
        NeoPixelRing.COLOR_RED,
        segment_size * 4,
        start_pos=segment_size * 3,
        clear=False
    )
    
    pause(DISPLAY_DURATION)


def run_all_tests(ring):
    """Run all NeoPixel tests in sequence."""
    tests = [
        test_basic_colors,
        test_custom_colors,
        test_brightness_levels,
        test_individual_leds,
        test_clear_function,
        test_bar_graph,
        test_gradient_bar,
        test_dot_on_background,
        test_rotating_gradient,
        test_snake_animation,
        test_theater_chase,
        test_color_wheel,
        test_rainbow_cycle,
        test_breathing_effect,
        test_inverted_breathing,
        test_map_range,
        test_multi_gradient_segments,
    ]
    
    total_tests = len(tests)
    
    for i, test_func in enumerate(tests, 1):
        print(f"\n{'#' * 60}")
        print(f"Running test {i}/{total_tests}")
        print(f"{'#' * 60}")
        
        try:
            test_func(ring)
        except KeyboardInterrupt:
            print("\n\nTest interrupted by user.")
            ring.clear()
            raise
        except Exception as e:
            print(f"\nERROR in {test_func.__name__}: {e}")
            ring.clear()
            pause(2.0)


def main():
    """Main test execution."""
    print("\n" + "#" * 60)
    print("NeoPixel Ring Comprehensive Test Suite")
    print("#" * 60)
    print(f"Display duration: {DISPLAY_DURATION}s per effect")
    print(f"Pause between tests: {PAUSE_BETWEEN_TESTS}s")
    print("#" * 60)
    
    # Initialize NeoPixel ring
    try:
        ring = NeoPixelRing()
        print(f"\nNeoPixel ring initialized:")
        print(f"  - LEDs: {ring.num_leds}")
        print(f"  - Default brightness: {ring.brightness}")
        print(f"  - Pin: D5")
    except Exception as e:
        print(f"\nFailed to initialize NeoPixel ring: {e}")
        return
    
    # Run all tests
    try:
        run_all_tests(ring)
        
        print("\n" + "#" * 60)
        print("All tests completed successfully!")
        print("#" * 60)
        
    except KeyboardInterrupt:
        print("\n\nTest suite interrupted by user.")
    finally:
        # Clean up
        print("\nCleaning up...")
        ring.clear()
        print("NeoPixel ring cleared and test complete.")


if __name__ == "__main__":
    main()