#COMPLEX VERSION - 3 LED sections of LED lighting - each seperately addressable - but on the same APA102 string
from micropython import mem_info, alloc_emergency_exception_buf
import gc
import apa102_thread
import dmx512_rx
import config
import time

# Get Our Configuration
dmxrx_deviceaddress = config.dmx_address  # Our device Base DMX Address
dmxrx_devicechannels = config.dmx_channels  # How many channels we care about
apa102_numleds = config.apa102_numleds

# Environment Setup
gc.threshold(16384)  # Run Garbage collection everytime 16KB is allocated
alloc_emergency_exception_buf(512)  # Allocate Emergency Exception Buffer

def update_apa102_simple(grgbw_list):
    global_bright = int(grgbw_list[0] / 8)  # Valid 1-31, 0 = disable
    pixels.customwrite(global_bright, grgbw_list[1], grgbw_list[3], grgbw_list[2], 1, 3)

# LED 1-30 = LED Section 1
# LED 31-60 = LED Section 2
# LED 61-120 = LED Section 3

def update_apa102_complex(grgbw_list):
    # First String
    # print(list(grgbw_list))
    global_bright = int(grgbw_list[0] / 8)  # Valid 1-31, 0 = disable
    pixels.customwrite(global_bright, grgbw_list[1], grgbw_list[3], grgbw_list[2], 1, 30)
    # Second String
    if len(grgbw_list) >= 8:
        global_bright = int(grgbw_list[4] / 8)  # Valid 1-31, 0 = disable
        pixels.customwrite(global_bright, grgbw_list[5], grgbw_list[7], grgbw_list[6], 31, 60)
    # Third String
    if len(grgbw_list) >= 12:
        global_bright = int(grgbw_list[8] / 8)  # Valid 1-31, 0 = disable
        pixels.customwrite(global_bright, grgbw_list[9], grgbw_list[11], grgbw_list[10], 61, 120)

def dmxstatuschange(status):
    if status == 0: # We are offline & timed-out
        print("Turning off LED Output")
        pixels.clear()

# Configuring Modules - LED Outputs
pixels = apa102_thread.PIXELS(apa102_numleds, 18, 19)
pixels.test()
# Configuring Modules - DMX Receiver
dmx = dmx512_rx.DMX(dmxrx_deviceaddress, dmxrx_devicechannels, 1)
dmx.set_updatefunction(update_apa102_complex)
# dmx.set_statusfunction(dmxstatuschange)  # Not needed with full rainbow fallback

pixels.fullrainbow_init(2)  # Setup fallback Default if no DMX is received
fullrainbow_refresh_ms = time.ticks_ms() + 20  # 50 Rainbow updates/second (1/20ms)
print("INFO: Starting Main Loop")
while True:
    if dmx.loop() == 0:  # If 0 we have been offline for an extended period
        if fullrainbow_refresh_ms < time.ticks_ms():
            fullrainbow_refresh_ms = time.ticks_ms() + 20
            pixels.fullrainbow_timer()
            rgb = pixels.fullrainbow_get()
            pixels.globalwrite(30, rgb[0], rgb[2], rgb[1])



