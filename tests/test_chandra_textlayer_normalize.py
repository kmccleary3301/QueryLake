from __future__ import annotations

from scripts.chandra_textlayer_normalize import normalize_textlayer_page


def test_normalize_textlayer_page_converts_toc_and_unwraps_text():
    raw = """2026-3-11
Scalable Training of Mixture-of-Experts Models with
Megatron Core
Technical Report
Contents
1 Introduction 5
1.1 Mixture of Experts 5
2 Architecture 8
2.1 Forward Pass 9

This is a wrapped
paragraph that should be
joined.
"""
    out = normalize_textlayer_page(raw)
    assert "Scalable Training of Mixture-of-Experts Models with Megatron Core" in out
    assert "Technical Report\n----------------" in out
    assert "| Section | Page |" in out
    assert "This is a wrapped paragraph that should be joined." in out


def test_normalize_textlayer_page_strips_source_banner_and_keeps_doi():
    raw = """Nature Methods
nature methods
https://doi.org/10.1038/example
Brief Communication
DeepCor: denoising fMRI data with
contrastive autoencoders

Body line one
Body line two
"""
    out = normalize_textlayer_page(raw)
    assert "nature methods" not in out.lower()
    assert "Brief Communication" in out
    assert "DeepCor: denoising fMRI data with contrastive autoencoders" in out
    assert "Body line one Body line two" in out
