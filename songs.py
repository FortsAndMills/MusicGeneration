import mido
from mido import MidiFile
import numpy as np
import copy
import math

import matplotlib.pyplot as plt

# для возможности прослушивания midi прямо в ноутбуке
try:
	HEARING_PORT = mido.open_output()
except:
	pass
# для вывода массивов numpy целиком
np.set_printoptions(threshold=np.nan)

BASE_NOTE = 21  # номер нижней клавиши на реальной фортепианной клавиатуре
KEYS = 88       # клавиш на клавиатуре
FREQ = 4        # ticks for beat

# класс мидифайла песни
class Song:
    # Если в качестве name подана строка, то будет загружен миди файл с таким названием
    # Помимо строки может принимать массив, где числа от 0 до 88 соотв. нотам, иначе пауза    
    
    def __init__(self, data, finished=True, hold_mode=True):
        self.correct = True  # пометка о том, что файл загрузился без ошибок.
        self.hold_mode = hold_mode

        if isinstance(data, str):            
            self.name = data
            self.notes = np.zeros((32, KEYS), dtype=int)
            self.tempo_changes = 0
            
            # переводим в ноты
            try:
                self.mid = MidiFile(data)
            except:
                print(self.name, ": Error opening file with mido")
                self.correct = False
                return
                       
            for msg in self.mid:                
                if msg.type == 'time_signature':
                    if msg.denominator not in {2, 4, 8, 16} or msg.numerator not in {2, 4, 8, 16}:
                        print(self.name, ": Error: bad signature ", msg.numerator, '/', msg.denominator)
                        self.correct = False
                        return
                if msg.type == 'set_tempo':
                    self.tempo_changes += 1 
            
            data_tracks = set()
            for t_id, track in enumerate(self.mid.tracks):
                absolute_time_passed = 0
                pressed_keys = np.zeros((88))
                
                for msg in track:
                    absolute_time_passed += msg.time     
                    
                    key_on = (msg.type == "note_on" and msg.velocity > 0)
                    key_off = (msg.type == "note_off" or (msg.type == "note_on" and msg.velocity == 0))
                    if key_on or key_off:   
                        data_tracks.add(t_id)                     
                        t = round(absolute_time_passed * FREQ / self.mid.ticks_per_beat)

                        while t >= len(self.notes):
                            if self.hold_mode:
                                self.notes = np.vstack([self.notes, np.zeros((32, 88), dtype=int)])
                            else:
                                self.notes = np.vstack([self.notes, np.tile(self.notes[-1][None], (32, 1))])
                        
                        if (msg.note - BASE_NOTE < 0 or msg.note - BASE_NOTE >= 88):
                            print(self.name, ": ERROR: note out of range, ", msg.note, msg.note - BASE_NOTE)
                            self.correct=False
                            return
                        
                        if self.hold_mode:
                            self.notes[t, msg.note - BASE_NOTE] = msg.velocity*key_on
                        else:
                            self.notes[t:, msg.note - BASE_NOTE] = msg.velocity*key_on
            
            if len(data_tracks) > 2:
                print(self.name, ": Error: must be one (or two for two hands) track only")
                self.correct = False
                return
            
            self.notes = self.notes[self.notes.sum(axis=1).nonzero()[0][0]:]
        else:
            self.name = "Generated song!"
            self.notes = np.zeros((0, KEYS))

            self.mid = MidiFile(type=0)
            self.track = mido.MidiTrack()
            self.mid.tracks.append(self.track)

            self.time_passed = 0
            self.release = []

            for line in data:
                self.add(line)

            if finished:
                self.finish()

    # проиграть песню
    def play(self):
        for msg in self.mid.play():
            HEARING_PORT.send(msg)

    # транспонирование мелодии
    def transpose(self, shift):
        if (not self.correct or
                (shift > 0 and self.notes[:, -shift:].sum() != 0) or
                (shift < 0 and self.notes[:, :-shift].sum() != 0)):
            return False

        self.notes = np.hstack([self.notes[:, -shift:], self.notes[:, :-shift]])
        return True
    
    def drawSong(song, scale=(None, None)):
        if scale[0] is None:
            scale = (song.notes.shape[0] / 10, song.notes.shape[1] / 10)

        plt.figure(figsize=scale)
        plt.title(song.name)
        plt.imshow(song.notes.T, aspect='auto', origin='lower')
        plt.xlabel("time")
        plt.xticks(np.arange(0, song.notes.shape[0], 4))
        plt.show()

    # добавление новых строк в ноты
    def add(self, played):
        self.notes = np.vstack([self.notes, played])

        # "отпуск" нот, сыгранных долю назад
        if self.hold_mode and played.sum() > 0:
            for i in self.release:
                self.track.append(mido.Message('note_on', note=BASE_NOTE + i, velocity=0, time=self.time_passed))
                self.time_passed = 0
            self.release = []

        # добавление новых нот
        for i, key in enumerate(played):
            if key > 0:
                if i not in self.release:
                    self.track.append(mido.Message('note_on', note=BASE_NOTE + i, velocity=key, time=self.time_passed))
                    self.time_passed = 0
                    self.release.append(i)
            elif not self.hold_mode and i in self.release:
                self.track.append(mido.Message('note_on', note=BASE_NOTE + i, velocity=0, time=self.time_passed))
                self.time_passed = 0
                self.release.remove(i)
                
        self.time_passed += self.mid.ticks_per_beat // FREQ

    # должна быть вызвана в конце создания файла
    def finish(self):
        for i in self.release:
            self.track.append(mido.Message('note_off', note=BASE_NOTE + i, velocity=64, time=self.time_passed))
            self.time_passed = 0
        self.track.append(mido.Message('note_off', note=BASE_NOTE, velocity=0, time=self.time_passed))

    # сохранение
    def save_file(self, name):
        self.mid.save(name + '.mid')
