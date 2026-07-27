from mutagen import File
from pprint import pprint

audio = File(r"C:\PythonScripts\CoverFetch\InputMusic\Sex On Fire (Arcando Remix).aiff", easy=True)

print(type(audio))
print(audio.tags)

print("\nFrames:")
for key, value in audio.tags.items():
    print(key, "->", value)

print("\nKeys:")
print(audio.keys())