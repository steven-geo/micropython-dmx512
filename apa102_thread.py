# Based on https://github.com/isildur7/Dotstar-on-rpi-pico
import machine
import array
import utime
import _thread
import time
import random
import math

MAX_PIXELS = 512
REFRESHRATE = 100  # FPS/Hz (MAX of 100)
threadlocker = _thread.allocate_lock()

class PIXELS:

    def _getbaudrate(self):
        global REFRESHRATE
        """ Work out minimum viable baud rate to update the APA102 leds """
        # Works out the baudrate to ensure the led pixel strip refreshes end to end within 5ms (200Hz)
        # This ensures you cannot see the strip update individual pixels, but rather the whole string at once
        rp2040_clk = 125000000
        clock = (rp2040_clk / 2)  # Maximum SPI Clock the Pico can have
        minbaud = ((self.NUM_LEDS + 3)*32) * (REFRESHRATE * 2)  # Allow for start/stop and a packet gap
        while clock > 20000000:  # Max bitrate should be around 20MHz for APA102 LEDs
            clock = clock / 2
        while clock > minbaud:  # Divide the clock until we find one that is just fast enough
            clock = clock / 2
        spi_clock = int(clock * 2)  # Revert the last divide by 2
        spi_clock = int( 2 * round( (spi_clock) / 2. ))  # Round up to nearest binary boundary
        print(f" @ {spi_clock} baud for {self.NUM_LEDS} pixels... ",end='')
        return spi_clock

    def __init__(self, pixel_number, clock_pin, data_pin):
        """ Class inititation """
        print("INFO: Setting up APA102 Transmitter", end='')
        if pixel_number <= MAX_PIXELS:
            self.NUM_LEDS = pixel_number
        else:
            print(f"\nWARNING: Maximum number of pixels supported is {MAX_PIXELS} - limiting to {MAX_PIXELS}")
            self.NUM_LEDS = MAX_PIXELS
        self.pixel_update = False  # Will clear all pixels to 0 (Typically Off) when True
        self.led_ar = array.array("L", [0 for _ in range(self.NUM_LEDS+2)])
        spi_baud = self._getbaudrate()
        self.spi_sck = machine.Pin(clock_pin)
        self.spi_tx = machine.Pin(data_pin)
        self.spi=machine.SPI(0, baudrate=spi_baud, sck=self.spi_sck, mosi=self.spi_tx)
        self.thread = _thread.start_new_thread(self._apa102_threadfunction,())
        print("Done.")

    def _apa102_threadfunction(self):
        while True:
            try:
                # Refresh Pixels if any change has been done to the pixel buffer
                if self.pixel_update:
                    self.led_ar[0] = 0x00000000  # start marker
                    self.led_ar[-1] = 0xffffffff  # end marker
                    pre_final = bytearray(self.led_ar)
                    # print(pre_final)  # Prints out Byte Array being sent to LEDs
                    # print('.',end='')
                    self.spi.write(pre_final)
                    update = False
            except:
                pass

    def _combine_color(self, red, green, blue):
        """ Make a multi int rgb value into a single 24 bit RGB value """
        return (red << 16) + (green << 8) + blue

    def _reverseBits(n, no_of_bits):
        """ Flip LSB to MSB direction """
        result = 0
        for i in range(no_of_bits):
            result <<= 1
            result |= n & 1
            n >>= 1
        return result

    def _buffer(self, brightness, red, green, blue, startled = 1, endled = None):
        if startled < 1:
            startled = 1
        if endled is None:
            endled = self.NUM_LEDS
        elif endled > self.NUM_LEDS:
            endled = self.NUM_LEDS
        for i in range(startled, endled+1):
            rgb = self._combine_color(red, blue, green)  # APA102 Operate in RBG mode
            # check APA102-2020 docs, first three bits are markers, next bits are brightness
            # then follow BGR pattern. These values are reversed. (LSB->MSB)
            # led_ar[i] = ((0xe0 | _reverseBits(brightness, 5)) << 24) | (self._reverseBits((rgb & 0xFF), 8) << 16) | (self.reverseBits((rgb >> 8 & 0xFF), 8) << 8) | (self._reverseBits((rgb >> 16 & 0xFF), 8))
            # for some reason, this works and not the one above although
            # it may seem wrong. There is something about the bytearray method
            # that makes this work and I hope it doesn't change
            self.led_ar[i] = rgb << 8 | (0xe0 | brightness)

    def clear(self):
        """ Clear LED Array - All Lights off """
        self._buffer(0,0,0,0)
        self.pixel_update = True

    def customwrite(self, brightness, red, green, blue, startled=1, endled=None):
        """ Simple Clear, Fill, Write the buffer - then send to the pixels """
        self._buffer(brightness, red, green, blue, startled, endled)
        self.pixel_update = True

    def globalwrite(self, brightness, red, green, blue):
        """ Simple Clear, Fill, Write the buffer - then send to the pixels """
        self._buffer(brightness, red, green, blue)
        self.pixel_update = True

    def test(self, brightness = 3):
        print("INFO: Running LED Testing")
        speed = .25
        # print("R",end='')
        self.globalwrite(brightness, 255, 0, 0)
        time.sleep(speed)
        # print("G",end='')
        self.globalwrite(brightness, 0, 255, 0)
        time.sleep(speed)
        # print("B",end='')
        self.globalwrite(brightness, 0, 0, 255)
        time.sleep(speed)
        # print("W",end='')
        self.globalwrite(brightness, 255, 255, 255)
        time.sleep(speed)
        # print("0",end='')
        self.globalwrite(brightness, 0, 0, 0)

    def hsv2rgb(self, hue, s = 1, v = 1):
        """ Convert a Hue, Saturation, Value colour into rgb """
        # hue = 0-2880, s = 0-1, v = 0-1
        h1 = hue / 8
        h60 = h1 / 60.0
        h60f = math.floor(h60)
        hi = int(h60f) % 6
        f = h60 - h60f
        p = v * (1 - s)
        q = v * (1 - f * s)
        t = v * (1 - (1 - f) * s)
        r, g, b = 0, 0, 0
        if hi == 0: r, g, b = v, t, p
        elif hi == 1: r, g, b = q, v, p
        elif hi == 2: r, g, b = p, v, t
        elif hi == 3: r, g, b = p, q, v
        elif hi == 4: r, g, b = t, p, v
        elif hi == 5: r, g, b = v, p, q
        r, g, b = int(r * 255), int(g * 255), int(b * 255)
        return [r, g, b]

    def fullrainbow_timer(self):
        self.fullrainbow_led_loc = self.fullrainbow_led_loc + self.fullrainbow_speed  # increment location in rainbow
        if self.fullrainbow_led_loc >= 2880: self.fullrainbow_led_loc = self.fullrainbow_led_loc - 2880  # loop around
        led_loc = int(self.fullrainbow_led_loc)  # ensure led_loc is an int
        rgb = self.hsv2rgb(led_loc)
        self.fullrainbow_buff = rgb

    def fullrainbow_init(self, skip = 5, start_pos = -1):
        # skip = How many positions to skip of 2880 on each update, higher number is a quicker moving rainbow
        # start_pos = Value in 2880 to start from, usful to sync multiple rainbows. -1 to select a random start
        self.timerdelay = 0.02  # 50Hz refresh (default)
        if start_pos>= 0:
            self.fullrainbow_led_loc = start_pos
        else:
            self.fullrainbow_led_loc = random.randrange(0, 2880)  # Location in current Rainbow, init with a random start each time
        self.fullrainbow_speed = skip  # How many leds to skip on each update - ie speed up the rotation.
        self.fullrainbow_buff = [0,0,0]
        print(f"INFO: Starting Full Rainbow at position {self.fullrainbow_led_loc} with a speed of {self.fullrainbow_speed}")

    def fullrainbow_get(self):
        return self.fullrainbow_buff

# 32 bits per pixel
# Ensure Update is 100fps to be well within DMX update speeds
# APA102 can go up to 24 MHz in optimal conditions
# So @ 24Mbaud @ 32bit = 748K pixels per second @ 100fps = 6000 pixels THEORETICAL MAX
# So @ 12Mbaud @ 32bit = 374K pixels per second @ 100fps = 3000 pixels MAX
# So @ 6Mbaud @ 32bit = 187K pixels per second @ 100fps = 1500 pixels MAX
# So @ 1Mbaud @ 32bit = 31K pixels per second @ 100fps = 300 pixels MAX
# So @ 100Kbaud @ 32bit = 3K1 pixels per second @ 100fps = 30 pixels MAX
