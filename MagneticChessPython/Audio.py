"""
Able to play audio and text to speech
"""

import pyttsx3 as tts
from slugify import slugify
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide" # Hide pygame welcome message
from pygame import mixer
from threading import Thread

import time

BASE_AUDIO_PATH = '../audio/'
BASE_TTS_PATH = BASE_AUDIO_PATH + 'TextToSpeech/'

AUDIO_WPM = 150

NON_TTS_AUDIO = {
    'boot': 'Windows XP Startup.wav',
    'move': 'move-self.wav',
    'check': 'move-check.wav',
    'capture': 'capture.wav',
    'castle': 'castle.wav',
    'promote': 'promote.wav',
    'illegal': 'illegal.wav',
    'gamestart': 'game-start.wav',
    'gameend': 'game-end.wav',
}

MAX_CHANNELS = 8

class Audio:
    def __init__(self):
        self.mixer = mixer
        #self.mixer.pre_init(24000) # Configure smaple rate to 24000 Hz (to make gTTS sound better)
        self.mixer.init()
        self.mixer.set_num_channels(MAX_CHANNELS)

        self.engine = None

        self.thread = Thread(target=self.__startEngine)
        self.thread.daemon = True
        self.thread.start()

        self.sounds = {}
        for key, filename in NON_TTS_AUDIO.items():
            self.sounds[key] = self.mixer.Sound(BASE_AUDIO_PATH + filename)
    
    def __del__(self):
        self.engine.endLoop()
        self.engine.stop()
        self.mixer.quit()

    def __startEngine(self):
        global stop_threads
        # start engine loop in its own thread
        self.engine = tts.init()
        self.engine.setProperty('rate', AUDIO_WPM) # Set speed of speech in wpm
        self.engine.setProperty('voice', 'english-us')
        self.engine.setProperty('volume', 1.0) # Volume
        self.engine.startLoop(False)
        while True:
            time.sleep(0.1)
            self.engine.iterate()

    def __getIdleChannel(self):
        for i in range(1, 8):
            if not self.mixer.Channel(i).get_busy():
                return self.mixer.Channel(i)
        return None
    
    def __playSoundObject(self, soundObject):
        idleChannel = self.__getIdleChannel()
        if idleChannel:
            idleChannel.play(soundObject)
        else:
            print("Tried to play sound, but all channels are busy.")

    def playSound(self, sound):
        if sound not in self.sounds:
            print("Sound not found: '" + sound + "'")
            return
        
        self.__playSoundObject(self.sounds[sound])

    def playTTS(self, text):
        if not text:
            return
        
        start_time = time.time()
        self.engine.say(text)

        after_play = time.time()
        print("Time to play: " + str(after_play - start_time))

    def stopAllSounds(self):
        self.mixer.stop()
