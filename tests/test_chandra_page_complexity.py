from pathlib import Path
import sys

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from QueryLake.operation_classes.ray_chandra_class import analyze_ocr_page_complexity


def test_page_complexity_identifies_simple_sparse_page():
    image = Image.new("RGB", (800, 1000), "white")
    draw = ImageDraw.Draw(image)
    draw.text((80, 120), "A short title", fill="black")
    draw.text((80, 180), "One paragraph of text.", fill="black")

    result = analyze_ocr_page_complexity(image)

    assert result["class"] in {"simple", "mixed"}
    assert result["near_white_fraction"] > 0.85
    assert result["pixels"] == 800000


def test_page_complexity_treats_very_sparse_light_pages_as_simple():
    image = Image.new("RGB", (900, 1200), "white")
    draw = ImageDraw.Draw(image)
    draw.text((70, 140), "Minimal heading", fill="black")
    draw.text((70, 220), "Sparse caption line.", fill="black")
    draw.text((70, 300), "Another short line.", fill="black")

    result = analyze_ocr_page_complexity(image)

    assert result["class"] == "simple"
    assert result["ink_fraction"] <= 0.02
    assert result["edge_density"] <= 0.03


def test_page_complexity_identifies_complex_dense_page():
    image = Image.new("RGB", (800, 1000), "white")
    draw = ImageDraw.Draw(image)
    cell_w = 90
    cell_h = 28
    for row in range(24):
        for col in range(7):
            x0 = 40 + col * cell_w
            y0 = 40 + row * cell_h
            x1 = x0 + cell_w - 8
            y1 = y0 + cell_h - 6
            draw.rectangle((x0, y0, x1, y1), outline="black", width=2)
            draw.text((x0 + 8, y0 + 6), f"{row}:{col}", fill="black")

    result = analyze_ocr_page_complexity(image)

    assert result["class"] in {"mixed", "complex"}
    assert result["edge_density"] > 0.05
    assert result["variance"] > 0.0
