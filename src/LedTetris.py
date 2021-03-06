import spidev
from bluetooth import *
import threading
import time
import copy
import random
import math


class MAX7219:
    ON = 1
    OFF = 0

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
            self.broadcast_command([i, MAX7219.ON])
            i = i + 1

    def turn_off(self):
        i = 1
        while i <= self.led:
            self.broadcast_command([i, MAX7219.OFF])
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
        self.running = True
        self.score = 0

    def pick_piece(self):
        return self.PIECES[random.randint(0, len(self.PIECES)-1)]

    def tick(self):
        if not self.is_it_time() or not self.running:
            return
        self.piece_position[1] = self.piece_position[1] + 1
        contact = False
        for i in range(len(self.piece)):
            if self.piece_position[1] + self.piece[i][1] >= 31:
                contact = True
                continue

            if self.canvas[self.piece_position[1] + self.piece[i][1] + 1][self.piece_position[0] + self.piece[i][0]] == 1:
                contact = True

        if contact:
            self.apply_piece(self.canvas)
            self.matrix.set_canvas(self.canvas)
            self.piece_position = [3, -1]
            self.piece = self.pick_piece()

            completed_lines = []
            for k,l in enumerate(self.canvas):
                completed = True
                for led in l:
                    completed = completed and led is 1
                if completed:
                    completed_lines.append(k)
            if len(completed_lines) > 0:
                self.running = False
                for i in completed_lines:
                    self.set_line(i, MAX7219.OFF)
                time.sleep(0.5)
                for i in completed_lines:
                    self.set_line(i, MAX7219.ON)
                time.sleep(0.5)
                for i in completed_lines:
                    self.set_line(i, MAX7219.OFF)
                time.sleep(0.5)
                for i in completed_lines:
                    self.canvas.pop(i)
                    self.canvas.insert(0, [MAX7219.OFF for k in range(8)])
                self.increment_score(len(completed_lines))
                self.running = True

        else:
            temp = copy.deepcopy(self.canvas)
            self.apply_piece(temp)
            self.matrix.set_canvas(temp)

    def increment_score(self, count_lines):
        self.score = self.score + (count_lines * 10)
        self.ticker = self.ticker - (count_lines * 10)
        self.ticker = max(self.ticker, 300)

    def is_it_time(self):
        timestamp = time.time() * 1000
        if self.ticker_timestamp is None or timestamp - self.ticker_timestamp >= self.ticker:
            self.ticker_timestamp = timestamp
            return True
        return False

    def set_line(self, y, state):
        if y < 0 or y > len(self.canvas)-1:
            return
        self.canvas[y] = [state for i in range(8)]
        self.refresh()

    def apply_piece(self, canvas):
        for i in range(len(self.piece)):
            if self.is_out_of_boundary(self.piece_position[0] + self.piece[i][0], self.piece_position[1] + self.piece[i][1]):
                print("Out of Boundary: %s, %s", self.piece_position[0] + self.piece[i][0], self.piece_position[1] + self.piece[i][1])
                continue
            canvas[self.piece_position[1] + self.piece[i][1]][self.piece_position[0] + self.piece[i][0]] = 1

    def move_piece_left(self):
        for p in self.piece:
            if self.piece_position[0] + p[0] - 1 < 0 or self.is_led_on(self.piece_position[0] + p[0] - 1, self.piece_position[1] + p[1]):
                return
        self.piece_position[0] = self.piece_position[0] - 1
        self.refresh()

    def move_piece_right(self):
        for p in self.piece:
            if self.piece_position[0] + p[0] + 1 > 7 or self.is_led_on(self.piece_position[0] + p[0] + 1, self.piece_position[1] + p[1]):
                return
        self.piece_position[0] = self.piece_position[0] + 1
        self.refresh()

    def move_piece_down(self):
        for p in self.piece:
            if self.is_out_of_boundary(self.piece_position[0] + p[0], self.piece_position[1] + p[1] + 1):
                return
            if self.is_led_on(self.piece_position[0] + p[0], self.piece_position[1] + p[1] + 1):
                return
        self.ticker_timestamp = time.time() * 1000
        self.piece_position[1] = self.piece_position[1] + 1
        self.refresh()

    def clockwise_rotate_piece(self):
        self.rotate_piece(90)

    def anticlockwise_rotate_piece(self):
        self.rotate_piece(-90)

    def rotate_piece(self, rotation_angle):
        rad = rotation_angle * (math.pi / 180)

        cos = math.cos(rad)
        sin = math.sin(rad)

        rotated_piece = []

        for p in self.piece:
            rotated_p = [
                int(round((cos * p[0]) - (sin * p[1]))),
                int(round((p[0] * sin) + (cos * p[1])))
            ]
            if self.is_out_of_boundary(self.piece_position[0] + rotated_p[0], self.piece_position[1] + rotated_p[1]) or self.is_led_on (self.piece_position[0] + rotated_p[0], self.piece_position[1] + rotated_p[1]):
                return
            rotated_piece.append(rotated_p)

        self.piece = rotated_piece
        self.refresh()

    def is_led_on(self, x, y):
        return self.canvas[y][x] == 1

    def is_out_of_boundary(self, x, y):
        return not (0 <= x < len(self.canvas[0])) or not(0 <= y < len(self.canvas))

    def refresh(self):
        temp = copy.deepcopy(self.canvas)
        self.apply_piece(temp)
        self.matrix.set_canvas(temp)

    def end(self):
        self.matrix.close()


class BluetoothThread(threading.Thread):
    def __init__(self, command_callback):
        threading.Thread.__init__(self)
        self.server_socket = BluetoothSocket(RFCOMM)
        self.server_socket.bind(("", PORT_ANY))
        self.server_socket.listen(1)
        self.connected = False
        self.client_socket = None
        self.client_info = None
        self.command_callback = command_callback
        self.running = True

    def await_connection(self):
        if self.connected:
            return
        print("Waiting for BlueController")
        self.client_socket, self.client_info = self.server_socket.accept()
        self.connected = self.client_socket is not None and self.client_info is not None
        print("Connected")

    def run(self):
        while self.running:
            self.await_connection()
            try:
                data = self.client_socket.recv(1024)
                if len(data) == 0:
                    pass
                self.command_callback(data)
            except IOError:
                pass
        print("Bluetooth ended")

    def close(self):
        if self.connected:
            self.client_socket.close()
        self.server_socket.close()
        self.connected = False
        self.running = False


def on_command(data):
    if data == "bottom":
        game.move_piece_down()
    if data == "left":
        game.move_piece_left()
    if data == "right":
        game.move_piece_right()
    if data == "A":
        game.clockwise_rotate_piece()
    if data == "B":
        game.anticlockwise_rotate_piece()
    print(data)


btThread = BluetoothThread(on_command)
game = LedTetris()

btThread.start()

try:
    while True:
        if btThread.connected:
            game.tick()
except KeyboardInterrupt:
    btThread.close()
    game.end()