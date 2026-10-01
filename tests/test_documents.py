from unittest.mock import Mock, patch

import pytest


def test_odt_import_keeps_headings_and_paragraph_boundaries(controller, tmp_path):
    pytest.importorskip("odf")
    from odf.opendocument import OpenDocumentText
    from odf.text import H, P, Span

    document = OpenDocumentText()
    document.text.addElement(H(outlinelevel=1, text="Title"))
    paragraph = P(text="Hello ")
    paragraph.addElement(Span(text="world"))
    document.text.addElement(paragraph)
    document.text.addElement(P())
    document.text.addElement(P(text="Last paragraph"))
    path = tmp_path / "input.odt"
    document.save(str(path))
    assert controller._extract_odt(str(path)) == "Title\nHello world\n\nLast paragraph"


def test_docx_import_keeps_table_text_in_document_order(controller, tmp_path):
    docx = pytest.importorskip("docx")
    document = docx.Document()
    document.add_paragraph("before")
    table = document.add_table(rows=1, cols=2)
    table.cell(0, 0).text = "cell A"
    table.cell(0, 1).text = "cell B"
    document.add_paragraph("after")
    path = tmp_path / "input.docx"
    document.save(str(path))
    text = controller._extract_docx(str(path))
    assert "cell A" in text and "cell B" in text
    assert text.index("before") < text.index("cell A") < text.index("after")


@pytest.mark.parametrize("extension", ["txt", "docx", "odt"])
def test_export_round_trip_preserves_empty_lines(controller, tmp_path, extension):
    if extension == "odt":
        pytest.importorskip("odf")
    elif extension == "docx":
        pytest.importorskip("docx")
    path = tmp_path / f"translated.{extension}"
    controller.view.output = "First paragraph\n\nThird paragraph\n"
    controller.view.ask_save_file = Mock(return_value=str(path))
    controller._on_save_file()
    assert path.exists()
    assert controller._extract_text_from_file(str(path)) == controller.view.output


def test_pdf_export_preserves_accents_and_punctuation(controller, tmp_path):
    pytest.importorskip("fpdf")
    fitz = pytest.importorskip("fitz")
    path = tmp_path / "translated.pdf"
    controller.view.output = "Traducción: ¡Hola! — café €"
    controller.view.ask_save_file = Mock(return_value=str(path))
    controller._on_save_file()
    assert path.exists()
    with fitz.open(str(path)) as document:
        text = "".join(page.get_text() for page in document)
    assert controller.view.output in text


def test_pdf_does_not_silently_replace_unsupported_characters(controller, tmp_path):
    pytest.importorskip("fpdf")
    path = tmp_path / "translated.pdf"
    controller.view.output = "你好"
    controller.view.ask_save_file = Mock(return_value=str(path))
    with patch("os.path.exists", return_value=False):
        controller._on_save_file()
    assert not path.exists()
    controller._drain_ui_queue()
    assert controller.view.set_status.call_args.args[1] == "error"


def test_opening_a_file_does_not_read_it_on_the_tk_thread(controller, tmp_path):
    path = tmp_path / "input.txt"
    path.write_text("file content", encoding="utf-8")
    controller.view.ask_open_file = Mock(return_value=str(path))
    with patch("fungi_traductor.controller.app_controller.threading.Thread") as worker:
        controller._on_open_file()
    worker.assert_called_once()
    assert controller.view.input == ""


def test_worker_loading_ocr_does_not_read_tk_widgets(controller):
    pytesseract = pytest.importorskip("pytesseract")
    image = pytest.importorskip("PIL.Image")
    controller.view.get_from_code = Mock(
        side_effect=lambda: (_ for _ in ()).throw(AssertionError("Tk access from a worker"))
    )
    fake_image = Mock()
    fake_image.__enter__ = Mock(return_value=fake_image)
    fake_image.__exit__ = Mock()
    with patch.object(image, "open", return_value=fake_image), \
            patch.object(pytesseract, "image_to_string", return_value="hello") as ocr:
        assert controller._extract_image_ocr("input.png", src_code="en") == "hello"
    ocr.assert_called_once_with(fake_image, lang="eng")


def test_export_with_an_unknown_extension_reports_the_actual_format(controller, tmp_path):
    path = tmp_path / "translation.other"
    controller.view.output = "hello"
    controller.view.ask_save_file = Mock(return_value=str(path))
    controller._on_save_file()
    controller._drain_ui_queue()
    assert path.with_suffix(".other.txt").read_text(encoding="utf-8") == "hello"
    assert controller.view.set_status.call_args.args == ("● traducción guardada como TXT", "ok")
