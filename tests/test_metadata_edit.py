import pytest
from PIL import Image, PngImagePlugin
from promethea import metadata_edit
from promethea.convert import fitz
from promethea.util import UserError

@pytest.mark.parametrize("ext", [".jpg", ".png"])
def test_edit_preserves_original_image_and_metadata(tmp_path, ext):
    path = tmp_path / ("image" + ext)
    image = Image.new("RGB", (30, 20), "red")
    exif = Image.Exif()
    exif[0x010F] = "Camera maker"
    exif[0x8825] = {1: "N", 2: (24.0, 33.0, 18.0), 3: "W", 4: (81.0, 47.0, 0.0)}
    image.save(path, exif=exif)
    before = path.read_bytes()
    with Image.open(path) as src:
        pixels = src.tobytes()
        gps = src.getexif().get_ifd(0x8825)
    out = metadata_edit.write_fields(path, False, {"Title": "Название", "Author": "Автор", "Created": "2024-03-21 12:34:56"})
    assert path.read_bytes() == before
    with Image.open(out) as result:
        assert result.tobytes() == pixels
        assert result.getexif()[0x010F] == "Camera maker"
        assert result.getexif().get_ifd(0x8825) == gps
    data = metadata_edit.read_fields(out, False)
    assert data["Title"] == "Название"
    assert data["Author"] == "Автор"
    assert data["Created"] == "2024-03-21 12:34:56"


def test_pdf_edits_keep_other_metadata_and_original(tmp_path):
    path = tmp_path / "document.pdf"
    doc = fitz.open(); doc.new_page(); doc.set_metadata({"title": "Old", "keywords": "keep"}); doc.save(path); doc.close()
    original = path.read_bytes()
    out = metadata_edit.write_fields(path, True, {"Title": "New", "Created": "2024-03-21 12:34:56"})
    assert path.read_bytes() == original
    with fitz.open(out) as result:
        assert result.page_count == 1
        assert result.metadata["title"] == "New"
        assert result.metadata["keywords"] == "keep"
    assert metadata_edit.read_fields(out, True)["Created"] == "2024-03-21 12:34:56"


def test_rejects_invalid_date_and_xmp_without_creating_copy(tmp_path):
    path = tmp_path / "image.png"
    info = PngImagePlugin.PngInfo(); info.add_itxt("XML:com.adobe.xmp", "<x:xmpmeta/>")
    Image.new("RGB", (20, 10)).save(path, pnginfo=info)
    with pytest.raises(UserError, match="date"):
        metadata_edit.write_fields(path, False, {"Created": "yesterday"})
    with pytest.raises(UserError, match="XMP"):
        metadata_edit.write_fields(path, False, {"Title": "New"})
    assert list(tmp_path.iterdir()) == [path]
