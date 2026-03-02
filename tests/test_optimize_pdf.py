import io

import pytest

pikepdf = pytest.importorskip("pikepdf")

from pikepdf import Name, Page
from pyplaner.optimize_pdf import (
    optimize_pdf,
    _stream_content_bytes,
    _deduplicate_images,
    _strip_and_dedup_resources,
)


def _make_page(pdf, resources=None, content=b""):
    page_dict = pikepdf.Dictionary(Type=Name.Page, MediaBox=[0, 0, 612, 792])
    if resources is not None:
        page_dict[Name.Resources] = resources
    if content:
        page_dict[Name.Contents] = pdf.make_stream(content)
    return Page(page_dict)


def _roundtrip(pdf):
    """Save and re-open to get proper indirect objects."""
    buf = io.BytesIO()
    pdf.save(buf)
    buf.seek(0)
    return pikepdf.open(buf)


def test_stream_content_bytes():
    """_stream_content_bytes returns the raw bytes of a stream object."""
    pdf = pikepdf.new()
    data = b"hello world"
    stream = pdf.make_stream(data)
    result = _stream_content_bytes(stream)
    assert result == data


def test_deduplicate_identical_images():
    """_deduplicate_images rewires two pages to share one canonical image."""
    pdf = pikepdf.new()
    img_data = b"\x89PNG\r\n" + b"\x00" * 100

    for _ in range(2):
        img = pdf.make_stream(img_data)
        img[Name.Type] = Name.XObject
        img[Name.Subtype] = Name.Image
        img[Name.Width] = 10
        img[Name.Height] = 10
        resources = pikepdf.Dictionary(
            XObject=pikepdf.Dictionary({"/Im0": img}),
        )
        pdf.pages.append(_make_page(pdf, resources, b"q /Im0 Do Q"))

    pdf = _roundtrip(pdf)

    p0_img = pdf.pages[0][Name.Resources][Name.XObject]["/Im0"]
    p1_img = pdf.pages[1][Name.Resources][Name.XObject]["/Im0"]
    assert p0_img.objgen != p1_img.objgen

    _deduplicate_images(pdf)

    p0_img = pdf.pages[0][Name.Resources][Name.XObject]["/Im0"]
    p1_img = pdf.pages[1][Name.Resources][Name.XObject]["/Im0"]
    assert p0_img.objgen == p1_img.objgen


def test_deduplicate_images_no_crash_when_no_images():
    """_deduplicate_images does nothing on a PDF with no images."""
    pdf = pikepdf.new()
    pdf.pages.append(_make_page(pdf))
    pdf = _roundtrip(pdf)
    _deduplicate_images(pdf)


def test_strip_procset():
    """_strip_and_dedup_resources removes obsolete /ProcSet arrays."""
    pdf = pikepdf.new()
    resources = pikepdf.Dictionary(
        ProcSet=pikepdf.Array([Name.PDF, Name.ImageC]),
    )
    pdf.pages.append(_make_page(pdf, resources))
    pdf = _roundtrip(pdf)

    assert Name.ProcSet in pdf.pages[0][Name.Resources]
    _strip_and_dedup_resources(pdf)
    assert Name.ProcSet not in pdf.pages[0][Name.Resources]


def test_deduplicate_form_xobjects():
    """_strip_and_dedup_resources merges identical Form XObjects across pages."""
    pdf = pikepdf.new()
    form_data = b"q 1 0 0 1 0 0 cm Q"

    for _ in range(2):
        form = pdf.make_stream(form_data)
        form[Name.Type] = Name.XObject
        form[Name.Subtype] = Name.Form
        form[Name.BBox] = pikepdf.Array([0, 0, 100, 100])
        resources = pikepdf.Dictionary(
            XObject=pikepdf.Dictionary({"/Fm0": form}),
        )
        pdf.pages.append(_make_page(pdf, resources, b"q /Fm0 Do Q"))

    pdf = _roundtrip(pdf)

    p0_fm = pdf.pages[0][Name.Resources][Name.XObject]["/Fm0"]
    p1_fm = pdf.pages[1][Name.Resources][Name.XObject]["/Fm0"]
    assert p0_fm.objgen != p1_fm.objgen

    _strip_and_dedup_resources(pdf)

    p0_fm = pdf.pages[0][Name.Resources][Name.XObject]["/Fm0"]
    p1_fm = pdf.pages[1][Name.Resources][Name.XObject]["/Fm0"]
    assert p0_fm.objgen == p1_fm.objgen


def test_optimize_pdf_full_pipeline():
    """optimize_pdf runs all stages without error and strips ProcSet."""
    pdf = pikepdf.new()
    img_data = b"\x89PNG\r\n" + b"\x00" * 100

    for _ in range(2):
        img = pdf.make_stream(img_data)
        img[Name.Type] = Name.XObject
        img[Name.Subtype] = Name.Image
        img[Name.Width] = 10
        img[Name.Height] = 10
        resources = pikepdf.Dictionary(
            XObject=pikepdf.Dictionary({"/Im0": img}),
            ProcSet=pikepdf.Array([Name.PDF, Name.ImageC]),
        )
        pdf.pages.append(_make_page(pdf, resources, b"q /Im0 Do Q"))

    pdf = _roundtrip(pdf)
    optimize_pdf(pdf)

    for page in pdf.pages:
        res = page.get(Name.Resources)
        if res is not None:
            assert Name.ProcSet not in res
