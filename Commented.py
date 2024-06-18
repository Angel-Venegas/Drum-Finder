# Reference: https://manual.audacityteam.org/man/scripting.html
# Make sure Audacity is running first and that mod-script-pipe is enabled before running this script.

import os
'''
os:

Purpose: The os module in Python provides a way of using operating system-dependent functionality. This includes functionalities like reading or writing to the file system, handling file paths, and executing system commands.
Typical Use Cases:
    File and directory manipulation (e.g., creating, deleting, moving files and directories).
    Interacting with the system environment (e.g., environment variables).
    Running system commands and scripts.
'''
import sys
'''
os:

Purpose: The os module in Python provides a way of using operating system-dependent functionality. This includes functionalities like reading or writing to the file system, handling file paths, and executing system commands.
Typical Use Cases:
    File and directory manipulation (e.g., creating, deleting, moving files and directories).
    Interacting with the system environment (e.g., environment variables).
    Running system commands and scripts.
'''
import numpy as np
'''
numpy (imported as np):

Purpose: NumPy is a fundamental package for scientific computing with Python. It provides support for arrays, matrices, and many mathematical functions to operate on these data structures.
Typical Use Cases:
    Numerical computations and operations on arrays (e.g., element-wise arithmetic, linear algebra).
    Statistical operations (e.g., mean, median, standard deviation).
    Handling large multi-dimensional arrays and matrices efficiently.
'''
from pydub import AudioSegment
'''
pydub:

Purpose: PyDub is a high-level audio library for working with audio files. It allows you to perform various audio manipulations such as slicing, concatenating, and applying effects.
Typical Use Cases:
    Loading and saving audio files in different formats (e.g., WAV, MP3).
    Editing audio files (e.g., cutting, splicing, adding silence).
    Applying audio effects (e.g., volume changes, fade in/out, overlaying audio tracks).
'''
import tempfile
'''
tempfile:

Purpose: The tempfile module generates temporary files and directories. It is often used for creating temporary storage that can be automatically cleaned up when no longer needed.
Typical Use Cases:
    Creating temporary files and directories for intermediate storage during program execution.
    Ensuring temporary files are securely created and deleted to avoid conflicts and maintain security.
'''
import time


if sys.platform == 'win32': # This line checks the platform on which the script is running. The sys.platform variable contains a string that indicates the platform. If it equals 'win32', it means the script is running on a Windows operating system.
    print("pipe-test.py, running on windows")
    TONAME = '\\\\.\\pipe\\ToSrvPipe' #  In Windows, named pipes are used for inter-process communication (IPC). This pipe is used by the client process to send data or requests to the server process. It's essentially the outbound communication channel from the client’s perspective.
    FROMNAME = '\\\\.\\pipe\\FromSrvPipe' # This pipe is used for receiving data from a server process. This pipe is used by the server process to send data or responses back to the client process. It's the inbound communication channel for the client, allowing it to receive the server's responses.
    EOL = '\r\n\0' # End Of Line
    '''
    The \r character is a carriage return. In the context of text, a carriage return moves the cursor back to the beginning of the line without advancing to the next line.
    In the context of the code, the null character is likely used to mark the end of a message or command being sent through the named pipe, ensuring that the receiving process can detect where the message ends.

    IPC Explanation
    "Inter-Process Communication (IPC) is a set of mechanisms provided by the operating system to allow processes to communicate and synchronize their actions. IPC is crucial for coordinating activities and sharing data between processes running on the same or different machines. Examples of IPC mechanisms include pipes, message queues, shared memory, semaphores, and sockets."
    There are several types of IPC mechanisms, each suitable for different use cases, including:

        Pipes: Allows one-way communication between processes.
        Named Pipes: A more flexible version of pipes that allows bidirectional communication and can be used between unrelated processes and across networks.
        Message Queues: Allows processes to send and receive messages in a queue.
        Shared Memory: Allows multiple processes to access the same memory space.
        Semaphores: Used to control access to a common resource by multiple processes to avoid conflicts.
        Sockets: Allows communication over a network between processes running on different machines.
    
    Pipe Explanation
    "A pipe is a method of IPC that allows one process to send data to another process. Pipes can be anonymous, which are typically used for communication between related processes, such as a parent and child process. Named pipes, on the other hand, provide more flexibility as they can be used for communication between unrelated processes and can support bidirectional communication. Named pipes are identified by a name in the system and can even be used for network communication."

    When audacity mod-script-pipe is enabled it looks for those pipes in order to interact with them.
    '''
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

TOFILE = open(TONAME, 'w') # writing to the pipe
print("-- File to write to has been opened")
FROMFILE = open(FROMNAME, 'rt') # reading in text mode
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

def detect_peaks(audio_file, threshold=0.9, min_distance=1000): # Finds all of the largest peaks in a song, threshold is the 
    """Detect peaks in an audio file."""
    # Load the audio file
    audio = AudioSegment.from_file(audio_file)
    
    # This gets an array of amplitudes from the samples, if the audio is 48khz then each second of audio contains 48,000 samples. Each sample index contain an amplitude value positive or negative.
    samples = np.array(audio.get_array_of_samples())
    
    # Taking the absolute value of the samples' amplitudes since we want the highest value
    samples = np.abs(samples) # A sample is piece of audio from the smallest possible measurement of amplitude (which means each sample is an amplitude from the smallest possible measurement of amplitude) stored on the computer.

    # Finds the maximum value in the array of absolute sample values. This maximum amplitude is used to set a threshold for detecting significant peaks.
    # max_amplitude = np.max(samples)

    # Calculate the bit depth and then find the highest possible positive amplitude value for the given bit depth
    # Bit depth tells a program how many bits are used to represent each sample in the audio signal. 
    # For example, a bit depth of 16 means each sample is represented by 16 bits, allowing for 2^16 possible values.
    # The maximum positive amplitude value for a given bit depth is calculated as (2^(bit_depth - 1)) - 1.
    # This is because the audio signal is typically represented using signed integers, 
    # where one bit is used for the sign (positive or negative), leaving (bit_depth - 1) bits for the magnitude.
    bit_depth = audio.sample_width * 8
    max_amplitude = (2 ** (bit_depth - 1)) - 1

    
    # This calculates the perfect threshold value based on the bitdepth
    threshold_value = threshold * max_amplitude 

    # Identifys the candidate peaks that exceed the threshold value ([0] since a touple of one array is returned because our array of samples is only one dimension. If it was two dimensions then a touplew of two arrays would be returned.)
    candidate_peaks = np.where(samples > threshold_value)[0] # Getting peaks that are larger than the threshold

    # Now that we have all of our largest peaks, we still have peak samples that are way too close too each other. The goal is to filter out the peaks such that any two peaks in the final list are at least min_distance samples apart.
    peaks = []
    last_peak = -min_distance # last_peak is initially set to -min_distance to ensure that the first candidate peak is always added to the peaks list, regardless of its position.
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
    
    # Detect peaks in the exported audio
    peaks, frame_rate = detect_peaks(temp_wav)
    
    # Highlight peaks in Audacity
    highlight_peaks(peaks, frame_rate)
    
    # Clean up temporary file
    os.remove(temp_wav)
    print(f"Temporary file {temp_wav} deleted.")


quick_test()


'''
When discussing audio sampling, particularly in the context of a 48 kHz sample rate, it's essential to understand the relationship between samples, indices, and amplitudes.

Key Concepts

Sample Rate:
The sample rate (e.g., 48 kHz) refers to the number of samples taken per second of audio.
In a 48 kHz audio file, 48,000 samples are taken every second.

Sample:
A sample refers to a single data point in the audio signal.
Each sample represents the amplitude of the audio signal at a specific point in time.
The amplitude is a measure of the sound pressure level at that moment, which is a numerical value.

Index:
The index refers to the position of the sample within the array of samples.
Indices are used to access specific samples in the array.
Relationship
Amplitude: The actual value of the audio signal at a specific point in time.
Index: The position of the sample within the array, indicating the time position relative to the start of the audio.



In Audacity, the numbers 1, 0, and -1 typically refer to the amplitude values of an audio signal in a normalized form. Here's what each value represents:

Normalized Amplitude Values
    1: This represents the maximum positive amplitude of the audio signal.
    0: This represents the zero crossing point, where the audio signal has no amplitude. It is the equilibrium point in the waveform.
    -1: This represents the maximum negative amplitude of the audio signal.

Understanding the Amplitude Values
    When an audio signal is normalized, its amplitude values are scaled to fall within the range of -1 to 1. This is a common practice in digital audio processing to simplify calculations and ensure consistency across different audio files.

How These Values Appear in Audacity
    Waveform Display:
        When you view an audio track in Audacity, the waveform's vertical axis typically ranges from -1 to 1.
        The peaks and troughs of the waveform correspond to these amplitude values.
        Positive peaks approach 1, while negative troughs approach -1.
        The line at the center of the waveform display corresponds to 0, the zero crossing point.
    
    Audio Clipping:
        If the audio signal exceeds the range of -1 to 1, it will clip, causing distortion. Clipping occurs when the amplitude is too high and is forcibly limited to the maximum allowable value, resulting in a flat top or bottom on the waveform.

Example
Consider a simple sine wave:
    At its highest point (positive peak), the amplitude is 1.
    At its lowest point (negative peak), the amplitude is -1.
    When it crosses the center line (zero crossing), the amplitude is 0.

Practical Implications
    Editing and Effects:
        When applying effects or editing audio in Audacity, maintaining amplitude levels within the range of -1 to 1 ensures that the audio does not clip and distort.
        
    Visualization:
        Understanding these normalized values helps you interpret the waveform display correctly, allowing you to identify loud and quiet parts of the audio easily.

    Audio Processing:
        Many audio processing algorithms assume that the audio signal is normalized, simplifying the implementation and improving compatibility across different systems and software.

Summary
1: Maximum positive amplitude.
0: Zero crossing point (no amplitude).
-1: Maximum negative amplitude.
Usage in Audacity: These values are used to represent the normalized amplitude of the audio signal, helping in visualization, editing, and processing without causing clipping or distortion.
Understanding these normalized values helps you work more effectively with audio signals in Audacity and other digital audio workstations.
'''