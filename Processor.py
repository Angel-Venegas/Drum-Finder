'''
py --version

Must be version 3.12
Use a virtual environment

py -3.12 -m venv venv
venv\Scripts\activate

'''

#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os # For operating system operations.
import time #  For adding delays
import sys # For platform-specific operations.
import numpy as np # For numerical operations on audio samples.
from pydub import AudioSegment # For high-level audio manipulation.
import tempfile # For creating temporary files.


if sys.platform == 'win32':
    print("pipe-test.py, running on windows")
    TONAME = '\\\\.\\pipe\\ToSrvPipe' 
    FROMNAME = '\\\\.\\pipe\\FromSrvPipe' 
    EOL = '\r\n\0'
else:
    print("pipe-test.py, running on linux or mac")
    TONAME = '/tmp/audacity_script_pipe.to.' + str(os.getuid())
    FROMNAME = '/tmp/audacity_script_pipe.from.' + str(os.getuid())
    EOL = '\n'

print("Write to  \"" + TONAME + "\"")
if not os.path.exists(TONAME):
    print(" ..does not exist.  Ensure Audacity is running with mod-script-pipe.")
    sys.exit()

print("Read from \"" + FROMNAME + "\"")
if not os.path.exists(FROMNAME):
    print(" ..does not exist.  Ensure Audacity is running with mod-script-ppipe.")
    sys.exit()

print("-- Both pipes exist.  Good.")

TOFILE = open(TONAME, 'w')
print("-- File to write to has been opened")
FROMFILE = open(FROMNAME, 'rt')
print("-- File to read from has now been opened too\r\n")



def send_command(command): # Sends commands to audacity
    """Send a single command."""
    print("Send: >>> \n" + command)
    TOFILE.write(command + EOL)
    TOFILE.flush()

def get_response(): # Constructs a String with a response from audacity
    """Return the command response."""
    result = ''
    line = ''
    while True:
        result += line
        line = FROMFILE.readline()
        if line == '\n' and len(result) > 0:
            break
    return result

def do_command(command): # https://manual.audacityteam.org/man/scripting_reference.html  # This code sends commands to audacity and returns the response
    """Send one command, and return the response."""
    send_command(command)
    response = get_response()
    print("Rcvd: <<< \n" + response)
    return response

def detect_peaks(audio_file, threshold=0.7, min_distance=3000): # Finds all of the largest peaks in a song, threshold is the 
    """Detect peaks in an audio file."""
    audio = AudioSegment.from_file(audio_file)
    
    samples = np.array(audio.get_array_of_samples())
    
    samples = np.abs(samples)

    bit_depth = audio.sample_width * 8
    max_amplitude = (2 ** (bit_depth - 1)) - 1

    threshold_value = threshold * max_amplitude 

    candidate_peaks = np.where(samples > threshold_value)[0]

    # Now that we have all of our largest peaks, we still have peak samples that are way too close too each other. The goal is to filter out the peaks such that any two peaks in the final list are at least min_distance samples apart.
    peaks = []
    last_peak = -min_distance
    for peak in candidate_peaks: # Remember, each peak is an index (or index of a sample) and we want each current index to be some minimum number of indexes apart from the previous index
        if peak - last_peak > min_distance:
            peaks.append(peak)
            last_peak = peak

    # audio.frame_rate is just the sample rate of the audio. The frame rate allows for the conversion of sample indices to actual time values in seconds.
    return peaks, audio.frame_rate

def highlight_peaks(peaks, frame_rate): # Highlights peaks at some distance from the center and then applies a split
    """Highlight peaks in Audacity and split at each peak."""
    for peak in peaks:
        time_in_seconds = peak / frame_rate # There are some amount of peaks in a sample rate for each second
        do_command(f'SelectTime: Start={time_in_seconds - 0.025} End={time_in_seconds + 0.025}')
        do_command('Split:')
        print(f"Split at {time_in_seconds} seconds")


def quick_test():
    """List of commands."""
    # Creates a temporary file of .wav which is uncompressed audio format
    temp_wav = tempfile.mktemp(suffix=".wav")
    print(f"Temporary WAV file location: {temp_wav}") # C:\Users\Username\AppData\Local\Temp\tmpxk9vdsr5.wav
    
    do_command(f'Export2: Filename="{temp_wav}" NumChannels=1') # Exports the currently selected audio in audacity to the named file (in this case, the temporary file, this happens immediately). So it is telling audacity to do this with one audio channel.
    
    peaks, frame_rate = detect_peaks(temp_wav)
    
    highlight_peaks(peaks, frame_rate)
    
    os.remove(temp_wav)
    print(f"Temporary file {temp_wav} deleted.")


quick_test()