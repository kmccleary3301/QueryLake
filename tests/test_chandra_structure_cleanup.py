from pathlib import Path
import importlib.util


_MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "chandra_structure_cleanup.py"
_SPEC = importlib.util.spec_from_file_location("chandra_structure_cleanup", _MODULE_PATH)
assert _SPEC and _SPEC.loader
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
cleanup_dir = _MODULE.cleanup_dir
cleanup_text = _MODULE.cleanup_text


def test_cleanup_text_moves_arxiv_compacts_tables_and_drops_page_number() -> None:
    source = """![NVIDIA logo]()

2026-3-11

Scalable Training of Mixture-of-Experts Models with Megatron Core
=================================================================

arXiv:2603.07685v2 [cs.DC] 10 Mar 2026

| **1** | **Introduction** | **5** |
| --- | --- | --- |
| 1.1 | Mixture of Experts | 5 |
| 1.2 | Challenges | 6 |

4
"""
    cleaned = cleanup_text(source, page_number=4)
    assert cleaned.startswith("arXiv:2603.07685v2 [cs.DC] 10 Mar 2026")
    assert "![NVIDIA logo]()" not in cleaned
    assert "| **1** **Introduction** | **5** |" in cleaned
    assert "| 1.1 Mixture of Experts | 5 |" in cleaned
    assert not cleaned.rstrip().endswith("\n4")


def test_cleanup_dir_writes_cleaned_pages(tmp_path: Path) -> None:
    src = tmp_path / "src"
    dst = tmp_path / "dst"
    src.mkdir()
    (src / "page_0001.md").write_text("![x]()\n\nhello\n\n1\n")
    cleanup_dir(src, dst)
    assert (dst / "page_0001.md").read_text() == "hello\n"


def test_cleanup_text_can_disable_selected_transforms() -> None:
    source = "arXiv:2603.07685v2 [cs.DC] 10 Mar 2026\n\n![x]()\n\n7\n"
    cleaned = cleanup_text(
        source,
        page_number=7,
        strip_empty_images=False,
        move_arxiv_front=False,
        drop_terminal_page_number=False,
        compact_outline_tables=False,
    )
    assert "![x]()" in cleaned
    assert cleaned.rstrip().endswith("7")
