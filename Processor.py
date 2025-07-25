# Reference: https://manual.audacityteam.org/man/scripting.html
# Make sure Audacity is running and mod-script-pipe is enabled before running this script.

import os
import sys
import numpy as np
from pydub import AudioSegment
import tempfile
import time

if sys.platform == 'win32':
    print("pipe-test.py, running on Windows")
    TONAME = '\\\\.\\pipe\\ToSrvPipe'
    FROMNAME = '\\\\.\\pipe\\FromSrvPipe'
    EOL = '\r\n\0'
else:
    print("pipe-test.py, running on Linux or macOS")
    TONAME = '/tmp/audacity_script_pipe.to.' + str(os.getuid())
    FROMNAME = '/tmp/audacity_script_pipe.from.' + str(os.getuid())
    EOL = '\n'

print("Write to  \"" + TONAME + "\"")
if not os.path.exists(TONAME):
    print(" ..does not exist. Ensure Audacity is running with mod-script-pipe.")
    sys.exit()

print("Read from \"" + FROMNAME + "\"")
if not os.path.exists(FROMNAME):
    print(" ..does not exist. Ensure Audacity is running with mod-script-pipe.")
    sys.exit()

print("-- Both pipes exist. Good.")

TOFILE = open(TONAME, 'w')
FROMFILE = open(FROMNAME, 'rt')
print("-- Pipes opened successfully\n")


def send_command(command):
    """Send a command to Audacity."""
    print("Send: >>> \n" + command)
    TOFILE.write(command + EOL)
    TOFILE.flush()

def get_response():
    """Get response from Audacity."""
    result = ''
    line = ''
    while True:
        result += line
        line = FROMFILE.readline()
        if line == '\n' and len(result) > 0:
            break
    return result

def do_command(command):
    """Send command to Audacity and return the response."""
    send_command(command)
    response = get_response()
    print("Rcvd: <<< \n" + response)
    return response

def detect_peaks(audio_file, threshold=0.9, min_distance=1000):
    """Detect major peaks in the audio file based on amplitude threshold and spacing."""
    audio = AudioSegment.from_file(audio_file)
    samples = np.abs(np.array(audio.get_array_of_samples()))

    bit_depth = audio.sample_width * 8
    max_amplitude = (2 ** (bit_depth - 1)) - 1
    threshold_value = threshold * max_amplitude

    threshold_peaks = np.where(samples > threshold_value)[0]

    peaks = []
    last_peak = -min_distance
    for peak in threshold_peaks:
        if peak - last_peak > min_distance:
            peaks.append(peak)
            last_peak = peak

    return peaks, audio.frame_rate

def highlight_peaks(peaks, frame_rate):
    """Highlight and split audio in Audacity at each detected peak."""
    for peak in peaks:
        time_in_seconds = peak / frame_rate
        do_command(f'SelectTime: Start={time_in_seconds - 0.025} End={time_in_seconds + 0.025}')
        do_command('Split:')
        print(f"Split at {time_in_seconds} seconds")

def quick_test():
    """Run peak detection and highlight them in the currently selected audio in Audacity."""
    temp_wav = tempfile.mktemp(suffix=".wav")
    print(f"Temporary WAV file: {temp_wav}")

    do_command(f'Export2: Filename="{temp_wav}" NumChannels=1')
    peaks, frame_rate = detect_peaks(temp_wav)
    highlight_peaks(peaks, frame_rate)

    os.remove(temp_wav)
    print(f"Temporary file {temp_wav} deleted.")

quick_test()