# Reference: https://manual.audacityteam.org/man/scripting.html
'''
Needs Python 3.11 to work:
# py -3.11 -m venv env
# .\env\Scripts\Activate
# pip install pydub numpy
# python Toggle.py
'''

import os
import sys
import numpy as np
from pydub import AudioSegment
import tempfile

# ======================== CONFIG TOGGLE ========================
MODE = "isolate"   # "isolate"(isolates drums) or "silence"(silence drums)
WINDOW_MS = 60     # same window for both modes (centered on peak)
PRE_FADE_MS = 20   # for "silence" mode
POST_FADE_MS = 20  # for "silence" mode
THRESHOLD = 0.7    # peak detect threshold (0..1)
MIN_DISTANCE = 1000  # samples between peaks
# ===============================================================

# ---------- Audacity pipe setup ----------
if sys.platform == 'win32':
    print("Running on Windows")
    TONAME = '\\\\.\\pipe\\ToSrvPipe'
    FROMNAME = '\\\\.\\pipe\\FromSrvPipe'
    EOL = '\r\n\0'
else:
    print("Running on Linux or macOS")
    TONAME = f'/tmp/audacity_script_pipe.to.{os.getuid()}'
    FROMNAME = f'/tmp/audacity_script_pipe.from.{os.getuid()}'
    EOL = '\n'

print(f'Write to  "{TONAME}"')
if not os.path.exists(TONAME):
    print(" ..does not exist. Ensure Audacity is running with mod-script-pipe.")
    sys.exit()

print(f'Read from "{FROMNAME}"')
if not os.path.exists(FROMNAME):
    print(" ..does not exist. Ensure Audacity is running with mod-script-pipe.")
    sys.exit()

print("-- Both pipes exist. Good.")
TOFILE = open(TONAME, 'w')
print("-- File to write to has been opened")
FROMFILE = open(FROMNAME, 'rt')
print("-- File to read from has now been opened too\r\n")

def send_command(command):
    print("Send: >>>\n" + command)
    TOFILE.write(command + EOL)
    TOFILE.flush()

def get_response():
    result = ''
    line = ''
    while True:
        result += line
        line = FROMFILE.readline()
        if line == '\n' and len(result) > 0:
            break
    return result

def do_command(command):
    send_command(command)
    response = get_response()
    print("Rcvd: <<<\n" + response)
    return response

# ---------- Peak detection ----------
def detect_peaks(audio_file, threshold=0.7, min_distance=1000):
    audio = AudioSegment.from_file(audio_file)
    samples = np.abs(np.array(audio.get_array_of_samples()))
    bit_depth = audio.sample_width * 8
    max_amplitude = (2 ** (bit_depth - 1)) - 1
    thr_value = threshold * max_amplitude
    threshold_peaks = np.where(samples > thr_value)[0]

    peaks = []
    last_peak = -min_distance
    for p in threshold_peaks:
        if p - last_peak > min_distance:
            peaks.append(p)
            last_peak = p
    return peaks, audio.frame_rate

# ---------- Helpers ----------
def _compute_windows_ms(peaks, frame_rate, window_ms, total_ms):
    half = window_ms // 2
    centers_ms = [int((p / frame_rate) * 1000) for p in peaks]
    windows = []
    for c in centers_ms:
        s = max(0, c - half)
        e = min(total_ms, c + half)
        if e > s:
            windows.append([s, e])
    windows.sort(key=lambda w: w[0])
    # merge overlaps
    merged = []
    for w in windows:
        if not merged or w[0] > merged[-1][1]:
            merged.append(w)
        else:
            merged[-1][1] = max(merged[-1][1], w[1])
    return merged

def _fit_to_length(seg, target_len_ms, frame_rate):
    if len(seg) == target_len_ms:
        return seg
    if len(seg) < target_len_ms:
        return seg + AudioSegment.silent(duration=target_len_ms - len(seg), frame_rate=frame_rate)
    return seg[:target_len_ms]

def _replace_segment_inplace(track, start_ms, end_ms, new_seg):
    target_len = end_ms - start_ms
    fixed = _fit_to_length(new_seg.set_frame_rate(track.frame_rate), target_len, track.frame_rate)
    return track[:start_ms] + fixed + track[end_ms:]

# ---------- MODE: ISOLATE (drums only) ----------
def render_isolated_drums(original_file, peaks, frame_rate, keep_duration_ms=60, fade_duration_ms=8):
    audio = AudioSegment.from_file(original_file)
    total_ms = len(audio)
    windows = _compute_windows_ms(peaks, frame_rate, keep_duration_ms, total_ms)

    out = AudioSegment.silent(duration=total_ms, frame_rate=audio.frame_rate)
    for start, end in windows:
        snippet = audio[start:end].fade_in(fade_duration_ms).fade_out(fade_duration_ms)
        out = out.overlay(snippet, position=start)

    path = os.path.join(os.getcwd(), "drums_only.wav")
    out.set_channels(2).export(path, format="wav")
    return path

# ---------- MODE: SILENCE (sample-accurate pre/post fades) ----------
def render_silenced_drums_sample_accurate(original_file, peaks, frame_rate,
                                          silence_window_ms=60, pre_fade_ms=20, post_fade_ms=20,
                                          silence_full=True, attenuation_db=30):
    audio = AudioSegment.from_file(original_file)
    if audio.channels > 1:
        audio = audio.set_channels(1)

    sr = audio.frame_rate
    sw = audio.sample_width
    dtype = {1: np.int8, 2: np.int16, 3: np.int32, 4: np.int32}.get(sw, np.int16)

    samples = np.array(audio.get_array_of_samples()).astype(np.int64)
    total_samples = len(samples)
    total_ms = len(audio)
    windows_ms = _compute_windows_ms(peaks, frame_rate, silence_window_ms, total_ms)

    spms = sr / 1000.0
    pre_n  = int(round(pre_fade_ms * spms))
    post_n = int(round(post_fade_ms * spms))

    def clamp(a, lo, hi): return max(lo, min(hi, a))

    for i, (start_ms, end_ms) in enumerate(windows_ms):
        start_s = clamp(int(round(start_ms * spms)), 0, total_samples)
        end_s   = clamp(int(round(end_ms * spms)),   0, total_samples)
        prev_end_s   = clamp(int(round(windows_ms[i-1][1] * spms)), 0, total_samples) if i > 0 else 0
        next_start_s = clamp(int(round(windows_ms[i+1][0] * spms)), 0, total_samples) if i + 1 < len(windows_ms) else total_samples

        # Pre-fade to 0
        ps = clamp(start_s - pre_n, prev_end_s, start_s)
        n = start_s - ps
        if n > 0:
            seg = samples[ps:start_s].astype(np.float64)
            ramp = np.linspace(1.0, 0.0, n, endpoint=True)
            samples[ps:start_s] = np.round(seg * ramp).astype(np.int64)

        # Silence/attenuate window
        if end_s > start_s:
            if silence_full:
                samples[start_s:end_s] = 0
            else:
                gain = 10.0 ** (-attenuation_db / 20.0)
                seg = samples[start_s:end_s].astype(np.float64) * gain
                samples[start_s:end_s] = np.round(seg).astype(np.int64)

        # Post-fade from 0
        pe = clamp(end_s + post_n, end_s, next_start_s)
        n = pe - end_s
        if n > 0:
            seg = samples[end_s:pe].astype(np.float64)
            ramp = np.linspace(0.0, 1.0, n, endpoint=True)
            samples[end_s:pe] = np.round(seg * ramp).astype(np.int64)

    # Clip and rebuild
    if dtype == np.int8:
        samples = np.clip(samples, -128, 127).astype(np.int8)
    elif dtype == np.int16:
        samples = np.clip(samples, -32768, 32767).astype(np.int16)
    else:
        samples = np.clip(samples, -2147483648, 2147483647).astype(np.int32)

    processed = AudioSegment(data=samples.tobytes(), sample_width=sw, frame_rate=sr, channels=1)
    path = os.path.join(os.getcwd(), "drums_silenced.wav")
    processed.set_channels(2).export(path, format="wav")
    return path

# ---------- One-button runner ----------
def run_once(mode):
    temp_wav = tempfile.mktemp(suffix=".wav")
    print(f"[{mode.upper()}] Temporary WAV file location: {temp_wav}")
    do_command(f'Export2: Filename="{temp_wav}" NumChannels=1')

    peaks, frame_rate = detect_peaks(temp_wav, threshold=THRESHOLD, min_distance=MIN_DISTANCE)
    print(f"Detected peaks: {len(peaks)}")

    if mode == "isolate":
        out = render_isolated_drums(temp_wav, peaks, frame_rate, keep_duration_ms=WINDOW_MS, fade_duration_ms=8)
    elif mode == "silence":
        out = render_silenced_drums_sample_accurate(temp_wav, peaks, frame_rate,
                                                    silence_window_ms=WINDOW_MS,
                                                    pre_fade_ms=PRE_FADE_MS,
                                                    post_fade_ms=POST_FADE_MS,
                                                    silence_full=True, attenuation_db=30)
    else:
        raise ValueError('MODE must be "isolate" or "silence"')

    do_command(f'Import2: Filename="{out}"')

    os.remove(temp_wav)
    os.remove(out)
    print(f"[{mode.upper()}] Temporary files {temp_wav} and {out} deleted.")

# ---------- Run ----------
if __name__ == "__main__":
    run_once(MODE)
# Python Toggle.py