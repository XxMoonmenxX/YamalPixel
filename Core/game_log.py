"""Bounded incremental reader of the current Java console; never pipes Java."""
import codecs
import re
from pathlib import Path

from Core.bugreport import redact


class GameLogReader:
    def __init__(self, path):
        self.path = Path(path)
        self.offset = 0
        self.at_end = False
        self.decoder = codecs.getincrementaldecoder('utf-8')('replace')

    def read(self):
        try:
            size = self.path.stat().st_size
            if size < self.offset:
                self.offset = 0
                self.decoder.reset()
            with self.path.open('rb') as source:
                source.seek(self.offset)
                data = source.read(65536)
                self.offset = source.tell()
                self.at_end = self.offset >= size
            return redact(self.decoder.decode(data))
        except OSError:
            self.at_end = True
            return ''


def loading_stage(text):
    """Only name observed stages; Minecraft has no universal progress percentage."""
    stages = (
        (r'Loading \d+ mods|Loading Minecraft|ModLauncher running|Fabric Loader', 'Загрузка Minecraft и модов'),
        (r'mixin|Initializing mods|Initializing.*mod', 'Инициализация модов'),
        (r'Backend library|LWJGL|OpenGL', 'Подготовка графики'),
        (r'Reloading ResourceManager|Reloading.*resources', 'Загрузка ресурсов'),
        (r'Created:.*atlas|Stitching.*atlas', 'Подготовка текстур'),
        (r'OpenAL initialized|Sound engine started', 'Загрузка звука'),
        (r'Connecting to ', 'Подключение к серверу'),
        (r'Loaded \d+ advancements|Preparing spawn area', 'Загрузка мира'),
    )
    observed = []
    for pattern, label in stages:
        for match in re.finditer(pattern, text, re.I):
            observed.append((match.start(), label))
    return max(observed)[1] if observed else None
