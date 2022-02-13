from c2f.audio_editor import convert_and_clip

def test_convert_and_clip():
    with open('wav-test-input.wav', 'rb') as input_file:
        clip_off = 2500
        convert_and_clip(input_file, 'wav-test-output.mp3', clip_off)
        #assert _do_cmp('wav-test-output.mp3')


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
