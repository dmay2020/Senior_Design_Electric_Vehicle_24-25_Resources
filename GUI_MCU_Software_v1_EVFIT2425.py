"""
GUI MCU Software

Electric Vechicle Capstone Research Team
Florida Institute of Technology Department of Electrical and Computer Engineering

Contributors : Derek May, Shawn Steakly, Elis Karcini, Alejandro Loynaz Ceballos

Last Updated : Fall 2024 

MIT License

Copyright (c) [2024] [Derek May]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

# Import(s)
import pygame, time, sys, random, math, smbus, statistics
import RPi.GPIO as GPIO
from pygame.locals import *
pygame.init()

# GFX Window Setup
BACKGROUND = (64, 64, 64)
WINDOW_WIDTH = 1920
WINDOW_HEIGHT = 1080
WINDOW = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption('Motor Control Panel')
FPS = 120
fpsClock = pygame.time.Clock()

# SPI Setup
CLK = 11
MISO = 21
MOSI = 13
SS = 15
GPIO.setmode(GPIO.BOARD)
GPIO.setup(CLK, GPIO.OUT)
GPIO.setup(MISO, GPIO.IN)
GPIO.setup(MOSI, GPIO.OUT)
GPIO.setup(SS, GPIO.OUT)

# POT Setup
ADS7830_ADDRESS = 0x4b
ADC_CHANNEL_0 = 0x00
bus = smbus.SMBus(1)

# SPI Send Byte Function
# Send 1 byte using the SPI protocol
def spiSendByte(data):
    GPIO.output(SS, GPIO.LOW)
    for bit in range(8):
        if data & 0x80:
            GPIO.output(MOSI, GPIO.HIGH)
        else:
            GPIO.output(MOSI, GPIO.LOW)
        data <<= 1
        
        GPIO.output(CLK, GPIO.HIGH)
        time.sleep(0.001)
        GPIO.output(CLK, GPIO.LOW)
        time.sleep(0.001)
    GPIO.output(SS, GPIO.HIGH)
    GPIO.output(MOSI, GPIO.LOW)

# Self-Contained Image Object
# Can be easily defined, updated and drawn to the screen multiple times.
class blitObject:
    def __init__(self, window, image_name, pos_x, pos_y, angle):
        self.window = window
        self.image = pygame.image.load(image_name)
        self.image.convert_alpha()
        self.width, self.height = self.image.get_size()
        self.center = (self.width/2, self.height/2)
        self.position = (pos_x, pos_y)
        self.angle = angle
        self.button_radius = min(self.width, self.height)/2
    
    def update(self):
        image_rect = self.image.get_rect(topleft = (self.position[0] - self.center[0], self.position[1] - self.center[1]))
        offset_center_to_pivot = pygame.math.Vector2(self.position) - image_rect.center
        rotated_offset = offset_center_to_pivot.rotate(-self.angle)
        rotated_image_center = (self.position[0] - rotated_offset.x, self.position[1] - rotated_offset.y)
        rotated_image = pygame.transform.rotate(self.image, self.angle)
        rotated_image_rect = rotated_image.get_rect(center = rotated_image_center)
        self.window.blit(rotated_image, rotated_image_rect)
    
    def clicked(self, click_position):
        x1 = self.position[0]
        y1 = self.position[1]
        x2 = click_position[0]
        y2 = click_position[1]
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        d = math.sqrt((dx * dx) + (dy * dy))
        if (self.button_radius >= d): return True
        else: return False

# Self-Contained 7-Segemnt Display Image Object
# Can be easily defined, updated and drawn to the screen multiple times.
class blit7seg:
    def __init__(self, window, pos_x, pos_y, size):
        if (size == "50" or size == "75" or size == "100"): self.size = size
        else: self.size = "100"
        file_ext = "__7seg_"+self.size+".png"
        self.d0 = pygame.image.load("0"+file_ext)
        self.d1 = pygame.image.load("1"+file_ext)
        self.d2 = pygame.image.load("2"+file_ext)
        self.d3 = pygame.image.load("3"+file_ext)
        self.d4 = pygame.image.load("4"+file_ext)
        self.d5 = pygame.image.load("5"+file_ext)
        self.d6 = pygame.image.load("6"+file_ext)
        self.d7 = pygame.image.load("7"+file_ext)
        self.d8 = pygame.image.load("8"+file_ext)
        self.d9 = pygame.image.load("9"+file_ext)
        self.d0.convert_alpha(window)
        self.d1.convert_alpha(window)
        self.d2.convert_alpha(window)
        self.d3.convert_alpha(window)
        self.d4.convert_alpha(window)
        self.d5.convert_alpha(window)
        self.d6.convert_alpha(window)
        self.d7.convert_alpha(window)
        self.d8.convert_alpha(window)
        self.d9.convert_alpha(window)
        self.window = window
        self.position = (pos_x, pos_y)
        self.width, self.height = self.d0.get_size()
        self.center = (self.width/2, self.height/2)
    
    def show(self, digit):
        image_rect = self.d0.get_rect(topleft=self.position)
        if (digit == 0): self.window.blit(self.d0, image_rect)
        elif (digit == 1): self.window.blit(self.d1, image_rect)
        elif (digit == 2): self.window.blit(self.d2, image_rect)
        elif (digit == 3): self.window.blit(self.d3, image_rect)
        elif (digit == 4): self.window.blit(self.d4, image_rect)
        elif (digit == 5): self.window.blit(self.d5, image_rect)
        elif (digit == 6): self.window.blit(self.d6, image_rect)
        elif (digit == 7): self.window.blit(self.d7, image_rect)
        elif (digit == 8): self.window.blit(self.d8, image_rect)
        elif (digit == 9): self.window.blit(self.d9, image_rect)
        elif (digit == 10):
            self.window.blit(self.d1, image_rect)
            self.window.blit(self.d0, image_rect)

# Read Potentiometer
# Reads the output of the ADC and averages it over 50 samples.
def read_pot(channel):
    inputs = [0] * 50
    bus.write_byte(ADS7830_ADDRESS, channel)
    for i in range(50):
        data = bus.read_i2c_block_data(ADS7830_ADDRESS, 0, 2)
        adc_value = (data[0] & 0xFF)
        inputs.append(adc_value)
        inputs.pop(0)
    avg_adc = statistics.mean(inputs)    
    return math.floor((avg_adc / 255.0) * 100)

def main () :
    # Initialize Window Objects
    WINDOW.fill(BACKGROUND)
    gauge = blitObject(WINDOW, '0to100gauge100.png', WINDOW_WIDTH/2, WINDOW_HEIGHT/2, 0)
    red_needle = blitObject(WINDOW, 'redneedle100.png', WINDOW_WIDTH/2, WINDOW_HEIGHT/2, 180)
    blue_needle = blitObject(WINDOW, 'blueneedle100.png', WINDOW_WIDTH/2, WINDOW_HEIGHT/2, 180)
    estop = blitObject(WINDOW, 'estop_100.png', 600 + (WINDOW_WIDTH/2), WINDOW_HEIGHT/2, 0)
    estop.button_radius = 74
    tf_tens_7seg = blit7seg(WINDOW, (WINDOW_WIDTH/2)-67, 100+(WINDOW_HEIGHT/2), "100")
    tf_ones_7seg = blit7seg(WINDOW, WINDOW_WIDTH/2, 100+(WINDOW_HEIGHT/2), "100")
    f_tens_7seg = blit7seg(WINDOW, (WINDOW_WIDTH/2)-67, 200+(WINDOW_HEIGHT/2), "100")
    f_ones_7seg = blit7seg(WINDOW, WINDOW_WIDTH/2, 200+(WINDOW_HEIGHT/2), "100")
    
    # PID Dependencies
    max_rate_of_change = 4
    current_rate_of_change = 0.0
    emergency = False
    target_frequency = 0
    frequency = 0
    
    # Update Blit Objects
    estop.update()
    gauge.update()
    blue_needle.update()
    red_needle.update()
    tf_tens_7seg.show(0)
    tf_ones_7seg.show(0)
    f_tens_7seg.show(0)
    f_ones_7seg.show(0)

    # Main Loop
    # Main loop where variables and graphics are updated, where PID is implemented, and where data is sent.
    looping = True
    while looping :
        # Event Handling
        ev = pygame.event.get()
        for event in ev :
            if event.type == QUIT :
                spiSendByte(0)
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                if (estop.clicked(pos)):
                    emergency = not emergency

        # Data Input
        target_frequency = read_pot(ADC_CHANNEL_0)
        
        # PID Controller
        if not emergency:
            if target_frequency > 100: target_frequency = 100
            elif target_frequency < 0: target_frequency = 0
            current_rate_of_change = max_rate_of_change * (target_frequency - frequency) / 100.0
            frequency = frequency + current_rate_of_change
            if frequency > 100:
                frequency = 100
            elif frequency < 0:
                frequency = 0
        else:
            target_frequency = 0
            frequency = 0
        
        # Data Output
        spiSendByte(int(math.floor(frequency)))
        
        # Update Blit Objects
        estop.update()
        gauge.update()
        blue_needle.angle = 180.0 - (frequency / 100.0 * 180.0)
        red_needle.angle = 180.0 - (target_frequency / 100.0 * 180.0)
        blue_needle.update()
        red_needle.update()
        tf_tens_7seg.show(math.floor(target_frequency/10))
        tf_ones_7seg.show(target_frequency - 10*(math.floor(target_frequency/10)))
        f_tens_7seg.show(math.floor(frequency/10))
        f_ones_7seg.show(math.floor(frequency - 10*(math.floor(frequency/10))))

        # Render Frame
        pygame.display.flip()
        dt = fpsClock.tick(FPS)/1000
        pygame.display.set_caption(f"MOTOR GUI | {math.floor(fpsClock.get_fps())}")
        
    GPIO.cleanup()
 
main()
