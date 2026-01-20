"""
Author: James Howe

A variety of basic functions for Adafruits neopixel,
Specificly this is for the 24 LED ring

A color will always be represented by a tuple of 3 values 0-255 which represent the Red, Green, and Blue component of the color
"""

import board
import neopixel

#This bit here might be better done a different way, like have the students define all thing in their code.py and just pass it into the methods 
#------------
PIN = board.D5
NUM_LEDS = 24
BRIGHTNESS = 0.1

ring = neopixel.NeoPixel(PIN, NUM_LEDS, brightness = BRIGHTNESS)
#------------

def get_ring():
    return ring

def set_brightness(b):
    ring.brightness = b
    
def __check_color_valid(color):
    """
    Just a private method for checking if a color that the user inputs is valid or not
    """

    if(len(color) < 3):
        return False, "Color tuple has less than 3 elements"
    if(len(color) > 3):
        return False, "Color tuple has more than 3 elements"
    for i in color:
        if(i > 255 or i < 0):
            return False, "A RGB value is out of bounds(0-255)"
    return True, ""


def set_pixel(color, pixel, ring = ring):
    #Make sure the color is valid
    valid_color, error_msg = __check_color_valid(color)
    if(not valid_color):
        print("ERROR while attempting to use neopixelFunctions.set_pixel:", error_msg)
        return

    ring[pixel] = color

def set_ring_color(color, ring = ring):
    """Takes in `color`, and uses neopixels built in function to set all the LEDs to that color"""
    
    #Make sure the color is valid
    valid_color, error_msg = __check_color_valid(color)
    if(not valid_color):
        print("ERROR while attempting to use neopixelFunctions.set_ring_color:", error_msg)
        return

    
    ring.fill(color)


def bar_graph(color, end_pos, fill_mode = 1, start_pos = 0, ring = ring, clear = 1):
    """
    Fills in all LEDs from start_pos(defaults to 0 inclusive) to end_pos(exclusive) with the color specified by `color`

    If `fill_mode` is False, then the behavior will change, only lighting up the LED at (end_pos-1)
    """
    
    #Error handling, makes sure the end pos is lower than the number of leds and that the start positon is greater than 0
    if(end_pos > len(ring)):
        print("ERROR: Your end position can't be more than the number of LEDS")
        return
    if(start_pos < 0):
        print("ERROR: Your start position can't be less than 0")
        return
    #Make sure the color is valid
    valid_color, error_msg = __check_color_valid(color)
    if(not valid_color):
        print("ERROR:", error_msg)
        return

    #Clear the ring before putting anything else on it
    if(clear):
    	ring.fill((0,0,0))


    #If fill_mode is true then set the values of the
    #LEDs from start_pos(inclusive) to end_pos(exclusive) with color
    if fill_mode == True:
        for i in range(start_pos, end_pos):
            ring[i] = color
    #Else just set the led at end_pos-1        
    else:
        ring[end_pos-1] = color


#Shaded bar graph (start color, stop color, position, dot/fill, dot color) -
#same as bar graph except the color transitions from a start to finish color)

def shaded_bar_graph(start_color, end_color, end_pos, start_pos = 0, ring = ring):
    """
    Shaded bar graph is the same idea as the regular bar graph except it takes in 2 colors and creates a
    gradient of the 2 colors from the start position to the end position

    """

    #Error handling, makes sure the end pos is lower than the number of leds and that the start positon is greater than 0
    if(end_pos > len(ring)):
        print("ERROR: Your end position can't be more than the number of LEDS")
        return
    if(start_pos < 0):
        print("ERROR: Your start position can't be less than 0")
        return
    #Make sure the color is valid
    valid_color, error_msg = __check_color_valid(start_color)
    if(not valid_color):
        print("ERROR: Start", error_msg)
        return
    valid_color, error_msg = __check_color_valid(end_color)
    if(not valid_color):
        print("ERROR: End", error_msg)
        return


    #Clear the ring before putting anything else on it
    ring.fill((0,0,0))

    #Gets the number of leds between end and start
    transition_length = (end_pos-start_pos)

    #Finds the slope for each RGB compenent indivdually
    slope = [
        (end_color[0] - start_color[0]) / transition_length,
        (end_color[1] - start_color[1]) / transition_length,
        (end_color[2] - start_color[2]) / transition_length
    ]
    
    #Finds the starting value for each RGB compenent indivdually
    y_offset = [
        start_color[0],
        start_color[1],
        start_color[2]
    ]

    for i in range(0,transition_length):

        #Calculate the color at the point with the slope equation y = mx + b
        #for each led from start to end
        calculated_color = (
            slope[0]*i + y_offset[0],
            slope[1]*i + y_offset[1],
            slope[2]*i + y_offset[2]
        )
        
        ring[start_pos + i] = calculated_color


#Dot on background (color, position, dot color) -
#ring is one color but a single dot is a different color; input ring color, dot position, dot color.
def dot_on_background(fill_color, dot_pos, dot_color, ring = ring):
    """
    Makes the ring one color, but the LED at dot_pos is dot_color
    
    Fills the LEDs with fill_color and then sets the led at dot_pos with dot_color
    """
    
    #Error handling, makes sure the dot's position is less than the number of leds
    if(dot_pos > len(ring)):
        print("ERROR: Your dot_pos is larger than the number of LEDS")
        return
    #Make sure the color is valid
    valid_color, error_msg = __check_color_valid(fill_color)
    if(not valid_color):
        print("ERROR: Fill", error_msg)
        return
    valid_color, error_msg = __check_color_valid(dot_color)
    if(not valid_color):
        print("ERROR: Dot", error_msg)
        return
    
    ring.fill(fill_color)
    ring[dot_pos] = dot_color


def animate_snake(color = (255,0,0), snake_length = 4, start_pos = 0, frames = 24, ring = ring):
    """
    Just a fun little method for animating a snake for an amount of frames 
    """
    #Clear the LEDS
    ring.fill((0,0,0))

    #Find the head color, which is just the inverse of the rest of the snake
    head_color = (255-color[0], 255-color[1], 255-color[2])

    #Initially fill in the snake 
    for i in range(start_pos, start_pos + snake_length):
        ring[i] = color

    #for each frame, turn off the tail of the snake, turn on the led in front of the snake and set the previous head the the body color
    for frame in range(0,frames):
        
        #turn off the tail of the snake
        ring[(start_pos + frame) % len(ring)] = (0,0,0)
        
        #turn on the led in front of the snake
        ring[(start_pos + snake_length + frame) % len(ring)] = head_color
        
        #set the previous head the the body color
        ring[(start_pos + snake_length + frame - 1) % len(ring)] = color

        #A very imprescise way to get the delay between frames that I want
        #without this it's too fast, and time.sleep() doesn't have enough fidelity 
        x = 0
        for i in range(0,10000):
            x += 1
            x -= 1


        
def maprange( original_range, range_to_map_to, s, clamp = True):
    # Did not write this got it from rosseta code
    # https://rosettacode.org/wiki/Map_range#Python
    #It takes in 3 aurguments,
    # original_range: the original range of s
    # range_to_map_to: the range you want to map s onto
    # s: the value you want to map
    # clamp: whether or not a value which exceeds the end mapping range will be clamped
    # The function maps s from its original range onto a new one
    # for eg, mapping maprange([0,10],[0,100],5) would return 50
	(a1, a2), (b1, b2) = original_range, range_to_map_to
	return_value = b1 + ((s - a1) * (b2 - b1) / (a2 - a1))
	if(return_value < b1):
            return_value = b1
        elif(return_value > b2):
            return_value = b2
	return  return_value

    

def wheel(pos):
    """
    Did not write this, unsure if you want it in the final thing

    """
    # Input a value 0 to 255 to get a color value.
    # The colours are a transition r - g - b - back to r.
    if pos < 0 or pos > 255:
        return (0, 0, 0)
    if pos < 85:
        return (255 - pos * 3, pos * 3, 0)
    if pos < 170:
        pos -= 85
        return (0, 255 - pos * 3, pos * 3)
    pos -= 170
    return (pos * 3, 0, 255 - pos * 3)


