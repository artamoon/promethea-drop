from pathlib import Path
from unittest.mock import patch

from PySide6.QtCore import QPoint
from PySide6.QtWidgets import QApplication

from promethea import toasts, trigger


def test_undo_preserves_files_when_trash_fails(tmp_path):
    ok, failed = tmp_path / "ok.txt", tmp_path / "failed.txt"
    ok.write_text("ok")
    failed.write_text("keep")
    with patch.object(toasts.QFile, "moveToTrash", side_effect=lambda p: p == str(ok)):
        moved, remaining = toasts.trash([ok, failed])
    assert moved == [ok]
    assert remaining == [failed]
    assert failed.read_text() == "keep"
    assert tmp_path.exists()


def test_undo_partial_failure_remains_retryable(tmp_path):
    app = QApplication.instance() or QApplication([])
    card = toasts.ToastCard(None)
    from promethea.report import Result
    first, second = tmp_path / "first", tmp_path / "second"
    first.touch()
    second.touch()
    card.done(Result("Done", "", [first, second]))
    with patch.object(toasts.QFile, "moveToTrash", side_effect=[True, False]):
        card._act("Undo")
    assert card.title == "Undo incomplete"
    assert card.result.outs == [second]
    assert second.exists()
    card.close()


def test_menu_times_out_without_pointer_motion():
    app = QApplication.instance() or QApplication([])
    watcher = trigger.PrometheaWatcher(lambda: True, lambda: False)
    watcher._state = lambda: (True, False, False)
    hidden = []
    watcher.hide_menu.connect(lambda: hidden.append(True))
    with patch.object(trigger.QCursor, "pos", return_value=QPoint(0, 0)):
        for _ in range(trigger.NO_DRAG_TIMEOUT + 1):
            watcher._tick()
    assert hidden


def test_file_drag_opens_switches_and_closes_menu():
    from PySide6.QtTest import QTest
    app = QApplication.instance() or QApplication([])
    state = {'visible': False, 'drag': False, 'keys': (True, False, False), 'pos': QPoint(100, 100)}
    watcher = trigger.PrometheaWatcher(lambda: state['visible'], lambda: state['drag'])
    watcher._state = lambda: state['keys']
    watcher._file_context = lambda: True
    events = []
    def show(pos):
        events.append('show'); state['visible'] = True
    watcher.show_menu.connect(show)
    watcher.toggle_ring.connect(lambda: events.append('toggle'))
    watcher.hide_menu.connect(lambda: events.append('hide'))
    with patch.object(trigger.QCursor, 'pos', side_effect=lambda: state['pos']):
        watcher._tick()
        state.update(keys=(True, True, False), pos=QPoint(120, 100))
        watcher._tick()
        assert events == ['show']
        state.update(drag=True, keys=(True, False, False))
        watcher._tick()
        state['keys'] = (True, True, False)
        watcher._tick()
        assert events == ['show', 'toggle']
        state['keys'] = (False, False, False)
        watcher._tick()
        QTest.qWait(180)
    assert events == ['show', 'toggle', 'hide']


def test_file_drop_reaches_selected_action(tmp_path):
    from PySide6.QtCore import QMimeData, QPointF, QUrl, Qt
    from PySide6.QtGui import QDragEnterEvent, QDropEvent
    from PySide6.QtTest import QTest
    from promethea.radial import Item, RadialMenu
    app = QApplication.instance() or QApplication([])
    src = tmp_path / 'input.png'
    src.write_bytes(b'example')
    item = Item('JPG', key='convert:JPG')
    menu = RadialMenu(lambda paths: {'Convert': [item]}, lambda paths: 'test')
    mime = QMimeData()
    mime.setUrls([QUrl.fromLocalFile(str(src))])
    enter = QDragEnterEvent(QPoint(200, 100), Qt.CopyAction | Qt.MoveAction, mime, Qt.LeftButton, Qt.ShiftModifier)
    menu.dragEnterEvent(enter)
    assert enter.isAccepted() and enter.dropAction() == Qt.CopyAction
    triggered = []
    menu.activated.connect(lambda selected, paths: triggered.append((selected.key, paths)))
    drop = QDropEvent(QPointF(200, 100), Qt.CopyAction | Qt.MoveAction, mime, Qt.LeftButton, Qt.ShiftModifier)
    menu.dropEvent(drop)
    QTest.qWait(30)
    assert drop.isAccepted() and drop.dropAction() == Qt.CopyAction
    assert len(triggered) == 1 and triggered[0][0] == 'convert:JPG'
    assert [Path(p) for p in triggered[0][1]] == [src]
    assert src.read_bytes() == b'example'
