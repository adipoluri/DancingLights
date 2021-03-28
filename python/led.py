import numpy as np
import serial

# updates LEDS on board.
pixels = np.tile(1, (3, 60))
_prev_pixels = np.tile(253, (3, 60))
PORT = 'COM1'

led = serial.Serial(PORT, 115200, timeout=0.1)


def update():
    global pixels, _prev_pixels
    # Truncate values and cast to integer
    pixels = np.clip(pixels, 0, 255).astype(int)
    p = np.copy(pixels)
    MAX_PIXELS_PER_PACKET = 126

    # Pixel indices
    idx = range(pixels.shape[1])
    idx = [i for i in idx if not np.array_equal(p[:, i], _prev_pixels[:, i])]
    n_packets = len(idx) // MAX_PIXELS_PER_PACKET + 1
    idx = np.array_split(idx, n_packets)
    for packet_indices in idx:
        m = []
        for i in packet_indices:
            m.append(i)  # Index of pixel to change
            m.append(p[0][i])  # Pixel red value
            m.append(p[1][i])  # Pixel green value
            m.append(p[2][i])  # Pixel blue value
        m = bytes(m)
        led.write(m)
    _prev_pixels = np.copy(p)
