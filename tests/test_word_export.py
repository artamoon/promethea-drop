import subprocess
from pathlib import Path
from unittest.mock import patch
from promethea import convert


def test_word_timeout_falls_back_without_creating_partial_pdf(tmp_path):
    src=tmp_path/'test.docx'; src.write_bytes(b'dummy')
    out=tmp_path/'test.pdf'
    with patch('subprocess.run', side_effect=subprocess.TimeoutExpired('word', 20)):
        assert convert._word_to_pdf(src, out) is False
    assert not out.exists()


def test_word_failure_cannot_leave_output(tmp_path):
    src=tmp_path/'test.docx'; src.write_bytes(b'dummy')
    out=tmp_path/'test.pdf'
    def fail(args, **kwargs):
        Path(args[-1]).write_bytes(b'partial')
        return subprocess.CompletedProcess(args,1)
    with patch('subprocess.run', side_effect=fail):
        assert convert._word_to_pdf(src, out) is False
    assert not out.exists()
