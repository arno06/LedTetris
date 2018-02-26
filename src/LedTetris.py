import spidev
import time
import copy
import random


class MAX7219:
    REG_NOOP = 0x00
    REG_DECODEMODE = 0x09
    REG_INTENSITY = 0x0A
    REG_SCANLIMIT = 0x0B
    REG_SHUTDOWN = 0x0C
    REG_DISPLAYTEST = 0x0F

    def __init__(self, bus=0, device=0, led_count=8, matrix_count=4):
        self.bus = bus
        self.device = device
        self.led = led_count
        self.count = matrix_count
        self.spi = spidev.SpiDev()
        self.spi.open(bus, device)
        self.spi.cshigh = False
        self.spi.max_speed_hz = 8000000
        self.broadcast_command([MAX7219.REG_NOOP, 0x00])
        self.broadcast_command([MAX7219.REG_SCANLIMIT, 0x07])
        self.broadcast_command([MAX7219.REG_DECODEMODE, 0x00])
        self.broadcast_command([MAX7219.REG_DISPLAYTEST, 0x00])
        self.broadcast_command([MAX7219.REG_SHUTDOWN, 0x01])
        self.set_intensity(0x07)

    def command(self, data):
        self.spi.writebytes(data)

    def broadcast_command(self, data):
        self.command(data * self.count)

    def turn_on(self):
        i = 1
        while i <= self.led:
            self.broadcast_command([i, 1])
            i = i + 1

    def turn_off(self):
        i = 1
        while i <= self.led:
            self.broadcast_command([i, 0])
            i = i + 1

    def set_intensity(self, value):
        self.broadcast_command([MAX7219.REG_INTENSITY, value])

    def set_canvas(self, canvas):
        i = self.led - 1
        while i >= 0:
            cmd = []
            for j in range(self.count):
                line = ''
                for k in range(self.led):
                    v = canvas[(j * 8) + k][i]
                    line = line + str(v)
                cmd = cmd + [self.led - i, int(line, 2)]
            self.command(cmd)
            i = i - 1

    def close(self):
        self.broadcast_command([MAX7219.REG_SHUTDOWN, 0x01])
        self.turn_off()
        self.spi.close()


def tick():
    global part
    position[1] = position[1] + 1
    temp = copy.deepcopy(canvas)
    contact = False
    for i in range(len(part)):
        if position[1] + part[i][0] >= 31 or canvas[position[1] + part[i][0]+1][position[0] + part[i][1]] == 1:
            contact = True

    if contact:
        apply_part(canvas)
        matrix.set_canvas(canvas)
        position[1] = 0
        part = parts[random.randint(0, len(parts)-1)]
    else:
        apply_part(temp)
        matrix.set_canvas(temp)


def apply_part(context):
    for i in range(len(part)):
        context[position[1] + part[i][0]][position[0] + part[i][1]] = 1

canvas = [
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0]
]

parts = [
    [[0, 0], [1, 0], [0, 1], [1, 1]],
    [[0, 0], [1, 0], [2, 0], [3, 0]],
    [[0, 0], [0, 1], [1, 1], [2, 1]],
    [[0, 1], [1, 1], [2, 1], [2, 0]],
    [[0, 0], [1, 0], [1, 1], [2, 1]],
    [[1, 0], [2, 0], [0, 1], [1, 1]],
    [[1, 0], [0, 1], [1, 1], [2, 1]]
]

part = parts[0]
position = [3, 0]
matrix = MAX7219()
matrix.set_canvas(canvas)

try:
    while True:
        tick()
        time.sleep(1)
except KeyboardInterrupt:
    matrix.close()