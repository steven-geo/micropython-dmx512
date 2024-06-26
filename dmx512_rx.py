import time
import machine

# Constants - do not change otherwise DMX might break
DMX_BAUD = 250000  # DMX512 runs at 250,000 baud
DMX_RXTIMEOUT = const(2)  # Milliseconds to wait otherwise discard RX buffer
DMX_TIMEOUT = 30  # Seconds to wait before turning all outputs off after loss of DMX signal

class DMX:

    def set_updatefunction(self, function=None):
        """ Set the function in the main program to call when our data is updated """
        self.callbackupdate = function

    def set_statusfunction(self, function=None):
        """ Set the function in the main program to call when our status changes """
        self.callbackstatus = function

    def _setdmxstatus(self,status, silent = False):
        """ Set the dmx status and run our callback function """
        self.dmx_status = status
        if not silent:
            if self.dmx_status == 2:
                print("INFO: DMX Network Online")
            elif self.dmx_status == 1:
                print("WARNING: DMX Network Offline")
            elif self.dmx_status == 0:
                print(f"\nWARNING: DMX Offline for {DMX_TIMEOUT} seconds")
            else:
                print(f"ERROR: DMX Status is not valid: {self.dmx_status}")
        if self.callbackstatus:
            self.callbackstatus(self.dmx_status)
        # dmxstatus
        # 0 = Timeout (over 60 seconds since we received data)
        # 1 = Offline
        # 2 = Online
            
    def secondcounter(self, callback=None):
        """ This runs once per second to report/check our DMX512 network status """
        if self.dmx_status == 2 and self.char_counter < 5:
            # No DMX received in the last 1 second, we are now offline.
            self.dmx_offlinetimer = 0
            self._setdmxstatus(1)
        elif self.dmx_status < 2 and self.char_counter > 0:
            # We were offline/timedout, now we have received something, so we are now online
            self._setdmxstatus(2)
        elif self.dmx_status < 2 and self.char_counter == 0:
            # Whilst we are not receiving DMX, increment offline timer.
            self.dmx_offlinetimer += 1
            print(".",end='')  # Whilst DMX is offline still output a '.' to show we are running
        elif self.dmx_status:
            # Every 1 second - print out some basic info to show we are running
            print(f"INFO: DMXpps={self.char_counter} Loops={self.loops} Ch={self.dmxrx_list} TotalCh={self.dmx_packet_length}")
        if self.dmx_offlinetimer >= DMX_TIMEOUT:
            # Ensures a safe/default mode is called every DMX_TIMEOUT seconds if offline
            self.dmx_offlinetimer = 0
            self._setdmxstatus(0)
        self.char_counter = 0
        self.loops = 0

    def loop(self):
        """ Monitors DMX RX and calls update functions if valid """
        if self.dmx_rx.any():
            self.dmx_buff+=self.dmx_rx.read(514)
            self.dmxrx_timer = time.ticks_ms()
            self.new_packet = True
        if time.ticks_diff(time.ticks_ms(), self.dmxrx_timer) > DMX_RXTIMEOUT:
            self.dmxrx_timer = time.ticks_ms()
            if len(self.dmx_buff) >= self.dmx_endchannel and self.dmx_buff[0] == 0 and self.new_packet:  # and self.dmx_buff[1] == 0
                self.char_counter+=1  # Counts valid packets received (per second).
                # self.dmxrx_list = list(self.dmx_buff[self.dmxrx_base-1:self.dmx_endchannel-1])  # Make a new list with just the channels we care about
                self.dmxrx_list = list(self.dmx_buff[self.dmxrx_base:self.dmx_endchannel])  # Make a new list with just the channels we care about
                if self.callbackupdate:
                    self.callbackupdate(self.dmxrx_list)
                self.new_packet = False
                self.dmx_packet_length = len(self.dmx_buff) - 2
            self.dmx_buff = b''  # using bytearray() is a lot slower!
        if len(self.dmx_buff) > 600:
            # Catch invalid data to make sure the buffer doesn't overflow
            print(f"ERROR: DMX Buff Length overflow: Length={len(self.dmx_buff)}")
            self.dmx_buff = b''  # using bytearray() is a lot slower!
        self.loops+=1
        return self.dmx_status

    def __init__(self, address, channels, rx_pin=1):
        self.dmxrx_base = address + 1
        # self.dmx_channels = channels
        self.dmx_endchannel = self.dmxrx_base + channels
        self.dmxrx_timer = time.ticks_ms()
        self.dmx_buff = bytearray()
        self.char_counter = 0
        self.dmx_offlinetimer = 0
        self.dmx_packet_length = 0
        self.dmxrx_list = []
        self.new_packet = False
        self.callbackupdate = None
        self.callbackstatus = None
        self.loops = 0
        self._setdmxstatus(2, True)  # By Default we are online
        print(f"INFO: Setting up DMX512 Rx on Channels {self.dmxrx_base-1}-{self.dmx_endchannel-2} ...  ", end='')
        dmx_rx_pin = machine.Pin(rx_pin)
        self.dmx_rx = machine.UART(0, baudrate=DMX_BAUD, rx=dmx_rx_pin, bits=8, parity=None, stop=2)
        self.timer_1second = machine.Timer(period=1000, mode=machine.Timer.PERIODIC, callback=self.secondcounter)
        print("Done.")

