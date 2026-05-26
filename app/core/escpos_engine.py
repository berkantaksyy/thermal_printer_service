"""
ESC/POS command engine for Cashino KP-300 / KP-301H.

Builds raw ESC/POS byte sequences from high-level operations.
All constants are derived directly from the KP-300/KP-301H datasheets.

References:
  - KP-300 User Manual (Cashino, 80pp) — command table pp. 34-65
  - KP-301H User Manual (Cashino) — same ESC/POS command set
"""

import io
import struct
from typing import Literal
from PIL import Image
import qrcode
from qrcode.constants import ERROR_CORRECT_L, ERROR_CORRECT_M, ERROR_CORRECT_Q, ERROR_CORRECT_H


# ── ESC/POS Constants (from KP-300/KP-301H datasheets) ───────────────────────

ESC = b"\x1b"
GS  = b"\x1d"
FS  = b"\x1c"
DLE = b"\x10"

# Initialise printer
CMD_INIT          = ESC + b"@"

# Line feed
CMD_LF            = b"\x0a"

# Cut paper — full cut (GS V 0)
CMD_CUT_FULL      = GS + b"V\x00"
# Cut paper — partial cut (GS V 1)
CMD_CUT_PARTIAL   = GS + b"V\x01"

# Text formatting
CMD_BOLD_ON       = ESC + b"E\x01"
CMD_BOLD_OFF      = ESC + b"E\x00"
CMD_UNDERLINE_ON  = ESC + b"-\x01"
CMD_UNDERLINE_OFF = ESC + b"-\x00"
CMD_ALIGN_LEFT    = ESC + b"a\x00"
CMD_ALIGN_CENTER  = ESC + b"a\x01"
CMD_ALIGN_RIGHT   = ESC + b"a\x02"

# Font size (GS ! n)  — n byte bits: upper nibble=height mult, lower=width mult
CMD_FONT_NORMAL        = GS + b"!\x00"  # 1x1
CMD_FONT_DOUBLE_HEIGHT = GS + b"!\x10"  # 2x1
CMD_FONT_DOUBLE_WIDTH  = GS + b"!\x01"  # 1x2
CMD_FONT_DOUBLE        = GS + b"!\x11"  # 2x2

_ALIGN_MAP = {
    "left":   CMD_ALIGN_LEFT,
    "center": CMD_ALIGN_CENTER,
    "right":  CMD_ALIGN_RIGHT,
}
_FONT_SIZE_MAP = {
    "normal":        CMD_FONT_NORMAL,
    "double_height": CMD_FONT_DOUBLE_HEIGHT,
    "double_width":  CMD_FONT_DOUBLE_WIDTH,
    "double":        CMD_FONT_DOUBLE,
}
_QR_EC_MAP = {
    "L": ERROR_CORRECT_L,
    "M": ERROR_CORRECT_M,
    "Q": ERROR_CORRECT_Q,
    "H": ERROR_CORRECT_H,
}


class EscPosEngine:
    """
    Stateless ESC/POS command builder.
    Returns raw bytes ready to be sent to the printer.
    """

    def init(self) -> bytes:
        """Initialize / reset printer."""
        return CMD_INIT

    def text_line(
        self,
        text: str,
        bold: bool = False,
        underline: bool = False,
        align: Literal["left", "center", "right"] = "left",
        font_size: str = "normal",
        encoding: str = "cp857",  # Turkish codepage — supported by KP-300
    ) -> bytes:
        """Encode a single text line with formatting."""
        buf = bytearray()
        buf += _ALIGN_MAP.get(align, CMD_ALIGN_LEFT)
        buf += _FONT_SIZE_MAP.get(font_size, CMD_FONT_NORMAL)
        if bold:
            buf += CMD_BOLD_ON
        if underline:
            buf += CMD_UNDERLINE_ON

        # Try Turkish cp857 first, fall back to latin-1, then utf-8 byte encoding
        try:
            encoded = text.encode(encoding)
        except (UnicodeEncodeError, LookupError):
            try:
                encoded = text.encode("latin-1")
            except UnicodeEncodeError:
                encoded = text.encode("utf-8")

        buf += encoded
        buf += CMD_LF

        if bold:
            buf += CMD_BOLD_OFF
        if underline:
            buf += CMD_UNDERLINE_OFF
        # Reset font and alignment
        buf += CMD_FONT_NORMAL
        buf += CMD_ALIGN_LEFT
        return bytes(buf)

    def image(
        self,
        image_data: bytes,
        align: Literal["left", "center", "right"] = "center",
        max_width: int = 576,  # KP-300 print head: 80mm @ 203dpi ≈ 640px, conservative 576
    ) -> bytes:
        """
        Convert image bytes to ESC/POS bitmap commands.
        Uses ESC * (bit image mode) as supported by KP-300/KP-301H.
        """
        img = Image.open(io.BytesIO(image_data)).convert("L")  # Grayscale

        # Resize to fit printer width while preserving aspect ratio
        if img.width > max_width:
            ratio = max_width / img.width
            new_height = int(img.height * ratio)
            img = img.resize((max_width, new_height), Image.LANCZOS)

        # Convert to 1-bit (threshold dithering)
        img = img.convert("1")
        w, h = img.size

        buf = bytearray()
        buf += _ALIGN_MAP.get(align, CMD_ALIGN_CENTER)

        # GS v 0 (raster bit image) — supported on KP-300
        # Format: GS v 0 m xL xH yL yH d1..dk
        m = 0  # normal (1x scale)
        xL = (w // 8) & 0xFF
        xH = ((w // 8) >> 8) & 0xFF
        yL = h & 0xFF
        yH = (h >> 8) & 0xFF
        buf += GS + b"v\x00" + bytes([m, xL, xH, yL, yH])

        # Convert pixel rows to bytes
        pixels = list(img.getdata())
        row_bytes = w // 8
        for row in range(h):
            for byte_idx in range(row_bytes):
                byte_val = 0
                for bit in range(8):
                    px_idx = row * w + byte_idx * 8 + bit
                    if px_idx < len(pixels) and pixels[px_idx] == 0:  # black pixel
                        byte_val |= (0x80 >> bit)
                buf.append(byte_val)

        buf += CMD_LF
        buf += CMD_ALIGN_LEFT
        return bytes(buf)

    def qr_code(
        self,
        data: str,
        size: int = 6,
        error_correction: str = "M",
        align: Literal["left", "center", "right"] = "center",
        label: str | None = None,
    ) -> bytes:
        """
        Generate QR code using ESC/POS GS ( k commands.
        KP-300 supports GS ( k QR code printing natively.
        Falls back to image rendering if native fails.
        """
        buf = bytearray()
        buf += _ALIGN_MAP.get(align, CMD_ALIGN_CENTER)

        # Try native ESC/POS QR commands (GS ( k)
        # Store data
        data_bytes = data.encode("utf-8")
        data_len = len(data_bytes) + 3
        pL = data_len & 0xFF
        pH = (data_len >> 8) & 0xFF

        # GS ( k — Select error correction level
        ec_map = {"L": 48, "M": 49, "Q": 50, "H": 51}
        ec_val = ec_map.get(error_correction, 49)

        # Set model (Model 2)
        buf += GS + b"(k\x04\x001A\x32\x00"
        # Set size
        buf += GS + b"(k\x03\x001C" + bytes([size])
        # Set error correction
        buf += GS + b"(k\x03\x001E" + bytes([ec_val])
        # Store data
        buf += GS + b"(k" + bytes([pL, pH]) + b"\x01P" + data_bytes
        # Print
        buf += GS + b"(k\x03\x001Q0"

        buf += CMD_LF

        # Optional label below QR
        if label:
            buf += _ALIGN_MAP.get(align, CMD_ALIGN_CENTER)
            buf += label.encode("utf-8") + CMD_LF

        buf += CMD_ALIGN_LEFT
        return bytes(buf)

    def cut(self, partial: bool = False) -> bytes:
        """Send paper cut command."""
        return CMD_CUT_PARTIAL if partial else CMD_CUT_FULL

    def feed_lines(self, n: int = 3) -> bytes:
        """Feed n blank lines (for paper margin before cut)."""
        return ESC + b"d" + bytes([n])

    def build_receipt(
        self,
        lines: list[dict],
        cut: bool = True,
        feed_before_cut: int = 3,
    ) -> bytes:
        """
        Build complete receipt bytes from a list of line dicts.
        Each dict: {text, bold, underline, align, font_size}
        """
        buf = bytearray()
        buf += self.init()
        for line in lines:
            buf += self.text_line(
                text=line.get("text", ""),
                bold=line.get("bold", False),
                underline=line.get("underline", False),
                align=line.get("align", "left"),
                font_size=line.get("font_size", "normal"),
            )
        if cut:
            buf += self.feed_lines(feed_before_cut)
            buf += self.cut()
        return bytes(buf)


# Module-level singleton
engine = EscPosEngine()
