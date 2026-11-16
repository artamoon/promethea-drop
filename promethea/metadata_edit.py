"""Edit embedded metadata on a copy without re-encoding image pixels."""
from __future__ import annotations

import binascii
import re
import struct
from datetime import datetime
from pathlib import Path

from PIL import Image
from .convert import atomic_save, open_pdf
from .util import UserError, sibling

FIELDS = ("Title", "Author", "Description", "Created")
XP_TAGS = {"Title": 0x9C9B, "Author": 0x9C9D, "Description": 0x9C9C}
PDF_TAGS = {"Title": "title", "Author": "author", "Description": "subject", "Created": "creationDate"}


def supported(path: str | Path, is_pdf: bool = False) -> bool:
    return is_pdf or Path(path).suffix.lower() in {".jpg", ".jpeg", ".png"}


def _date_display(value: str) -> str:
    if not value:
        return ""
    m = re.match(r"^(?:D:)?(\d{4})[:\-]?(\d{2})[:\-]?(\d{2})[ T]?(\d{2}):?(\d{2}):?(\d{2})", str(value))
    return f"{m[1]}-{m[2]}-{m[3]} {m[4]}:{m[5]}:{m[6]}" if m else str(value)


def _date(value: str, pdf: bool) -> str:
    try:
        dt = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        raise UserError("Use a valid date and time: YYYY-MM-DD HH:MM:SS") from None
    return dt.strftime("D:%Y%m%d%H%M%S" if pdf else "%Y:%m:%d %H:%M:%S")


def _xp_value(value) -> str:
    if isinstance(value, (bytes, tuple, list)):
        try:
            return bytes(value).decode("utf-16le").rstrip("\x00")
        except (ValueError, UnicodeError):
            return ""
    return str(value or "")


def read_fields(path: str | Path, is_pdf: bool) -> dict[str, str]:
    if is_pdf:
        with open_pdf(path) as doc:
            meta = doc.metadata or {}
            return {key: _date_display(meta.get(tag, "")) if key == "Created" else str(meta.get(tag) or "")
                    for key, tag in PDF_TAGS.items()}
    with Image.open(path) as im:
        exif = im.getexif()
        sub = exif.get_ifd(0x8769)
        result = {key: _xp_value(exif.get(tag)) for key, tag in XP_TAGS.items()}
        result["Author"] = result["Author"] or str(exif.get(0x013B, ""))
        result["Description"] = result["Description"] or str(exif.get(0x010E, ""))
        result["Created"] = _date_display(str(sub.get(0x9003) or ""))
        return result


def _jpeg_exif(data: bytes, exif: bytes) -> bytes:
    if not data.startswith(b"\xff\xd8"):
        raise UserError("This file is not a valid JPEG")
    if len(exif) + 2 > 65535:
        raise UserError("EXIF metadata is too large for JPEG")
    segment = b"\xff\xe1" + struct.pack(">H", len(exif) + 2) + exif
    pos, parts, found = 2, [data[:2], segment], 0
    while pos < len(data):
        start = pos
        if data[pos] != 0xFF:
            raise UserError("Cannot safely update this JPEG")
        while pos < len(data) and data[pos] == 0xFF:
            pos += 1
        if pos >= len(data):
            raise UserError("Cannot safely update this JPEG")
        marker = data[pos]; pos += 1
        if marker in (0xDA, 0xD9):
            parts.append(data[start:]); break
        if marker in (0x01, *range(0xD0, 0xD8)):
            parts.append(data[start:pos]); continue
        if pos + 2 > len(data):
            raise UserError("Cannot safely update this JPEG")
        length = int.from_bytes(data[pos:pos + 2], "big")
        if length < 2 or pos + length > len(data):
            raise UserError("Cannot safely update this JPEG")
        end = pos + length
        if marker == 0xE1 and data[pos + 2:pos + 8] == b"Exif\x00\x00":
            found += 1
            if found > 1:
                raise UserError("This JPEG has multiple EXIF blocks and cannot be safely edited")
        else:
            parts.append(data[start:end])
        pos = end
    else:
        raise UserError("Cannot safely update this JPEG")
    return b"".join(parts)


def _png_exif(data: bytes, exif: bytes) -> bytes:
    signature = b"\x89PNG\r\n\x1a\n"
    if not data.startswith(signature):
        raise UserError("This file is not a valid PNG")
    payload = exif[6:] if exif.startswith(b"Exif\x00\x00") else exif
    kind = b"eXIf"
    chunk = struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", binascii.crc32(kind + payload) & 0xffffffff)
    pos, parts, inserted = 8, [signature], False
    while pos + 12 <= len(data):
        length = int.from_bytes(data[pos:pos + 4], "big")
        end = pos + length + 12
        if end > len(data):
            raise UserError("Cannot safely update this PNG")
        typ = data[pos + 4:pos + 8]
        if typ == b"IDAT" and not inserted:
            parts.append(chunk); inserted = True
        if typ != b"eXIf":
            parts.append(data[pos:end])
        pos = end
        if typ == b"IEND":
            if not inserted or pos != len(data):
                raise UserError("Cannot safely update this PNG")
            return b"".join(parts)
    raise UserError("Cannot safely update this PNG")


def write_fields(path: str | Path, is_pdf: bool, changes: dict[str, str]) -> Path:
    path = Path(path)
    if not supported(path, is_pdf):
        raise UserError("Editing is available for JPEG, PNG and PDF files")
    changes = {k: v.strip() for k, v in changes.items() if k in FIELDS}
    if "Created" in changes and changes["Created"]:
        _date(changes["Created"], is_pdf)
    out = sibling(path, "Metadata", path.suffix)
    if is_pdf:
        with open_pdf(path) as doc:
            if doc.get_xml_metadata():
                raise UserError("This PDF has XMP metadata; editing it safely is not yet supported")
            metadata = dict(doc.metadata or {})
            for readonly in ("format", "encryption"):
                metadata.pop(readonly, None)
            for key, value in changes.items():
                metadata[PDF_TAGS[key]] = _date(value, True) if key == "Created" and value else value
            doc.set_metadata(metadata)
            atomic_save(lambda tmp: doc.save(str(tmp)), out)
        return out
    with Image.open(path) as im:
        if any(k in im.info for k in ("xmp", "XML:com.adobe.xmp", "XML:com.adobe.xmp\x00")):
            raise UserError("This image has XMP metadata; editing it safely is not yet supported")
        exif = im.getexif()
        if 0x927C in exif.get_ifd(0x8769):
            raise UserError("This image has camera maker notes; editing them safely is not yet supported")
        if path.suffix.lower() == ".png":
            text_tags = {"Title": ("Title",), "Author": ("Author",),
                         "Description": ("Description", "Comment"), "Created": ("Creation Time",)}
            if any(k in im.info for field, keys in text_tags.items() if field in changes for k in keys):
                raise UserError("This PNG has text metadata for an edited field; editing it safely is not yet supported")
        for key, tag in XP_TAGS.items():
            if key in changes:
                # Remove the old parallel EXIF value when replacing or clearing it.
                old_tag = {"Author": 0x013B, "Description": 0x010E}.get(key)
                if old_tag is not None and old_tag in exif:
                    del exif[old_tag]
                if changes[key]:
                    exif[tag] = (changes[key] + "\x00").encode("utf-16le")
                elif tag in exif:
                    del exif[tag]
        if "Created" in changes:
            sub = dict(exif.get_ifd(0x8769))
            if changes["Created"]:
                sub[0x9003] = _date(changes["Created"], False)
            else:
                sub.pop(0x9003, None)
            if sub:
                exif[0x8769] = sub
            elif 0x8769 in exif:
                del exif[0x8769]
        exif_bytes = exif.tobytes()
    data = path.read_bytes()
    if b"http://ns.adobe.com/xap/1.0/\x00" in data or b"XML:com.adobe.xmp" in data:
        raise UserError("This image has XMP metadata; editing it safely is not yet supported")
    updated = _jpeg_exif(data, exif_bytes) if path.suffix.lower() in {".jpg", ".jpeg"} else _png_exif(data, exif_bytes)
    atomic_save(lambda tmp: Path(tmp).write_bytes(updated), out)
    return out
