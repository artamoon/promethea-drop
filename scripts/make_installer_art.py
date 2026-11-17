"""Generate the installer artwork from the application's existing icon."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "installer" / "assets"
OUT.mkdir(parents=True, exist_ok=True)
icon = Image.open(ROOT / "promethea" / "assets" / "promethea.png").convert("RGBA")
ink = "#EEECE6"
accent = "#E4F222"
font_path = Path("C:/Windows/Fonts/seguiemj.ttf")
font_path = Path("C:/Windows/Fonts/segoeui.ttf") if Path("C:/Windows/Fonts/segoeui.ttf").exists() else font_path
font = ImageFont.truetype(str(font_path), 23)
small = ImageFont.truetype(str(font_path), 13)

panel = Image.new("RGB", (330, 620), "#1C1C1C")
draw = ImageDraw.Draw(panel)
logo = icon.resize((190, 190), Image.Resampling.LANCZOS)
panel.paste(logo, (28, 72), logo)
draw.rectangle((28, 342, 81, 345), fill=accent)
draw.text((28, 366), "PROMETHEA", font=font, fill=ink)
draw.text((29, 403), "D R O P", font=small, fill=ink)
panel.save(OUT / "wizard.png")

small_panel = Image.new("RGB", (110, 110), "#1C1C1C")
logo = icon.resize((86, 86), Image.Resampling.LANCZOS)
small_panel.paste(logo, (12, 12), logo)
small_panel.save(OUT / "wizard-small.png")
