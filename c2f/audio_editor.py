from pydub import AudioSegment

def convert_and_clip(wave_file, destination, skip_ms):
    original = AudioSegment.from_file(wave_file, format="wav")
    clipped = original[skip_ms:]
    clipped.export(destination, format="mp3")
