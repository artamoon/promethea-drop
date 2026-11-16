import subprocess, wave
from pathlib import Path
import pytest
from promethea import convert, media
from promethea.util import UserError, category

@pytest.fixture
def audio(tmp_path):
    path=tmp_path/'sample.wav'
    with wave.open(str(path),'wb') as out:
        out.setnchannels(1); out.setsampwidth(2); out.setframerate(16000); out.writeframes(b'\x00\x00' * 16000)
    return path

@pytest.mark.parametrize('target', ['MP3','OGG','OPUS','M4A','FLAC'])
def test_audio_conversion(audio,target):
    before=audio.read_bytes()
    out=media.convert(audio,'audio',target)[0]
    assert out.exists() and out.stat().st_size>100
    assert audio.read_bytes()==before
    proc=subprocess.run([media.ffmpeg_path(),'-v','error','-i',str(out),'-f','null','-'],capture_output=True)
    assert proc.returncode == 0, proc.stderr.decode(errors='replace')


def test_video_conversions_and_missing_audio(tmp_path):
    src=tmp_path/'sample.mov'
    result=subprocess.run([media.ffmpeg_path(),'-v','error','-f','lavfi','-i','testsrc=size=64x64:rate=5', '-f','lavfi','-i','sine=frequency=440:sample_rate=16000','-t','1','-c:v','mpeg4','-c:a','aac','-y',str(src)],capture_output=True)
    assert result.returncode==0, result.stderr.decode(errors='replace')
    original=src.read_bytes()
    for target in ['MP3','WAV','GIF','MP4']:
        out=media.convert(src,'video',target)[0]
        check=subprocess.run([media.ffmpeg_path(),'-v','error','-i',str(out),'-f','null','-'],capture_output=True)
        assert check.returncode==0, check.stderr.decode(errors='replace')
    assert src.read_bytes()==original
    silent=tmp_path/'silent.mov'
    result=subprocess.run([media.ffmpeg_path(),'-v','error','-f','lavfi','-i','testsrc=size=64x64:rate=5','-t','1','-c:v','mpeg4','-y',str(silent)],capture_output=True)
    assert result.returncode==0
    with pytest.raises(UserError,match='track'):
        media.convert(silent,'video','MP3')
    assert not (tmp_path/'silent.mp3').exists()


def test_formats_and_menu_targets():
    assert category('music.m4a')=='audio'
    assert category('clip.mov')=='video'
    assert 'MP3' in convert.targets_for('audio','.m4a')
    assert 'MP4' in convert.targets_for('video','.mov')
    assert 'MP4' not in convert.targets_for('video','.mp4')


def test_requested_audio_directions(audio):
    originals = {ext: media.convert(audio, 'audio', ext)[0] for ext in ('MP3', 'M4A', 'OGG', 'OPUS')}
    for source, target in [('M4A','MP3'), ('OGG','MP3'), ('OPUS','MP3'), ('MP3','WAV'), ('MP3','OGG')]:
        output = media.convert(originals[source], 'audio', target)[0]
        result = subprocess.run([media.ffmpeg_path(), '-v', 'error', '-i', str(output), '-f', 'null', '-'], capture_output=True)
        assert result.returncode == 0, result.stderr.decode(errors='replace')
