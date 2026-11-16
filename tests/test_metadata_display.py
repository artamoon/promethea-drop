from PIL import Image, PngImagePlugin
from PySide6.QtWidgets import QApplication, QTableWidget
from promethea import imaging
from promethea.tools import MetadataWindow


def test_image_details_and_untruncated_metadata(tmp_path):
    path = tmp_path / "example.png"
    meta = PngImagePlugin.PngInfo()
    meta.add_text("Description", "A" * 200)
    Image.new("RGB", (120, 80)).save(path, pnginfo=meta, dpi=(300, 300))
    details = imaging.read_image_metadata(path)
    summary = imaging.metadata_summary(path)
    assert details["Description"] == "A" * 200
    assert details["Dimensions"] == "120 × 80 px"
    assert summary["File"].startswith("PNG · ")
    assert "dpi" in summary["Resolution"]


def test_metadata_window_shows_basic_fields_without_exif(tmp_path):
    app = QApplication.instance() or QApplication([])
    path = tmp_path / "plain.png"
    Image.new("RGB", (20, 10)).save(path)
    window = MetadataWindow(path, lambda *args: None)
    info = imaging.read_image_metadata(path)
    assert window.n_fields == 0
    assert window.toggle.isEnabled()
    assert window.toggle.text() == f"Show all {len(info)} fields"
    window.toggle.click()
    assert window.toggle.text() == "Hide fields"
    assert window.findChild(QTableWidget).rowCount() == len(info)
    window.close()
