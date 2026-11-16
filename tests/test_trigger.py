"""Срабатывание только там, где действительно тянут файл."""
from __future__ import annotations

from promethea.trigger import is_file_window


def test_explorer_and_desktop_classes_are_allowed():
    for cls in ("CabinetWClass", "ExploreWClass", "Progman", "WorkerW"):
        assert is_file_window(cls), cls


def test_app_canvases_are_rejected():
    assert not is_file_window("Chrome_WidgetWin_1", "Figma.exe")
    assert not is_file_window("Photoshop", "Photoshop.exe")
    assert not is_file_window("Qt5152QWindowIcon", "python.exe")


def test_process_name_fallback():
    assert is_file_window("SomeShellClass", "explorer.exe")
    assert is_file_window("", "EXPLORER.EXE")
    assert not is_file_window("", "")


def test_class_wins_over_unrelated_process():
    assert is_file_window("CabinetWClass", "")
