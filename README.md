Drum Detection in Audio Using Python
This project provides a Python script to detect drum hits in an audio file. The script uses inter-process communication (IPC) with Audacity to manipulate audio tracks.

Requirements
  Python 3.x installed.
  Audacity installed and running.
  mod-script-pipe enabled in Audacity.

Libraries Used
  os: Provides a way to use operating system-dependent functionality, such as file and directory manipulation, interacting with system environment, and executing system commands.
  sys: Provides access to some variables used or maintained by the interpreter and functions that interact strongly with the interpreter.
  numpy: Fundamental package for scientific computing with Python, offering support for arrays, matrices, and many mathematical functions.
  pydub: High-level audio library for working with audio files, allowing various audio manipulations such as slicing, concatenating, and applying effects.
  tempfile: Generates temporary files and directories for intermediate storage during program execution.
  time: Provides various time-related functions.


How It Works
The script sets up named pipes for communication with Audacity. It exports audio from Audacity, processes the audio to detect drum peaks, and then highlights these peaks in Audacity.

Steps:
1. Set up pipes:
  For Windows:
  Outbound communication: \\\\.\\pipe\\ToSrvPipe
  Inbound communication: \\\\.\\pipe\\FromSrvPipe
  End-of-line character: \r\n\0
  For Linux/Mac:
  Outbound communication: /tmp/audacity_script_pipe.to.<user_id>
  Inbound communication: /tmp/audacity_script_pipe.from.<user_id>
  End-of-line character: \n

2. Send commands to Audacity: Uses the send_command function to send commands to Audacity through the named pipe.

3. Receive responses from Audacity: Uses the get_response function to read responses from the named pipe.

4. Detect peaks in audio:
  LoadS the audio file using pydub.
  ConvertS the audio to an array of samples.
  IdentifyS peaks that exceed a certain threshold.
  EnsureS peaks are a minimum distance apart.

5. Highlight peaks in Audacity: Uses the highlight_peaks function to highlight and split the audio at detected peaks.

6. Temporary file handling: Uses the tempfile module to create and delete temporary audio files during processing.

Running the Script
  Ensure Audacity is running and mod-script-pipe is enabled.
  Run the script:

Acknowledgements
This script references the Audacity Scripting Manual.
  https://manual.audacityteam.org/man/scripting.html
  https://manual.audacityteam.org/man/scripting_reference.html
