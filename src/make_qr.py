"""QR code for the deployed app, for the report and the demo slide.

python src/make_qr.py https://skillabus.streamlit.app   ->  docs/report/figures/qr_app.png
"""

import sys
from pathlib import Path

import qrcode
from qrcode.constants import ERROR_CORRECT_M

OUT = Path(__file__).resolve().parents[1] / "docs" / "report" / "figures" / "qr_app.png"


def main(url: str) -> None:
    qr = qrcode.QRCode(error_correction=ERROR_CORRECT_M, box_size=20, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    qr.make_image(fill_color="#0b1a2e", back_color="white").save(OUT)
    print(f"{OUT} -> {url}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: python src/make_qr.py <app url>")
    main(sys.argv[1])
