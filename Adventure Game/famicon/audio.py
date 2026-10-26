"""Chiptune sound effects and music, synthesised at start-up (no audio files)."""
import array
import random
import threading

import pygame

SFX = {  # name: [(start_hz, end_hz, seconds, wave, volume), ...] played back to back
    "sword": [(900, 300, 0.09, "noise", 0.22)], "beam": [(1300, 500, 0.16, "square", 0.16)],
    "hurt": [(300, 120, 0.22, "square", 0.25)], "hit": [(500, 180, 0.08, "noise", 0.25)],
    "kill": [(700, 100, 0.2, "noise", 0.25)], "clink": [(1800, 1400, 0.05, "square", 0.14)],
    "pickup": [(880, 1320, 0.07, "square", 0.16), (1320, 1760, 0.07, "square", 0.16)],
    "heart": [(660, 880, 0.08, "square", 0.18), (880, 1100, 0.1, "square", 0.18)],
    "key": [(988, 988, 0.06, "square", 0.18), (1319, 1319, 0.12, "square", 0.18)],
    "item": [(523, 523, 0.1, "square", 0.2), (659, 659, 0.1, "square", 0.2), (784, 784, 0.1, "square", 0.2),
             (1047, 1047, 0.3, "square", 0.2)],
    "door": [(200, 90, 0.18, "noise", 0.22)], "bomb_set": [(300, 300, 0.05, "square", 0.15)],
    "explosion": [(240, 40, 0.5, "noise", 0.35)], "boomerang": [(600, 800, 0.06, "square", 0.12)] * 3,
    "arrow": [(1100, 500, 0.1, "square", 0.14)], "heal": [(440, 880, 0.12, "square", 0.16)] * 3,
    "cut": [(700, 400, 0.07, "noise", 0.18)], "secret": [(784, 784, 0.08, "square", 0.18), (988, 988, 0.08, "square", 0.18),
                                                          (1175, 1175, 0.08, "square", 0.18), (1568, 1568, 0.2, "square", 0.18)],
    "rumble": [(90, 60, 0.35, "noise", 0.3)], "text": [(1000, 1000, 0.02, "square", 0.06)],
    "error": [(200, 200, 0.12, "square", 0.18)], "boss_hit": [(320, 100, 0.16, "noise", 0.3)],
    "boss_die": [(400, 50, 0.9, "noise", 0.35)], "die": [(500, 100, 0.8, "square", 0.22)],
    "fall": [(600, 100, 0.4, "square", 0.2)], "select": [(1200, 1200, 0.03, "square", 0.1)],
    "stairs": [(500, 250, 0.3, "square", 0.15)],
}

NOTES = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def hz(note):
    if note.startswith("-"):
        return 0.0
    n = NOTES[note[0]]
    i = 1
    if note[i] in "#b":
        n += 1 if note[i] == "#" else -1
        i += 1
    return 440.0 * 2 ** ((n + 12 * (int(note[i:]) + 1) - 69) / 12)


def tone(f0, f1, seconds, wave, volume, rate, rng=random):
    count = max(1, int(seconds * rate))
    out, phase = [], 0.0
    for i in range(count):
        t = i / count
        phase += (f0 + (f1 - f0) * t) / rate
        if wave == "noise":
            v = rng.uniform(-1, 1)
        elif wave == "tri":
            v = 4 * abs(phase % 1 - 0.5) - 1
        else:
            v = 1.0 if phase % 1 < 0.5 else -1.0
        out.append(v * volume * (1 - t) ** 1.5)
    return out


def voice(wave, volume, pattern, step, rate):
    out = []
    for tok in pattern.split():
        name, steps = tok.split(":")
        seconds = int(steps) * step
        f = hz(name)
        if f == 0:
            out.extend([0.0] * int(seconds * rate))
            continue
        n = int(seconds * rate)
        phase, vals = 0.0, []
        for i in range(n):
            phase += f / rate
            v = (1.0 if phase % 1 < 0.5 else -1.0) if wave == "square" else 4 * abs(phase % 1 - 0.5) - 1
            env = min(1.0, i / 60) * (1 - 0.35 * i / max(1, n))
            vals.append(v * volume * env)
        out.extend(vals)
    return out


MUSIC = {  # bpm, then (wave, volume, pattern) voices; durations are in sixteenth notes
    "overworld": (132, [
        ("square", 0.13, "E5:4 E5:2 D5:2 C5:4 G4:4 A4:4 A4:2 B4:2 C5:4 E5:4 G5:4 G5:2 F5:2 E5:4 C5:4 D5:4 E5:4 D5:4 G4:4"),
        ("tri", 0.2, "C3:4 G2:4 C3:4 G2:4 A2:4 E3:4 A2:4 E3:4 F2:4 C3:4 F2:4 C3:4 G2:4 D3:4 G2:4 D3:4")]),
    "dungeon": (100, [
        ("square", 0.1, "A3:4 -:4 C4:4 -:4 B3:4 -:4 E4:4 -:4 A3:4 -:4 F4:4 -:4 E4:8 D#4:8"),
        ("tri", 0.22, "A1:8 A1:8 G1:8 G1:8 F1:8 F1:8 E1:8 E1:8")]),
    "boss": (168, [
        ("square", 0.12, "A4:2 A4:2 C5:2 A4:2 E5:2 A4:2 D5:2 A4:2 A4:2 A4:2 C5:2 A4:2 G5:2 A4:2 F5:2 E5:2 "
                         "F4:2 F4:2 A4:2 F4:2 C5:2 F4:2 B4:2 F4:2 E4:2 E4:2 G#4:2 E4:2 B4:2 E4:2 A4:4"),
        ("tri", 0.22, "A2:2 A2:2 A2:2 A2:2 A2:2 A2:2 A2:2 A2:2 A2:2 A2:2 A2:2 A2:2 A2:2 A2:2 A2:2 A2:2 "
                      "F2:2 F2:2 F2:2 F2:2 F2:2 F2:2 F2:2 F2:2 E2:2 E2:2 E2:2 E2:2 E2:2 E2:2 E2:2 E2:2")]),
    "cave": (80, [
        ("tri", 0.2, "C4:8 G4:8 E4:8 D4:8 C4:8 A3:8 G3:16"),
        ("square", 0.05, "-:16 E5:4 -:12 -:16 D5:4 -:12")]),
    "title": (96, [
        ("square", 0.1, "A4:4 C5:4 E5:4 A5:4 G5:4 E5:4 C5:4 E5:4 F4:4 A4:4 C5:4 F5:4 E5:4 C5:4 A4:4 C5:4"),
        ("tri", 0.2, "A2:16 F2:16")]),
    "victory": (120, [
        ("square", 0.13, "C5:4 E5:4 G5:4 C6:8 B5:4 G5:4 A5:4 C6:8 G5:4 E5:4 G5:4 C6:16"),
        ("tri", 0.22, "C3:16 G2:8 A2:8 F2:16 C3:16")]),
}


def to_pcm(samples, channels):
    pcm = array.array("h")
    for v in samples:
        s = max(-32768, min(32767, int(v * 32767)))
        pcm.extend([s] * channels)
    return pcm


def render_sfx(name, rate):
    out = []
    for seg in SFX[name]:
        out.extend(tone(*seg[:4], seg[4], rate))
    return out


def render_music(name, rate):
    bpm, voices = MUSIC[name]
    step = 60.0 / bpm / 4
    tracks = [voice(w, v, p, step, rate) for w, v, p in voices]
    length = max(len(t) for t in tracks)
    mix = [0.0] * length
    for t in tracks:
        for i, v in enumerate(t):
            mix[i] += v
    return mix


class Audio:
    def __init__(self, enabled=True):
        self.ok = False
        self.sfx, self.tracks = {}, {}
        self.current = self.wanted = None
        self.channel = None
        if not enabled:
            return
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(22050, -16, 1, 512)
            self.rate, _, self.channels = pygame.mixer.get_init()
            self.ok = True
        except pygame.error:
            return
        threading.Thread(target=self._build, daemon=True).start()

    def _build(self):
        for name in SFX:
            self.sfx[name] = pygame.mixer.Sound(buffer=to_pcm(render_sfx(name, self.rate), self.channels).tobytes())
        for name in MUSIC:
            snd = pygame.mixer.Sound(buffer=to_pcm(render_music(name, self.rate), self.channels).tobytes())
            snd.set_volume(0.6)
            self.tracks[name] = snd
            if self.wanted == name:
                self._start(name)

    def _start(self, name):
        if self.channel:
            self.channel.stop()
        self.channel = self.tracks[name].play(loops=-1)
        self.current = name

    def play(self, name):
        if self.ok and name in self.sfx:
            self.sfx[name].play()

    def music(self, name):
        if not self.ok or name == self.wanted:
            return
        self.wanted = name
        if name is None:
            if self.channel:
                self.channel.stop()
            self.current = None
        elif name in self.tracks:
            self._start(name)
