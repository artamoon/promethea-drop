from pathlib import Path
from PySide6.QtGui import QGuiApplication
from PIL import Image
from promethea import convert
from promethea.util import category


def test_svg_to_png_renders_transparency(tmp_path):
    app=QGuiApplication.instance() or QGuiApplication([])
    src=tmp_path/'drawing.svg'
    src.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="40" height="20"><rect width="20" height="20" fill="#ff0000"/></svg>',encoding='utf-8')
    out=convert.convert(src,category(src),'PNG')[0]
    with Image.open(out) as image:
        assert image.size==(40,20)
        assert image.convert('RGBA').getpixel((5,5))==(255,0,0,255)
        assert image.convert('RGBA').getpixel((35,5))[3]==0


def test_docx_to_jpg_saves_each_page_next_to_source(tmp_path, monkeypatch):
    from docx import Document
    src=tmp_path/'document.docx'; Document().save(src)
    before=src.read_bytes()
    def make_pdf(path):
        out=Path(path).with_suffix('.pdf')
        doc=convert.fitz.open();doc.new_page(width=72,height=72);doc.new_page(width=72,height=72);doc.save(out);doc.close()
        return [out]
    monkeypatch.setattr(convert,'docx_to_pdf',make_pdf)
    outputs=convert.convert(src,'docx','JPG')
    assert [p.name for p in outputs]==['document page 1.jpg','document page 2.jpg']
    assert all(p.exists() for p in outputs)
    assert src.read_bytes()==before
