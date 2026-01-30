"""
Author: James Howe
Refactored by Aiden Cherniske 2026.01.28

NeoPixel control functions for Adafruit 24-LED ring.

Provides convenient functions for controlling NeoPixel LEDs including
solid colors, gradients, animations, and utility functions.

Hardware:
- 24-LED NeoPixel ring (Adafruit product 1586)
- Default pin: D5
- Colors represented as (R, G, B) tuples with values 0-255
"""

import board
import neopixel
import time
import math

class NeoPixelRing:
    """
    Controller for a NeoPixel LED ring.

    Provides high-level functions for setting colors, creating gradients,
    and running animations on a circular array of NeoPixels.
    """

    # Default configuration
    DEFAULT_PIN = board.D5
    DEFAULT_LED_COUNT = 24
    DEFAULT_BRIGHTNESS = 0.1

    # Color constants
    COLOR_OFF = (0, 0, 0)
    COLOR_RED = (255, 0, 0)
    COLOR_GREEN = (0, 255, 0)
    COLOR_BLUE = (0, 0, 255)
    COLOR_WHITE = (255, 255, 255)

    def __init__(self, pin=None, num_leds=None, brightness=None):
        """
        Initialize the NeoPixel ring.

        Args:
            pin: GPIO pin (default: D5)
            num_leds: Number of LEDs in the ring (default: 24)
            brightness: Brightness level (0.0 to 1.0, default: 0.1)
        """
        pin = pin or self.DEFAULT_PIN
        num_leds = num_leds or self.DEFAULT_LED_COUNT
        brightness = brightness or self.DEFAULT_BRIGHTNESS

        self._ring = neopixel.NeoPixel(
            pin,
            num_leds,
            brightness=brightness)
        self._num_leds = num_leds

    @property
    def ring(self):
        """Access the underlying NeoPixel object."""
        return self._ring

    @property
    def brightness(self):
        """Current brightness level (0.0 to 1.0)."""
        return self._ring.brightness

    @brightness.setter
    def brightness(self, value):
        """Set brightness level (0.0 to 1.0)."""
        if not (0.0 <= value <= 1.0):
            raise ValueError("Brightness must be between 0.0 and 1.0")
        self._ring.brightness = value

    @property
    def num_leds(self):
        """Number of LEDs in the ring."""
        return self._num_leds

    @staticmethod
    def _validate_color(color):
        """
        Validate that a color tuple is properly formatted.
        
        Args:
            color: Tuple of (R, G, B) values
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if not isinstance(color, (tuple, list)) or len(color) != 3: # ex. (255, 0, 0) or [255, 0, 0]
            return (False, "Color must be a tuple or list of three integers.")

        for i, component in enumerate(color):
            if not isinstance(component, (int, float)):
                return (False, f"Color component {i} is not a number.")
            if not 0 <= component <= 255:
                return (False, f"Color component {i} ({component}) is out of range (0-255).")
        return (True, "")

    def _require_valid_color(self, color, context=""):
        """
        Validate color and raise exception if invalid.
        
        Args:
            color: Color tuple to validate
            context: Context string for error message
            
        Raises:
            ValueError: If color is invalid
        """
        is_valid, error_msg = self._validate_color(color)
        if not is_valid:
            raise ValueError(f"{context}: {error_msg}" if context else error_msg)

    def _validate_index(self, index):
        """Validate that a position is within valid range."""
        if not 0 <= index < self._num_leds:
            raise ValueError(f"Position {index} out of range (0-{self._num_leds - 1})")

    def clear(self):
        """Turn off all LEDs in the ring."""
        self._ring.fill(self.COLOR_OFF)

    def fill(self, color):
        """
        Fill the entire ring with a solid color.
        
        Args:
            color: Color tuple (R, G, B)
        """
        self._require_valid_color(color, "fill")
        self._ring.fill(color)

    def set_index(self, index, color):
        """
        Set a single LED to a specific color.
        
        Args:
            index: LED index (0 to num_leds - 1)
            color: Color tuple (R, G, B)
        """
        self._validate_index(index)
        self._require_valid_color(color, "set_index")
        self._ring[index] = color


    # Additional methods for gradients and animations can be added here

    def bar_graph(self, color, end_pos, start_pos=0, fill_mode=True, clear=True):
        """
        Display a bar graph from start_pos to end_pos.
        
        Args:
            color: Color tuple (R, G, B)
            end_pos: End position of the bar graph (exclusive)
            start_pos: Start position of the bar graph (inclusive, default: 0)
            fill_mode: If True, fill the bar; if False, only light end LED (default: True)
            clear: If True, clear ring before drawing (default: True)
        """

        self._validate_index(start_pos)
        if not 0 <= end_pos <= self._num_leds:
            raise ValueError(f"end_pos {end_pos} out of range (0-{self._num_leds})")
        self._require_valid_color(color, "bar_graph")

        if clear:
            self.clear()

        if fill_mode:
            for i in range(start_pos, end_pos):
                self._ring[i] = color
        else:
            if end_pos > start_pos:
                self._ring[end_pos - 1] = color

    def gradient_bar(self, start_color, end_color, end_pos, start_pos=0, clear=True):
        """
        Display a gradient bar from start to end position.

        The color smoothly transitions from start_color to end_color.
        
        Args:
            start_color: Starting color tuple (R, G, B)
            end_color: Ending color tuple (R, G, B)
            end_pos: End position of the gradient bar (exclusive)
            start_pos: Start position of the gradient bar (inclusive, default: 0)
            clear: If True, clear ring before drawing (default: True)
        """

        self._validate_index(start_pos)
        if not 0 <= end_pos <= self._num_leds:
            raise ValueError(f"end_pos {end_pos} out of range (0-{self._num_leds})")
        self._require_valid_color(start_color, "gradient_bar start_color")
        self._require_valid_color(end_color, "gradient_bar end_color")

        if clear:
            self.clear()

        length = end_pos - start_pos
        if length <= 0:
            return

        # Calculate RGB slopes for linear interpolation
        slopes = [
            (end_color[i] - start_color[i]) / length for i in range(3)
        ]

        # Set each LED color based on position
        for i in range(length):
            color = tuple(
                int(start_color[j] + slopes[j] * i) for j in range(3)
            )
            self._ring[start_pos + i] = color

    def dot_on_background(self, background_color, dot_color, dot_position):
        """
        Display a single dot on a background color.
        
        Args:
            background_color: Background color tuple (R, G, B)
            dot_color: Dot color tuple (R, G, B)
            dot_position: Position of the dot (0 to num_leds - 1)
        """

        self._validate_index(dot_position)
        self._require_valid_color(background_color, "dot_on_background background_color")
        self._require_valid_color(dot_color, "dot_on_background dot_color")

        self._ring.fill(background_color)
        self._ring[dot_position] = dot_color

    def rotating_gradient(self, start_color, end_color, duration=5.0, speed=0.03):
        """
        Animate a rotating gradient around the ring.
        
        Args:
            start_color: Starting color tuple (R, G, B)
            end_color: Ending color tuple (R, G, B)
            duration: Total duration of animation in seconds (default: 5.0)
            speed: Delay between frames in seconds (default: 0.03)
        """
        self._require_valid_color(start_color, "rotating_gradient start_color")
        self._require_valid_color(end_color, "rotating_gradient end_color")
        
        frames = int(duration / speed)
        
        for frame in range(frames):
            offset = frame % self._num_leds
            for i in range(self._num_leds):
                position = (i + offset) % self._num_leds
                ratio = position / self._num_leds
                
                color = tuple(
                    int(start_color[j] + (end_color[j] - start_color[j]) * ratio)
                    for j in range(3)
                )
                self._ring[i] = color
            
            time.sleep(speed)

    def animate_snake(self, color=None, snake_length=4, start_pos=0, frames=24, delay=0.05):
        """
        Animate a snake moving around the ring.
        
        The snake has a colored head (inverse of body color) and moves clockwise.
        
        Args:
            color: (R, G, B) tuple for snake body (default: red)
            snake_length: Length of snake in LEDs (default: 4)
            start_pos: Starting position (default: 0)
            frames: Number of frames to animate (default: 24)
            delay: Delay between frames in seconds (default: 0.05)
        """
        color = color or self.COLOR_RED
        self._require_valid_color(color, "animate_snake color")

        if snake_length < 1 or snake_length >= self._num_leds:
            raise ValueError(f"snake_length {snake_length} out of range (1-{self._num_leds - 1})")

        self.clear()

        # Head color is inverse of body color
        head_color = tuple(255 - c for c in color)

        # Draw initial snake
        for i in range(snake_length):
            pos = (start_pos + i) % self._num_leds
            self._ring[pos] = color

        # Animate the snake movement
        for frame in range(frames):
            # Clear tail
            tail_pos = (start_pos + frame) % self._num_leds
            self._ring[tail_pos] = self.COLOR_OFF

            # Add new head
            head_pos = (start_pos + frame + snake_length) % self._num_leds
            self._ring[head_pos] = head_color

            # Convert previous head to body color
            prev_head_pos = (start_pos + frame + snake_length - 1) % self._num_leds
            self._ring[prev_head_pos] = color

            if delay > 0:
                time.sleep(delay)

    def theater_chase(self, color, wait=0.1, iterations=10):
        """
        Theater marquee-style chasing lights animation.
        
        Args:
            color: Color tuple (R, G, B)
            wait: Delay between frames in seconds (default: 0.1)
            iterations: Number of complete cycles (default: 10)
        """
        self._require_valid_color(color, "theater_chase color")
        
        for _ in range(iterations):
            for offset in range(3):
                self.clear()
                for i in range(offset, self._num_leds, 3):
                    self._ring[i] = color
                time.sleep(wait)

    @staticmethod
    def map_range(value, from_range, to_range, clamp=True):
        """
        Map a value from one range to another.

        ex. 
            map_range(5, (0, 10), (0, 100)) -> 50.0
            map_range(15, (0, 10), (0, 100), clamp=True) -> 100.0
        
        Args:
            value: Input value to map
            from_range: Tuple (min, max) of input range
            to_range: Tuple (min, max) of output range
            clamp: If True, clamp output to to_range (default: True)
        Returns:
            float: Mapped value
        """
        from_min, from_max = from_range
        to_min, to_max = to_range

        # Linear interpolation
        result = to_min + ((value - from_min) * (to_max - to_min) / (from_max - from_min))

        if clamp:
            result = max(to_min, min(to_max, result))

        return result

    @staticmethod
    def color_wheel(position):
        """
        Generate a color from a position on the color wheel.
        
        Creates a smooth transition: Red -> Green -> Blue -> Red
        
        Args:
            position: Position on wheel (0-255)
            
        Returns:
            tuple: (R, G, B) color tuple
        """
        if not 0 <= position <= 255:
            raise ValueError("position must be in range 0-255")

        if position < 85:
            # Red to Green
            return (255 - position * 3, position * 3, 0)
        elif position < 170:
            # Green to Blue
            position -= 85
            return (0, 255 - position * 3, position * 3)
        else:
            # Blue to Red
            position -= 170
            return (position * 3, 0, 255 - position * 3)

    def rainbow_cycle(self, wait=0.02, iterations=1):
        """
        Cycle through rainbow colors across all LEDs.
        
        Args:
            wait: Delay between updates (seconds)
            iterations: Number of complete cycles
        """
        for _ in range(iterations):
            for j in range(256):
                for i in range(self._num_leds):
                    pixel_index = (i * 256 // self._num_leds) + j
                    self._ring[i] = self.color_wheel(pixel_index & 255)
                time.sleep(wait)

    def breathing_effect(self, color, min_brightness=0.0, max_brightness=1, 
                         steps = 50, delay=0.02, cycles=1, invert=False):
        """
        Create a breathing (pulsing) effect with a given color.

        The effect modulates brightness from min_brightness to max_brightness.

        Args:
            color: Base color tuple (R, G, B)
            min_brightness: Minimum brightness (0.0 to 1.0)
            max_brightness: Maximum brightness (0.0 to 1.0)
            steps: Number of steps in one breath cycle
            delay: Delay between steps (seconds)
            cycles: Number of complete breath cycles (default: 1)
            invert: If True, reverse the breathing direction (default: False)
        """
        self._require_valid_color(color, "breathing_effect color")

        if not (0.0 <= min_brightness < max_brightness <= 1.0):
            raise ValueError("Brightness values must be in range 0.0 to 1.0 and min < max")
        if steps < 2:
            raise ValueError("steps must be at least 2")

        # Store original brightness to restore later
        original_brightness = self._ring.brightness

        # Set the color once
        self.fill(color)

        # Calculate brightness step size
        brightness_range = max_brightness - min_brightness
        step_size = brightness_range / steps

        for _ in range(cycles):
            # Inhale
            for step in range(steps):
                if invert:
                    brightness = max_brightness - step * step_size
                else:
                    brightness = min_brightness + step * step_size
                self._ring.brightness = brightness
                time.sleep(delay)

            # Exhale
            for step in range(steps):
                if invert:
                    brightness = min_brightness + step * step_size
                else:
                    brightness = max_brightness - step * step_size
                self._ring.brightness = brightness
                time.sleep(delay)

        # Restore original brightness
        self._ring.brightness = original_brightness

# Backward compatibility: create a global instance 

_global_ring = None

def _get_global_ring():
    """Get or create the global NeoPixel ring instance."""
    global _global_ring
    if _global_ring is None:
        _global_ring = NeoPixelRing()
    return _global_ring

def get_ring():
    """Get the global NeoPixel ring object. Deprecated: Use NeoPixelRing class instead."""
    return _get_global_ring().ring

# Backwards compatibility functions
def set_brightness(brightness):
    """Set global ring brightness. Deprecated: Use NeoPixelRing class instead."""
    _get_global_ring().brightness = brightness


def set_pixel(color, pixel, ring=None):
    """Set a pixel color. Deprecated: Use NeoPixelRing class instead."""
    if ring is None:
        _get_global_ring().set_index(pixel, color)
    else:
        # Direct ring access for backwards compatibility
        is_valid, error = NeoPixelRing._validate_color(color)
        if not is_valid:
            print(f"ERROR while attempting to use set_pixel: {error}")
            return
        ring[pixel] = color


def set_ring_color(color, ring=None):
    """Set all LEDs to one color. Deprecated: Use NeoPixelRing class instead."""
    if ring is None:
        _get_global_ring().fill(color)
    else:
        is_valid, error = NeoPixelRing._validate_color(color)
        if not is_valid:
            print(f"ERROR while attempting to use set_ring_color: {error}")
            return
        ring.fill(color)


def bar_graph(color, end_pos, fill_mode=1, start_pos=0, ring=None, clear=1):
    """Create bar graph. Deprecated: Use NeoPixelRing class instead."""
    if ring is None:
        _get_global_ring().bar_graph(color, end_pos, start_pos, bool(fill_mode), bool(clear))
    else:
        # Direct implementation for backwards compatibility
        if end_pos > len(ring):
            print("ERROR: Your end position can't be more than the number of LEDS")
            return
        if start_pos < 0:
            print("ERROR: Your start position can't be less than 0")
            return
        is_valid, error = NeoPixelRing._validate_color(color)
        if not is_valid:
            print(f"ERROR: {error}")
            return
        
        if clear:
            ring.fill((0, 0, 0))
        
        if fill_mode:
            for i in range(start_pos, end_pos):
                ring[i] = color
        else:
            ring[end_pos - 1] = color


def shaded_bar_graph(start_color, end_color, end_pos, start_pos=0, ring=None):
    """Create gradient bar. Deprecated: Use NeoPixelRing.gradient_bar instead."""
    if ring is None:
        _get_global_ring().gradient_bar(start_color, end_color, end_pos, start_pos)
    else:
        # Direct implementation for backwards compatibility
        if end_pos > len(ring):
            print("ERROR: Your end position can't be more than the number of LEDS")
            return
        if start_pos < 0:
            print("ERROR: Your start position can't be less than 0")
            return
        
        ring.fill((0, 0, 0))
        
        transition_length = end_pos - start_pos
        slopes = [
            (end_color[i] - start_color[i]) / transition_length
            for i in range(3)
        ]
        
        for i in range(transition_length):
            color = tuple(
                slopes[j] * i + start_color[j]
                for j in range(3)
            )
            ring[start_pos + i] = color


def dot_on_background(fill_color, dot_pos, dot_color, ring=None):
    """Dot on background. Deprecated: Use NeoPixelRing class instead."""
    if ring is None:
        _get_global_ring().dot_on_background(fill_color, dot_color, dot_pos)
    else:
        if dot_pos >= len(ring):
            print("ERROR: Your dot_pos is larger than the number of LEDS")
            return
        ring.fill(fill_color)
        ring[dot_pos] = dot_color


def animate_snake(color=(255, 0, 0), snake_length=4, start_pos=0, frames=24, ring=None):
    """Animate snake. Deprecated: Use NeoPixelRing class instead."""
    if ring is None:
        _get_global_ring().animate_snake(color, snake_length, start_pos, frames)
    else:
        # Direct implementation for backwards compatibility
        ring.fill((0, 0, 0))
        head_color = (255 - color[0], 255 - color[1], 255 - color[2])
        
        for i in range(start_pos, start_pos + snake_length):
            ring[i % len(ring)] = color
        
        for frame in range(frames):
            ring[(start_pos + frame) % len(ring)] = (0, 0, 0)
            ring[(start_pos + snake_length + frame) % len(ring)] = head_color
            ring[(start_pos + snake_length + frame - 1) % len(ring)] = color
            
            # Delay
            x = 0
            for i in range(10000):
                x += 1
                x -= 1


def maprange(original_range, range_to_map_to, s, clamp=True):
    """Map range. Deprecated: Use NeoPixelRing.map_range instead."""
    return NeoPixelRing.map_range(s, original_range, range_to_map_to, clamp)


def wheel(pos):
    """Color wheel. Deprecated: Use NeoPixelRing.color_wheel instead."""
    return NeoPixelRing.color_wheel(pos)