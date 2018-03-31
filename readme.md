LedTetris
======

Repository for a simple Tetris game running on a raspberry pi zero w with a dot matrix (max 7219) acting as a display and using an Android App as controller through Bluetooth.

Requirements
------
 * Raspberry PI (tested on a zero w)
 * [Dot Matrix MAX7219] (https://www.google.fr/search?q=max7219+dot+matrix&oq=max7219+dot+matrix)
 * Android Device

Setup
-------

### Raspberry PI

First things first, Raspbian was used as operating system (configured to allow ssh connection through local network)

Make sure to setup bluetooth properly, meaning:
 * install bluez & python-bluez
 * run bluetoothctl command to pair with your android device


### Dot Matrix MAX7219

3 steps:
 * enable SPI into raspi-config
 * install spidev
 * connect it (https://fr.pinout.xyz/pinout/)
   * VCC : pin 2
   * Ground : pin 6
   * DataIn : pin 19
   * Chip Select : pin 24
   * Clock : pin 23


### Android Device

TBD


Classes
------

### MAX7219
Represents the minimum abstraction required for manipulating a MAX7219 Dot Matrix. It starts Spidev and open the correct bus (in our case pin 24 stands for bus0), setup the registers required for the matrix to run properly and proposes utility methods.
It makes life easier when manipulating multiple chained Dot Matrix, handling one List for the canvas.

#### def command(data)
Alias for spidev.writebytes

#### def broadcast_command(data)
Allow to send 1 command to each Dot Matrix

#### def turn_on()
Turn on each led of every matrix

#### def turn_off()
Turn off each led of every matrix

#### def set_intensity(value)
Define the correct register to set the same brightness intensity for every matrix (value between 0 and 15)

#### def set_canvas(canvas)
Take one List (of row, each row being List of int values) and send the proper command to define each led state (0 off, 1 on)

#### def close()
Make sure every thing is stopped (led turned off & spidev closed)

### LedTetris

### BluetoothThread