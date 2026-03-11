"""PDF bookmark (outline / table of contents) manipulation."""

import io
from collections.abc import Iterable, Sequence

import pikepdf


def add_bookmarks(
    pdf_bytes: bytes,
    items: Sequence[tuple[str, int]],
    parent: Iterable[str] | None = None,
) -> bytes:
    """Insert bookmarks into a PDF.

    Each call appends one or more sibling bookmark entries under the specified
    *parent* node. Call multiple times to build a multi-level outline
    incrementally.

    :param pdf_bytes: Raw PDF content.
    :param items: ``(title, page_number)`` pairs to insert. Page numbers are
        0-based.
    :param parent: Path of bookmark titles from the root to the desired parent
        node, e.g. ``["2026", "January"]`` inserts under the "January" child of
        "2026". ``None`` (default) or empty iterable inserts at the top level.
    :returns: PDF bytes with bookmarks added.
    :raises ValueError: If any title in *parent* is not found in the existing
        outline.
    """
    if not items:
        return pdf_bytes
    if parent is None:
        parent = ()

    with pikepdf.open(io.BytesIO(pdf_bytes)) as pdf:
        with pdf.open_outline() as outline:
            target = outline.root
            for title in parent:
                for child in target:
                    if child.title == title:
                        target = child.children
                        break
                else:
                    raise ValueError(f"Parent bookmark not found: {title!r}")

            for title, page in items:
                target.append(pikepdf.OutlineItem(title, page))

        buf = io.BytesIO()
        pdf.save(buf)
        return buf.getvalue()
