'''
Author: Matt Lamparter
Based on previous work by James Howe
Updated 2025.11.14

A basic class which keeps track of the current location of the stepper motor and
allows one to either set it's poistion or move it

CW for clockwise and CCW for counter clockwise

This library is based on the Adafruit product 2927:
https://www.adafruit.com/product/2927
which in turn relies on the PC9685 and TB6612 devices
We use "stepper 1" on the Adafruit board on the custom DAMNED PCB

As of Fall 2024 this library is based on a NEMA 8 stepper from AliExpress with 200 steps per
revolution or 1.8° per step

The motor relies on the use of a Hall effect sensor and a magnet in a motor arm to find the home position
Sensor is located at the 3 o'clock position when viewing the PCB from the front

A ring of 24 NeoPixels can be used to indicate sensing of Hall effect edges
https://www.adafruit.com/product/1586

As of Fall 2025 this library now requires an instantiation of the ECEGMotor class to pass an I2C object
This will help if anyone is not able to use the default board.SCL and board.SDA pins.

CircuitPython motor functions references:
https://github.com/adafruit/Adafruit_CircuitPython_Motor/blob/main/adafruit_motor/stepper.py
https://github.com/adafruit/Adafruit_CircuitPython_MotorKit/blob/c6118a65b68f00256bb88168de38179e6dd20721/adafruit_motorkit.py#L51
https://github.com/adafruit/Adafruit_CircuitPython_MotorKit/blob/c6118a65b68f00256bb88168de38179e6dd20721/examples/motorkit_stepper_test.py


'''
import board
import time
from digitalio import DigitalInOut, Direction, Pull
from adafruit_motorkit import MotorKit
from adafruit_motor import stepper


class ECEGMotor:
    '''
    A basic class which keeps track of the current stepper motor position
    and allows the user to move it
    '''
    STEPS_FOR_FULL = 200 # our specific motor has 200 steps per rotation
    '''

    '''
    def __init__(self, i2c_bus):
        """
        The intilizer for the method

        """
        #self.__debug = debug
        self.__kit = MotorKit(i2c=i2c_bus)
        self.__stepper = self.__kit.stepper1
        self.__stepper.release()
        self.__current_step = 0 #the current number of steps CW from home(step 0)
        self.__Hall = DigitalInOut(board.D16) # Hall sensor hard wired to D16 (A2) of Feather
        self.__Hall.direction = Direction.INPUT # set the Hall sensor pin to be an input
        print("INITIALIZATION OF MOTOR FROM LIBRARY COMPLETE")


    def find_home(self):
        """
        A method for finding the Hall sensor on the device
        Spin CW infinitely until an edge is detected.  Assume the first edge is missed
        and we only get the second edge to be safe.  This assumption is based on the fact
        that the motor arm moves fast and the Hall sensor can be slow to respond.
        Move CCW backwards 20 steps in order to
        ensure we move beyond the first edge.  Now slowly move CW and check to see if an edge
        is detected.  Save the location of edge1, find the location of edge 2, find the middle
        and move backwards to the middle.  Then move the arm to 12 o'clock.  This is now "home".  Set the step counter to 0.
        """
        # create edge detectors for the range where the magnet triggers the Hall sensor
        edge1 = 0
        edge2 = 0
        # step counter used only for homing the motor
        stepCount = 0

        #if self.__debug:
        print("Finding the home of the stepper motor")
        # begin by rotating CW until at least one edge of the Hall magnetic field is found
        while True:
            self.__stepper.onestep(direction=stepper.BACKWARD, style=stepper.DOUBLE)
            if (self.__Hall.value == 0):
                print("Initial edge detected!")
                break
        '''
        motor has paused at the end of the Hall sensor, in theory
        move back several steps which should eliminate the magnetic field/Hall active edge.
        20 steps was chosen because after testing multiple times it was found that the
        active zone was never more than about 14 steps.  20 seemed like a safe bet in case
        the first edge was detected at the *end* of the Hall active zone
        '''
        for i in range(20):
            self.__stepper.onestep(direction=stepper.FORWARD, style=stepper.DOUBLE)

        # now step forward, SLOWLY (with pauses between each step to allow for Hall sensor
        # to responsd) and locate the two edges of the active Hall zone
        for i in range(45):
            if self.__Hall.value:
                if edge1 != 0 and edge2 == 0:
                    edge2 = stepCount - 1
                    print("Edge2 found!")
                    break
                self.__stepper.onestep(direction=stepper.BACKWARD, style=stepper.DOUBLE)
                stepCount = stepCount + 1
                time.sleep(0.5)
            else:
                if edge1 == 0:
                    edge1 = stepCount
                    print("Edge1 found!")
                self.__stepper.onestep(direction=stepper.BACKWARD, style=stepper.DOUBLE)
                stepCount = stepCount + 1
                time.sleep(0.5)
            if i == 44:
                if edge2 == 0:
                    print("Edge2 never found!")
        # define a temporary home used to locate the center of the Hall sensor
        home = edge2 - edge1
        # move the motor arm CCW back "home" steps
        # but remove four steps due to hysterisus
        for i in range(home-4):
            self.__stepper.onestep(direction=stepper.FORWARD, style=stepper.DOUBLE)
        time.sleep(0.1) # give the motor time to settle
        # move back to 12 o'clock position from the Hall sensor at the 3 o'clock position
        for i in range(ECEGMotor.STEPS_FOR_FULL / 4):
            self.__stepper.onestep(direction=stepper.FORWARD, style=stepper.DOUBLE)
        # sleep briefly just to make sure the motor arm has settled and it doesn't move from home
        time.sleep(0.5)
        # release the motor (deenergize coils) to eliminate current draw and heating
        # releasing causes the motor to move CCW a few steps so anticipate this offset and
        # move to counter it first
        #for i in range(3):
        #    self.__stepper.onestep(direction=stepper.FORWARD, style=stepper.DOUBLE)
        #self.__stepper.release()
        #if self.__debug:
        self.__current_step = 0 # reset the step counter to 0 once home is found
        print("Motor positioned at home")

    def check_and_update_step_count(self):
        '''
        A simple function to make sure that step count stays between 0 and (STEPS_FOR_FULL - 1)
        '''
        if self.__current_step < 0:
            self.__current_step = self.__current_step + ECEGMotor.STEPS_FOR_FULL
        if self.__current_step >= ECEGMotor.STEPS_FOR_FULL:
            self.__current_step = self.__current_step - ECEGMotor.STEPS_FOR_FULL

    def get_current_step(self):
        """
        A getter method that returns the current number of steps CW from home(step 0)

        Returns: int, current number of steps CW
        range of returned values is 0 to (STEPS_FOR_FULL - 1) in increments of 1
        """
        return self.__current_step

    def get_stepper(self):
        """
        A getter method for the stepper

        Returns: MotorKit.stepper1()
        """
        return self.__stepper

    def get_current_degree(self):
        """
        A method which calculates and returns the position of the arm as the number of degrees from home.  Home is definied as 0 degrees.

        Returns: float
        """
        return (float(self.__current_step) / float(ECEGMotor.STEPS_FOR_FULL)) * 360.0

    def set_position_degrees(self, pos):
        """
        Takes in the position in degrees from home (absolute) and then moves the arm to that location

        Params: The position in degrees that you want the arm to go to, could be int or float will do nothing if its not 0-360
        """

        if(pos < 0 or pos > 360):
            print("Input not between 0 and 360, the motor will not be moved")
            return

        goal_pos_in_steps = int(((pos/360) * ECEGMotor.STEPS_FOR_FULL))

        steps_to_take =  goal_pos_in_steps - self.__current_step

        for i in range(abs(steps_to_take)):

            #Move the arm CCW
            if(steps_to_take < 0):
                self.__stepper.onestep(direction = stepper.FORWARD, style = stepper.DOUBLE)
                self.__current_step -= 1
                #time.sleep(0.001)

            #Move the arm CW
            else:
                self.__stepper.onestep(direction = stepper.BACKWARD, style = stepper.DOUBLE)
                self.__current_step += 1
                #time.sleep(0.001)

    def set_position_steps(self, pos):
        """
        Takes in the position in steps from home (step 0) and then moves the arm to that location (absolute)

        Params: The position in steps that you want the arm to go to, should be int. It will do nothing if its not between 0 and STEPS_FOR_FULL
        """

        if(pos < 0 or pos > ECEGMotor.STEPS_FOR_FULL):
            print("Input not between 0 and", ECEGMotor.STEPS_FOR_FULL, "the motor will not be moved")
            return
        #convert any floats to ints
        pos = int(pos)
        steps_to_take =  pos - self.__current_step

        for i in range(abs(steps_to_take)):

            #Move the arm CCW
            if(steps_to_take < 0):
                self.__stepper.onestep(direction = stepper.FORWARD, style = stepper.DOUBLE)
                self.__current_step -= 1
                #time.sleep(0.001)

            #Move the arm CW
            else:
                self.__stepper.onestep(direction = stepper.BACKWARD, style = stepper.DOUBLE)
                self.__current_step += 1
                #time.sleep(0.001)

    def reset_position(self):
        """
        Resets the position of the arm to home moving in a CCW direction if the position is
        between 12 o'clock and 6 o'clock on the right half face, inclusive of both bositions
        Resets the position of the arm to home moving in a CW direction if the position is
        between 12 o'clock and 6 o'clock on the left half face, exclusive of both bositions
        """
        if self.__current_step <= int(ECEGMotor.STEPS_FOR_FULL/2):
            for i in range(self.__current_step):
                self.__stepper.onestep(direction = stepper.FORWARD, style = stepper.DOUBLE)
                #time.sleep(0.001)
        else:
            for i in range(ECEGMotor.STEPS_FOR_FULL - self.__current_step):
                self.__stepper.onestep(direction = stepper.BACKWARD, style = stepper.DOUBLE)
                #time.sleep(0.001)
        self.__current_step = 0


    def move_arm_steps(self, amount):
        """
        Moves the arm amount steps, if amount is negative then the arm is moved CCW and if its positive it moves CW
        This is a relative movement from the current position of the arm
        """
        amount = int(amount)
        if (abs(amount) > ECEGMotor.STEPS_FOR_FULL):
            print("Input beyond limits of max motor steps: ", ECEGMotor.STEPS_FOR_FULL,". The motor will not move.")
            return

        for i in range(abs(amount)):
            # what happens if amount == 0?
            if(amount < 0):
                self.__stepper.onestep(direction = stepper.FORWARD,style = stepper.DOUBLE)
                self.__current_step -= 1
                #time.sleep(0.001)
            else:
                self.__stepper.onestep(direction = stepper.BACKWARD, style = stepper.DOUBLE)
                self.__current_step += 1
                #time.sleep(0.001)
        self.check_and_update_step_count()

    def move_arm_degrees(self, degrees):
        """
        Moves the arm an absolute number of degrees from current position
        degrees must be between -360 and 360
        If degrees is negative then the arm is moved CCW and if its positive it moves CW
        function checks to see if requested movement would take the arm out of the absolute range (0,360)
        If requested movement would fall outside of that range then the arm stops at 0 or 360 degrees
        current_step is updated accordingly
        """

        if(abs(degrees) > 360):
            print("Input not between -360 and 360, the motor will not be moved")
            return
        # determine the number of corresponding motor steps required to move the requested degrees
        # steps need to be integer values
        requested_steps = int(((degrees/360) * ECEGMotor.STEPS_FOR_FULL))

        for i in range(abs(requested_steps)):

            if(requested_steps < 0):
                self.__stepper.onestep(direction = stepper.FORWARD, style = stepper.DOUBLE)
                self.__current_step -= 1
                #time.sleep(0.001)
            else:
                self.__stepper.onestep(direction = stepper.BACKWARD, style = stepper.DOUBLE)
                self.__current_step += 1
                #time.sleep(0.001)
        self.check_and_update_step_count()
