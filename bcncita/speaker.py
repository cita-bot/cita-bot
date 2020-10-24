import os
from shutil import which


class eSpeakSpeaker:
    @classmethod
    def is_applicable(cls):
        return which("espeak") is not None

    def say(self, phrase):
        os.system("espeak '" + phrase + "'")


class saySpeaker:
    @classmethod
    def is_applicable(cls):
        return which("say") is not None

    def say(self, phrase):
        os.system("say '" + phrase + "'")


class wSaySpeaker:
    @classmethod
    def is_applicable(cls):
        return which("wsay") is not None

    def say(self, phrase):
        os.system('wsay "' + phrase + '"')


def new_speaker():
    for cls in [eSpeakSpeaker, saySpeaker, wSaySpeaker]:
        if cls.is_applicable():
            return cls()
    raise ValueError("Platform is not supported")
