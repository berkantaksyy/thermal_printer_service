"""
Unit tests for the ESC/POS engine.
"""

import pytest
from app.core.escpos_engine import EscPosEngine, CMD_INIT, CMD_CUT_FULL, CMD_BOLD_ON, CMD_BOLD_OFF


def test_init_returns_correct_bytes():
    engine = EscPosEngine()
    result = engine.init()
    assert result == CMD_INIT


def test_text_line_basic():
    engine = EscPosEngine()
    result = engine.text_line("Hello")
    assert b"Hello" in result
    # LF is present (engine appends reset commands after the LF, so we check 'in' not 'endswith')
    assert b"\x0a" in result


def test_text_line_bold():
    engine = EscPosEngine()
    result = engine.text_line("Bold text", bold=True)
    assert CMD_BOLD_ON in result
    assert CMD_BOLD_OFF in result


def test_text_line_center_align():
    engine = EscPosEngine()
    result = engine.text_line("Centered", align="center")
    # ESC a 1
    assert b"\x1ba\x01" in result


def test_cut_command():
    engine = EscPosEngine()
    full_cut = engine.cut(partial=False)
    partial_cut = engine.cut(partial=True)
    assert full_cut == b"\x1dV\x00"
    assert partial_cut == b"\x1dV\x01"


def test_feed_lines():
    engine = EscPosEngine()
    result = engine.feed_lines(3)
    assert b"\x1bd\x03" == result


def test_build_receipt_has_init_and_cut():
    engine = EscPosEngine()
    lines = [{"text": "Test", "bold": False, "align": "left", "font_size": "normal"}]
    result = engine.build_receipt(lines, cut=True)
    assert result.startswith(CMD_INIT)
    assert CMD_CUT_FULL in result


def test_build_receipt_no_cut():
    engine = EscPosEngine()
    lines = [{"text": "No cut", "bold": False, "align": "left", "font_size": "normal"}]
    result = engine.build_receipt(lines, cut=False)
    assert CMD_CUT_FULL not in result


def test_qr_code_generates_bytes():
    engine = EscPosEngine()
    result = engine.qr_code("https://example.com", size=6)
    assert len(result) > 10
    # GS ( k command prefix
    assert b"\x1d(k" in result


def test_turkish_text_encoding():
    """Turkish characters should encode without exception."""
    engine = EscPosEngine()
    result = engine.text_line("Merhaba Dünya: Çalışıyor")
    assert len(result) > 0
