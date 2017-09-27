import mido
from mido import MidiFile
import numpy as np
import copy

# для возможности прослушивания midi прямо в ноутбуке
HEARING_PORT = mido.open_output()
# для вывода массивов numpy целиком
np.set_printoptions(threshold=np.nan)

# класс мидифайла песни
class Song:
    # Если в качестве name подана строка, то будет загружен миди файл с таким названием
    # Если есть выход за рамки диапазона, то песня будет сдвинута (умное слово - транспонирована)
    # Если такой возможности нет, песня будет помечена как некорректная, и нот в ней не будет

    # Помимо строки может принимать массив, где числа от 0 до 12 соотв. нотам, иначе пауза

    def __init__(self, name):
        self.name = name
        self.correct = True
        self.notes = np.zeros((128, 13), dtype=int)

        if isinstance(name, str):
            # проверка на то, что песня попадает в диапазон
            maxnote = 0
            minnote = 127
            for msg in MidiFile(name):
                if (msg.type == "note_on" and msg.velocity > 0):
                    if msg.note < minnote:
                        minnote = msg.note
                    if msg.note > maxnote:
                        maxnote = msg.note

            # случай некорректного файла
            if maxnote - minnote >= 13:
                print("ERROR! out of range!")
                self.correct = False
                return

            # вычисляем необходимый сдвиг
            shift = 0
            if minnote < 60:
                shift = 60 - minnote
            if maxnote >= 60 + 13:
                shift = 60 + 13 - 1 - maxnote

            # переводим в ноты
            absolute_time_passed = 0
            for msg in MidiFile(name):
                absolute_time_passed += msg.time

                if (msg.type == "note_on" and msg.velocity > 0):
                    self.notes[round(absolute_time_passed / 0.25)][msg.note - 60 + shift] = 1
        else:
            # парсим "массив нот"
            for i, note in enumerate(name):
                if note >= 0 and note < 13:
                    self.notes[i][note] = 1

    # проиграть песню
    def play(self):
        for msg in MidiFile(self.name).play():
            HEARING_PORT.send(msg)

    # транспонирование мелодии
    def transpose(self, shift):
        if (not self.correct or
                (shift > 0 and self.notes[:, -shift:].sum() != 0) or
                (shift < 0 and self.notes[:, :-shift].sum() != 0)):
            return False

        self.notes = np.hstack([self.notes[:, -shift:], self.notes[:, :-shift]])
        return True

# Класс для создания нового миди файла
class MySong:
    def __init__(self, played_lines=[]):
        self.notes = np.zeros((0, 13))

        self.mid = MidiFile()
        self.track = mido.MidiTrack()
        self.mid.tracks.append(self.track)

        self.time_passed = 0
        self.release = []

        for line in played_lines:
            self.add(line)

    # добавление новых строк в ноты
    def add(self, played):
        self.notes = np.vstack([self.notes, played])

        # "отпуск" нот, сыгранных долю назад
        for i in self.release:
            self.track.append(mido.Message('note_off', note=60 + i, velocity=64, time=self.time_passed))
            self.time_passed = 0
        self.release = []

        # добавление новых нот
        for i, key in enumerate(played):
            if key == 1:
                self.track.append(mido.Message('note_on', note=60 + i, velocity=64, time=self.time_passed))
                self.time_passed = 0
                self.release.append(i)
        self.time_passed += 256

    # должна быть вызвана в конце создания файла
    def finish(self):
        for i in self.release:
            self.track.append(mido.Message('note_off', note=60 + i, velocity=64, time=self.time_passed))
            self.time_passed = 0
        self.track.append(mido.Message('note_off', note=60, velocity=0, time=self.time_passed))

    # воспроизведение
    def play(self):
        for msg in self.mid.play():
            HEARING_PORT.send(msg)

    # сохранение
    def save_file(self, name):
        self.mid.save(name + '.mid')