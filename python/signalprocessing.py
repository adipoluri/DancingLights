import time

import numpy as np
from scipy.ndimage import gaussian_filter1d

from python import melbank


class ExpFilter:
    """Simple exponential smoothing filter"""

    def __init__(self, val=0.0, alpha_decay=0.5, alpha_rise=0.5):
        """Small rise / decay factors = more smoothing"""
        assert 0.0 < alpha_decay < 1.0, 'Invalid decay smoothing factor'
        assert 0.0 < alpha_rise < 1.0, 'Invalid rise smoothing factor'
        self.alpha_decay = alpha_decay
        self.alpha_rise = alpha_rise
        self.value = val

    def update(self, value):
        if isinstance(self.value, (list, np.ndarray, tuple)):
            alpha = value - self.value
            alpha[alpha > 0.0] = self.alpha_rise
            alpha[alpha <= 0.0] = self.alpha_decay
        else:
            alpha = self.alpha_rise if value > self.value else self.alpha_decay
        self.value = alpha * value + (1.0 - alpha) * self.value
        return self.value


mel_gain = ExpFilter(np.tile(1e-1, 24),
                     alpha_decay=0.01, alpha_rise=0.99)
mel_smoothing = ExpFilter(np.tile(1e-1, 24),
                          alpha_decay=0.5, alpha_rise=0.99)
common_mode = ExpFilter(np.tile(0.01, 60 // 2),
                        alpha_decay=0.99, alpha_rise=0.01)
r_filt = ExpFilter(np.tile(0.01, 60 // 2),
                   alpha_decay=0.2, alpha_rise=0.99)
g_filt = ExpFilter(np.tile(0.01, 60 // 2),
                   alpha_decay=0.05, alpha_rise=0.3)
b_filt = ExpFilter(np.tile(0.01, 60 // 2),
                   alpha_decay=0.1, alpha_rise=0.5)

fft_window = np.hamming(int(44100 / 60) * 2)
_prev_spectrum = np.tile(0.01, 60 // 2)
prev_fps_update = time.time()
samples_per_frame = int(44100 / 60)
y_roll = np.random.rand(2, samples_per_frame) / 1e16


def microphone_update(audio_samples):
    global y_roll, prev_fps_update
    # Normalize samples between 0 and 1
    y = audio_samples / 2.0 ** 15
    # Construct a rolling window of audio samples
    y_roll[:-1] = y_roll[1:]
    y_roll[-1, :] = np.copy(y)
    y_data = np.concatenate(y_roll, axis=0).astype(np.float32)

    vol = np.max(np.abs(y_data))
    if vol < 1e-7:
        print('No audio input. Volume below threshold. Volume:', vol)
        # led.pixels = np.tile(0, (3, config.N_PIXELS))
        # led.update()
    else:
        # Transform audio input into the frequency domain
        N = len(y_data)
        N_zeros = 2 ** int(np.ceil(np.log2(N))) - N
        # Pad with zeros until the next power of two
        y_data *= fft_window
        y_padded = np.pad(y_data, (0, N_zeros), mode='constant')
        YS = np.abs(np.fft.rfft(y_padded)[:N // 2])
        # Construct a Mel filterbank from the FFT data
        mel = np.atleast_2d(YS).T * mel_y.T
        # Scale data to values more suitable for visualization
        # mel = np.sum(mel, axis=0)
        mel = np.sum(mel, axis=0)
        mel = mel ** 2.0
        # Gain normalization
        mel_gain.update(np.max(gaussian_filter1d(mel, sigma=1.0)))
        mel /= mel_gain.value
        mel = mel_smoothing.update(mel)
        # Map filterbank output onto LED strip
        output = visualize(mel)
        # led.pixels = output
        # led.update()


def visualize(y):
    """Effect that maps the Mel filterbank frequencies onto the LED strip"""
    global _prev_spectrum
    y = np.copy(interpolate(y, 60 // 2))
    common_mode.update(y)
    diff = y - _prev_spectrum
    _prev_spectrum = np.copy(y)
    # Color channel mappings
    r = r_filt.update(y - common_mode.value)
    g = np.abs(diff)
    b = b_filt.update(np.copy(y))
    # Mirror the color channels for symmetric output
    r = np.concatenate((r[::-1], r))
    g = np.concatenate((g[::-1], g))
    b = np.concatenate((b[::-1], b))
    output = np.array([r, g, b]) * 255
    return output


def interpolate(y, new_length):
    # resizes array to equal number of LEDS
    if len(y) == new_length:
        return y
    x_old = _normalized_linspace(len(y))
    x_new = _normalized_linspace(new_length)
    z = np.interp(x_new, x_old, y)
    return z


def _normalized_linspace(size):
    return np.linspace(0, 1, size)


def create_mel_bank():
    global samples, mel_y, mel_x
    samples = int(44100 * 2 / (2.0 * 60))
    mel_y, (_, mel_x) = melbank.compute_melmat(num_mel_bands=24,
                                               freq_min=24,
                                               freq_max=12000,
                                               num_fft_bands=samples,
                                               sample_rate=44100)


samples = None
mel_y = None
mel_x = None
create_mel_bank()
