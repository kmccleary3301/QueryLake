from querylake_sdk import PdfOutputContractSummary, parse_pdf_output_contract_summary


def test_parse_pdf_output_contract_summary_from_metadata_dict():
    summary = parse_pdf_output_contract_summary(
        {
            "output_contract": "mixed_text_layer_fastpath_markdown",
            "page_source_by_page": {"0001": "text_layer", "0002": "ocr"},
            "page_source_counts": {"text_layer": 1, "ocr": 1},
        }
    )

    assert isinstance(summary, PdfOutputContractSummary)
    assert summary.is_mixed_text_layer_fastpath() is True
    assert summary.uses_text_layer() is True
    assert summary.text_layer_page_count() == 1
    assert summary.ocr_page_count() == 1
    assert summary.page_source(1) == "text_layer"
    assert summary.page_source("2") == "ocr"


def test_parse_pdf_output_contract_summary_from_payload_metadata():
    summary = parse_pdf_output_contract_summary(
        {
            "hash_id": "doc1",
            "metadata": {
                "output_contract": "text_layer_fastpath_markdown",
                "page_source_by_page": {"0001": "text_layer", "0002": "text_layer"},
                "page_source_counts": {"text_layer": 2, "ocr": 0},
            },
        }
    )

    assert summary.is_text_layer_fastpath() is True
    assert summary.is_ocr_markdown() is False
    assert summary.text_layer_page_count() == 2
    assert summary.ocr_page_count() == 0


def test_parse_pdf_output_contract_summary_defaults_to_ocr_markdown():
    summary = parse_pdf_output_contract_summary({"hash_id": "doc1"})

    assert summary.is_ocr_markdown() is True
    assert summary.uses_text_layer() is False
    assert summary.text_layer_page_count() == 0
    assert summary.ocr_page_count() == 0


def test_parse_pdf_output_contract_summary_from_md_field():
    summary = parse_pdf_output_contract_summary(
        {
            "hash_id": "doc1",
            "md": {
                "output_contract": "mixed_text_layer_fastpath_markdown",
                "page_source_by_page": {"0001": "text_layer", "0002": "ocr"},
                "page_source_counts": {"text_layer": 1, "ocr": 1},
            },
        }
    )

    assert summary.is_mixed_text_layer_fastpath() is True
    assert summary.page_source("0001") == "text_layer"
