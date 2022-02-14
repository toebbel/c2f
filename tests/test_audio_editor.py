from c2f.audio_editor import convert_and_clip

def test_convert_and_clip():
    clip_off = 2500
    convert_and_clip('tests/wav-test-input.wav', 'tests/test-actual-output.mp3', clip_off)
    # MP3s could differ on byte comparison when they were decoded on different machines (of ffmpeg versions)
    # If the test proves to be flaky, it should be removed.
    assert _do_cmp('tests/test-actual-output.mp3', 'tests/test-expected-output.mp3')


# taken from here: https://codereview.stackexchange.com/a/171014
def _do_cmp(f1, f2):
    bufsize = 1 # byte wise comparison
    with open(f1, 'rb') as fp1, open(f2, 'rb') as fp2:
        while True:
            b1 = fp1.read(bufsize)
            b2 = fp2.read(bufsize)
            if b1 != b2:
                return False
            if not b1:
                return True
