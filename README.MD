# Sample DMX512 and APA102 Multi Core code for the Raspberry Pi Pico

## dmx512_rx.py
This is a simple DMX512 receiving library

## apa102_thread.py
This uses the second processor in the raspberry Pi Pico to update the APA102 LED Light strip.

## complex_config.py & complex_main.py
These provide an example of multiple DMX addressable parts of a single LED string, showing more than a simple single colour can be controller per raspberry Pi Pico

## simple_config.py & simple_main.py
This is a simple DMX RGB example to set an APA102 LED string all to a single colour based on RGB values from the DMX bus


**NOTE: To use the above complex or simple examples, rename the files to config.py and main.py and copy to your raspberry Pi Pico, along with the dmx512_rx.py and apa102_thread.py library.**
