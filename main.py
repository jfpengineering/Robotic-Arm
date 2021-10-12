# ////////////////////////////////////////////////////////////////
# //                     IMPORT STATEMENTS                      //
# ////////////////////////////////////////////////////////////////

import math
import sys
import time
from threading import Thread

from kivy.app import App
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.properties import ObjectProperty
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import *
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.slider import Slider
from kivy.uix.image import Image
from kivy.uix.behaviors import ButtonBehavior
from kivy.clock import Clock
from kivy.animation import Animation
from functools import partial
from kivy.config import Config
from kivy.core.window import Window
from pidev.kivy import DPEAButton
from pidev.kivy import PauseScreen
from time import sleep
import RPi.GPIO as GPIO 
from pidev.stepper import stepper
from pidev.Cyprus_Commands import Cyprus_Commands_RPi as cyprus


# ////////////////////////////////////////////////////////////////
# //                      GLOBAL VARIABLES                      //
# //                         CONSTANTS                          //
# ////////////////////////////////////////////////////////////////
START = True
STOP = False
UP = False
DOWN = True
ON = True
OFF = False
YELLOW = .180, 0.188, 0.980, 1
BLUE = 0.917, 0.796, 0.380, 1
CLOCKWISE = 0
COUNTERCLOCKWISE = 1
ARM_SLEEP = 2.5
DEBOUNCE = 0.10

lowerTowerPosition = 60
upperTowerPosition = 76


# ////////////////////////////////////////////////////////////////
# //            DECLARE APP CLASS AND SCREENMANAGER             //
# //                     LOAD KIVY FILE                         //
# ////////////////////////////////////////////////////////////////
class MyApp(App):

    def build(self):
        self.title = "Robotic Arm"
        return sm

Builder.load_file('main.kv')
Window.clearcolor = (.1, .1,.1, 1) # (WHITE)

cyprus.open_spi()

# ////////////////////////////////////////////////////////////////
# //                    SLUSH/HARDWARE SETUP                    //
# ////////////////////////////////////////////////////////////////

sm = ScreenManager()
s0 = stepper(port=0, micro_steps=32, hold_current=20, run_current=20, accel_current=20, deaccel_current=20, steps_per_unit=200, speed=1)

# ////////////////////////////////////////////////////////////////
# //                       MAIN FUNCTIONS                       //
# //             SHOULD INTERACT DIRECTLY WITH HARDWARE         //
# ////////////////////////////////////////////////////////////////
	
class MainScreen(Screen):
    version = cyprus.read_firmware_version()
    armPosition = 0
    lastClick = time.clock()
    magnet = False
    is_arm = False
    moveArm = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        self.initialize()

    def debounce(self):
        processInput = False
        currentTime = time.clock()
        if ((currentTime - self.lastClick) > DEBOUNCE):
            processInput = True
        self.lastClick = currentTime
        return processInput

    def toggleArm(self):
        if self.is_arm == False:
            cyprus.set_pwm_values(2, period_value=100000, compare_value=100000, compare_mode=cyprus.LESS_THAN_OR_EQUAL)
            self.is_arm = True
        else:
            cyprus.set_pwm_values(2, period_value=100000, compare_value=0, compare_mode=cyprus.LESS_THAN_OR_EQUAL)
            self.is_arm = False

    def toggleMagnet(self):
        if self.magnet == False:
            cyprus.set_servo_position(1, 1)
            self.magnet = True
        else:
            cyprus.set_servo_position(1, .5)
            self.magnet = False
        
    def auto(self):
        cyprus.set_servo_position(1, 1)
        cyprus.set_pwm_values(2, period_value=100000, compare_value=100000, compare_mode=cyprus.LESS_THAN_OR_EQUAL)
        sleep(1)
        cyprus.set_pwm_values(2, period_value=100000, compare_value=0, compare_mode=cyprus.LESS_THAN_OR_EQUAL)
        sleep(.5)
        s0.go_to_position_threaded(0.34)
        while s0.is_busy():
            sleep(.1)
        cyprus.set_pwm_values(2, period_value=100000, compare_value=100000, compare_mode=cyprus.LESS_THAN_OR_EQUAL)
        sleep(.1)
        while not self.isBallOnTallTower():
            cyprus.set_pwm_values(2, period_value=100000, compare_value=0, compare_mode=cyprus.LESS_THAN_OR_EQUAL)
            sleep(.5)
            cyprus.set_pwm_values(2, period_value=100000, compare_value=100000, compare_mode=cyprus.LESS_THAN_OR_EQUAL)
            sleep(.5)
        cyprus.set_servo_position(1, .5)
        sleep(.1)
        cyprus.set_pwm_values(2, period_value=100000, compare_value=0, compare_mode=cyprus.LESS_THAN_OR_EQUAL)
        sleep(.2)
        s0.go_to_position_threaded(0)
        sleep(3)
        s0.go_to_position_threaded(.34)
        while s0.is_busy():
            sleep(.1)
        cyprus.set_servo_position(1, 1)
        sleep(.1)
        cyprus.set_pwm_values(2, period_value=100000, compare_value=100000, compare_mode=cyprus.LESS_THAN_OR_EQUAL)
        sleep(.25)
        cyprus.set_pwm_values(2, period_value=100000, compare_value=0, compare_mode=cyprus.LESS_THAN_OR_EQUAL)
        sleep(.1)
        s0.go_to_position_threaded(0)
        while s0.is_busy():
            sleep(.1)
        while not self.isBallOnShortTower():
            cyprus.set_pwm_values(2, period_value=100000, compare_value=0, compare_mode=cyprus.LESS_THAN_OR_EQUAL)
            sleep(.8)
            cyprus.set_pwm_values(2, period_value=100000, compare_value=100000, compare_mode=cyprus.LESS_THAN_OR_EQUAL)
            sleep(.8)
        cyprus.set_servo_position(1, .5)
        sleep(.1)
        cyprus.set_pwm_values(2, period_value=100000, compare_value=0, compare_mode=cyprus.LESS_THAN_OR_EQUAL)
        sleep(2)
        print("DONE!!!")

    def setArmPosition(self):
        s0.go_to_position_threaded(float(self.moveArm.value*.0034))

    def homeArm(self):
        s0.go_until_press(0, 15000)
        while s0.is_busy():
            sleep(.1)
        s0.set_as_home()
        sleep(.1)
        s0.go_to_position_threaded(1.12)
        while s0.is_busy():
            sleep(.1)
        s0.set_as_home()
        sleep(.1)
        print(s0.get_position_in_units())
        
    def isBallOnTallTower(self):
        if (cyprus.read_gpio() & 0b0001):
            sleep(.1)
            if (cyprus.read_gpio() & 0b0001):
                return False
        else:
            return True

    def isBallOnShortTower(self):
        if (cyprus.read_gpio() & 0b0010):
            sleep(.1)
            if (cyprus.read_gpio() & 0b0010):
                return False
        else:
            return True
        
    def initialize(self):
        cyprus.initialize()
        cyprus.setup_servo(1)
        sleep(.1)
        cyprus.set_servo_position(1, .5)
        sleep(.1)
        cyprus.set_pwm_values(2, period_value=100000, compare_value=0, compare_mode=cyprus.LESS_THAN_OR_EQUAL)
        sleep(.1)
        self.homeArm()
        sleep(.1)
        self.magnet = False
        self.is_arm = False
        print("Home arm and turn off magnet")

    def resetColors(self):
        self.ids.armControl.color = YELLOW
        self.ids.magnetControl.color = YELLOW
        self.ids.auto.color = BLUE

    def quit(self):
        MyApp().stop()
    
sm.add_widget(MainScreen(name = 'main'))


# ////////////////////////////////////////////////////////////////
# //                          RUN APP                           //
# ////////////////////////////////////////////////////////////////

MyApp().run()
cyprus.close_spi()
