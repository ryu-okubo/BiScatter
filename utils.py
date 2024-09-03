import numpy as np
import matplotlib.pyplot as plt
import glob
from pprint import pprint
from scipy import signal
import time
import pandas as pd
import scipy
from scipy.stats import linregress
import math
import time
from datetime import datetime


def zoom_fft(x, fs, min_freq = 0, max_freq=None, nfft=2**10):
    """take zoom fft

    Args:
        x (_type_): input signal
        fs (_type_): sampling frequency
        max_freq (_type_): max frequency we want fft to get
        nfft (_type_): number of fft bins 

    Returns:
        w, H: fft angle and amplitude (amplitude in complex)
    """
    if max_freq==None:
        max_freq = int(fs/2)
    
    H = signal.zoom_fft(x, fn=[min_freq,max_freq], m=nfft, fs=fs)
    w = np.linspace(min_freq, max_freq, nfft)

    return w, H

def get_output_theory(length_diff, band_width, chirp_duration, speed_ratio=0.7):
    """get output frequency of the BiLo system based on the given parameters

    Args:
        length_diff (int): transmission line difference
        band_width (int): bandwidth of the chirp signal
        chirp_duration (int): chirp duration of the chirp signal
        speed_ratio (float): speed of signal ratio with respect to speed of light, default to 0.7
    """
    inch2meter = 0.0254
    c = 2.98e8

    slope = band_width / chirp_duration

    length = length_diff*inch2meter 
    speed_signal = c*speed_ratio

    control_delay = length / speed_signal
    f_beat = control_delay * slope

    return f_beat

def parse_bin_file(filepath):
    parsed_data = []

    with open(filepath, 'rb') as file:
        # Read the entire file content
        content = file.read()

        # Decode the content to a string
        content_str = content.decode('utf-8').strip()

        # Split the content by lines
        lines = content_str.split('\r\n')

        for line in lines:
            if line and ',' in line:
                # Split each line by comma and convert to tuple of integers
                values = list(map(int, line.split(',')))
                if len(values) == 2 and values[0] < 1e8:
                    parsed_data.append(values)
        file.close()
    
    return parsed_data

def get_seg_idx(amplitude, fs):
    window_length = 20
    stft_nfft = 2**8
    window = signal.windows.hann(window_length)
    window = signal.windows.hann(window_length)
    f, t, Zxx = signal.stft(amplitude, fs, window=window, nperseg=window_length, noverlap=window_length-1, nfft=stft_nfft)

    Zxx_amplitude = np.abs(Zxx)
    
    corr_decay = 0.1
    corr_offset = 0.7
    corr_filter = np.exp(-np.arange(len(f)) * corr_decay) - corr_offset

    Zxx_corr = np.sum(Zxx_amplitude * corr_filter[:, np.newaxis], axis=0)
    Zxx_corr = (Zxx_corr - np.mean(Zxx_corr)) / np.std(Zxx_corr)

    peaks, _ = signal.find_peaks(Zxx_corr, prominence = 1.25)

    return peaks, Zxx_corr

def find_closest(array1, array2):
    closest_elements = []
    for element in array2:
        closest = np.argmin(np.abs(array1 - element))
        closest_elements.append(closest)
    return closest_elements

def sig2db(mag_spec):
    """signal to decibel converter

    Args:
        mag_spec (array): input signal

    Returns:
        _type_: output signal in db scale
    """
    return 20*np.log10(mag_spec)
