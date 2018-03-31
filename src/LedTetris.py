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


class LedTetris:

    PIECES = [
        [[0, 0], [1, 0], [0, 1], [1, 1]],  # O
        [[0, 0], [1, 0], [2, 0], [3, 0]],  # I
        [[0, 0], [0, 1], [1, 1], [2, 1]],  # L
        [[0, 1], [1, 1], [2, 1], [2, 0]],  # J
        [[0, 0], [1, 0], [1, 1], [2, 1]],  # Z
        [[1, 0], [2, 0], [0, 1], [1, 1]],  # S
        [[1, 0], [0, 1], [1, 1], [2, 1]]   # T
    ]

    def __init__(self):
        self.canvas = [[0 for k in range(8)] for i in range(8*4)]
        self.piece_position = [3, -1]
        self.piece = self.pick_piece()
        self.matrix = MAX7219()
        self.matrix.set_canvas(self.canvas)
        self.ticker = 1000
        self.ticker_timestamp = None

    def pick_piece(self):
        return self.PIECES[random.randint(0, len(self.PIECES)-1)]

    def tick(self):
        if not self.is_it_time():
            return
        self.piece_position[1] = self.piece_position[1] + 1
        contact = False
        for i in range(len(self.piece)):
            if self.piece_position[1] + self.piece[i][0] >= 31 or self.canvas[self.piece_position[1] + self.piece[i][0]+1][self.piece_position[0] + self.piece[i][1]] == 1:
                contact = True

        if contact:
            self.apply_piece(self.canvas)
            self.matrix.set_canvas(self.canvas)
            self.piece_position[1] = -1
            self.piece = self.pick_piece()
        else:
            temp = copy.deepcopy(self.canvas)
            self.apply_piece(temp)
            self.matrix.set_canvas(temp)

    def is_it_time(self):
        timestamp = time.time() * 1000
        if self.ticker_timestamp is None or timestamp - self.ticker_timestamp >= self.ticker:
            self.ticker_timestamp = timestamp
            return True
        return False

    def apply_piece(self, canvas):
        for i in range(len(self.piece)):
            canvas[self.piece_position[1] + self.piece[i][0]][self.piece_position[0] + self.piece[i][1]] = 1

    def end(self):
        self.matrix.close()


game = LedTetris()

try:
    while True:
        game.tick()
except KeyboardInterrupt:
    game.end()