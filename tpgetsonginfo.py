#TP SOUND FILES: gets beats, pitches, hanging notes of songs

from aubio import source, tempo
from numpy import median, diff

#This code was modified from
#https://github.com/aubio/aubio/blob/master/python/demos/demo_bpm_extract.py
#this gets beats of the song
def get_file_bpm(path, params=None):
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
            fileContents += (str(this_beat) + '\n')
            pitch = pitch_o(samples)[0]
            confidence = pitch_o.get_confidence()
            if confidence < 0.8: pitch = 0.
            beats.append(this_beat)
        total_frames += read
        if read < hop_s:
            break
    return fileContents

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
import aubio

#modified from https://github.com/aubio/aubio/blob/master/python/demos/demo_pitch.py
#detects pitches
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
        return pitches

def findHangingNotes(pitches):
    prevPitch = -1
    hangingNotesList = copy.deepcopy(pitches)
    streak = []
    for i in range(len(pitches)-2):
        if abs(pitches[i] - pitches[i+1]) <= 25 and (
            abs(pitches[i+1] - pitches[i+2]) <= 25):
            if pitches[i] > 300:
                if pitches[i] not in streak:
                    streak.append(pitches[i])
                if pitches[i+1] not in streak:
                    streak.append(pitches[i+1])
                if pitches[i+2] not in streak:
                    streak.append(pitches[i+2])   
    return streak

#returns pitches, beats, hanging notes lists
def getSongInfo(self,song):
    contentsToWrite = get_file_bpm(self.song)
    self.song.split(".")
    song = self.song[0]
    useSong = song + ".txt."
    writeFile(useSong, contentsToWrite)
    song = readFile(useSong)
    beats = song.split('\n')
    findLastLine = []
    contentsToWrite = detect('neversaynever.wav')
    self.song.split(".")
    song = self.song[0]
    useSong = song + "beats.txt."
    writeFile(useSong, contentsToWrite)
    pitches = contentsToWrite
    useSong = song + "hangingnotes.txt"
    hangingNotes = findHangingNotes(pitches)
    writeFile(useSong, hangingNotes)
