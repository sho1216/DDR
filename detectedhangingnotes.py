###########################################################################
######################### Playing a WAV file ##############################
###########################################################################
import copy, pyaudio, wave, aubio
#Code modified from https://people.csail.mit.edu/hubert/pyaudio/
from array import array
from struct import pack
from aubio import source, tempo
from numpy import median, diff

#basic read, write, play audio file functions
def play(file):
    CHUNK = 1024 #measured in bytes
    wf = wave.open(file, 'rb')
    p = pyaudio.PyAudio()
    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True)
    data = wf.readframes(CHUNK)
    while len(data) > 0:
        stream.write(data)
        data = wf.readframes(CHUNK)
    stream.stop_stream()
    stream.close()
    p.terminate()

def readFile(path):
    with open(path, "rt") as f:
        return f.read()

def writeFile(path, contents):
    with open(path, "wt") as f:
        f.write(contents)

#modified from https://github.com/aubio/aubio/blob/master/python/demos/demo_pitch.py
def detect(filename):
        downsample = 8
        samplerate = int(44100 / downsample)
        win_s = int(4096 / downsample) # fft size
        hop_s = int(512  / downsample) # hop size
        s = aubio.source(filename, samplerate, hop_s)
        samplerate = s.samplerate
        tolerance = 0.8
        pitch_o = aubio.pitch("yin", win_s, hop_s, samplerate)
        pitch_o.set_unit("freq")
        pitch_o.set_tolerance(tolerance)
        pitches = []
        confidences = []
        # total number of frames read
        total_frames = 0
        counter = 0
        while True:
            samples, read = s()
            pitch = pitch_o(samples)[0]
            confidence = pitch_o.get_confidence()
            pitches += [pitch]
            confidences += [confidence]
            total_frames += read
            if read < hop_s: break
        return beats, pitches
    
#calculate the beats per minute (bpm) given path: path to the file
#and param: dictionary of parameters
def returnBeatsPitches(path, params=None):
    beats = []
    pitches = ''
    fileContents = ''
    if params is None:
        params = {}
    # default:
    samplerate, win_s, hop_s = 44100, 1024, 512
    if 'mode' in params:
        if params.mode in ['super-fast']:
            # super fast
            samplerate, win_s, hop_s = 4000, 128, 64
        elif params.mode in ['fast']:
            # fast
            samplerate, win_s, hop_s = 8000, 512, 128
        elif params.mode in ['default']:
            pass
        else:
            raise ValueError("unknown mode {:s}".format(params.mode))
    # manual settings
    if 'samplerate' in params:
        samplerate = params.samplerate
    if 'win_s' in params:
        win_s = params.win_s
    if 'hop_s' in params:
        hop_s = params.hop_s
    s = source(path, samplerate, hop_s)
    samplerate = s.samplerate
    o = tempo("specdiff", win_s, hop_s, samplerate)
    # List of beats, in samples
    beats = []
    # Total number of frames read
    total_frames = 0
    pitch_o = aubio.pitch("yin", win_s, hop_s, samplerate)
    pitch_o.set_unit("freq")
    tolerance = 0.8
    pitch_o.set_tolerance(tolerance)
    while True:
        samples, read = s()
        is_beat = o(samples)
        if is_beat:
            this_beat = o.get_last_s()
            beats.append(str(this_beat))
            pitch = pitch_o(samples)[0]
            confidence = pitch_o.get_confidence()
            pitches += (str(pitch) + '\n')
        total_frames += read
        if read < hop_s:
            break
    return pitches

#example for demo with Never Say Never 
res = returnBeatsPitches('neversaynever.wav')
writeFile('pitches.txt',res)

#find longer notes that are held in a song
def findHangingNotes(pitches):
    prevPitch = -1
    hangingNotesList = copy.deepcopy(pitches)
    streak = []
    writeStreak = ''   
    for i in range(len(pitches)-2):
        if abs(pitches[i] - pitches[i+1]) <= 25 and (
            abs(pitches[i+1] - pitches[i+2]) <= 25):
            if pitches[i] > 300:
                if pitches[i] not in streak:
                    streak.append(pitches[i])
                    writeStreak += str(pitches[i]) + '\n'
                if pitches[i+1] not in streak:
                    streak.append(pitches[i+1])
                    writeStreak += str(pitches[i+1]) + '\n'
                if pitches[i+2] not in streak:
                    streak.append(pitches[i+2])
                    writeStreak += str(pitches[i+2]) + '\n'
    return writeStreak

#example for demo with Never Say Never 
streak = (findHangingNotes(pitches))
writeFile('hangingnotes.txt',streak)
