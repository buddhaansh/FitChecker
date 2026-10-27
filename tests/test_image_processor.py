"""
tests/test_image_processor.py — Tests for image processing and dominant color extraction
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import io
import pytest
from PIL import Image

from src.image_processor import (
    validate_image_bytes,
    resize_image,
    save_garment_image,
    extract_dominant_colors,
    _nearest_named_color,
    get_image_info,
)


def _create_test_image_bytes(color=(255, 0, 0), size=(100, 100), fmt="JPEG"):
    img = Image.new("RGB", size, color=color)
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()


def test_validate_image_bytes_valid():
    b = _create_test_image_bytes()
    valid, msg = validate_image_bytes(b, "test.jpg")
    assert valid is True
    assert msg == ""


def test_validate_image_bytes_invalid_ext():
    b = _create_test_image_bytes()
    valid, msg = validate_image_bytes(b, "test.exe")
    assert valid is False
    assert "not supported" in msg


def test_validate_image_bytes_corrupt():
    corrupt_bytes = b"not an image file content"
    valid, msg = validate_image_bytes(corrupt_bytes, "test.jpg")
    assert valid is False
    assert "could not be opened" in msg


def test_resize_image():
    img = Image.new("RGB", (800, 600), color="blue")
    resized = resize_image(img, max_size=(300, 300))
    # Aspect ratio preserved: width 300, height 225
    assert resized.width <= 300
    assert resized.height <= 300


def test_save_garment_image():
    b = _create_test_image_bytes()
    saved_path, err = save_garment_image(b, "photo.jpg")
    assert err == ""
    assert os.path.exists(saved_path)
    assert saved_path.endswith(".jpg")

    info = get_image_info(saved_path)
    assert info["width"] > 0
    assert info["height"] > 0


def test_nearest_named_color():
    assert _nearest_named_color((255, 0, 0)) == "red"
    assert _nearest_named_color((255, 255, 255)) == "white"
    assert _nearest_named_color((0, 0, 0)) == "black"


def test_remove_background():
    from src.image_processor import remove_background
    img = Image.new("RGB", (60, 60), color=(0, 128, 0))
    cutout = remove_background(img)
    assert cutout.mode == "RGBA"
    assert cutout.size == (60, 60)


def test_save_garment_image_cutout():
    b = _create_test_image_bytes(color=(0, 0, 255))
    saved_path, err = save_garment_image(b, "photo.jpg", auto_remove_bg=True)
    assert err == ""
    assert os.path.exists(saved_path)
    assert saved_path.endswith(".png")


def test_extract_dominant_colors():
    # Pure red image
    img = Image.new("RGB", (50, 50), color=(255, 0, 0))
    colors = extract_dominant_colors(img, n_colors=1)
    assert len(colors) == 1
    assert colors[0]["name"] == "red"
    assert colors[0]["percentage"] == 100.0
