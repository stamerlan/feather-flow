"""Post-processing optimizations for Chromium-generated PDFs.

Chromium's ``page.pdf()`` (via Playwright) produces valid but bloated PDFs.
Every page is rendered independently, so identical assets - background images,
SVG rasterizations, transparency masks - are embedded as *separate* PDF objects
on every page. For a 365-day planner, this multiplies the same few images by
hundreds of times.

This module provides :func:`optimize_pdf`, which rewrites the in-memory
``pikepdf.Pdf`` to eliminate that redundancy before it is saved to disk.

Optimizations performed
-----------------------

1. **Image stream deduplication**

    Chromium rasterizes every ``<img>`` and inline ``<svg>`` per page. Two pages
    that share the same background and the same SVG image each get their own
    copy of the resulting Image XObject and its ``/SMask`` transparency mask. In
    a 365-day planner this produces ~730 redundant Image XObjects.

    First, every indirect object in the PDF is iterated via ``pdf.objects``.
    Image XObjects (``/Subtype /Image``) are identified, their content is hashed
    with SHA-256, and a *replacement map* is built:
    ``{duplicate_objgen: canonical_object}``.

    Then the full object graph is walked starting from each page and every
    reference that points at a duplicate is rewritten to point at the canonical
    copy instead. After this pass the duplicate objects become unreachable and
    are dropped when pikepdf writes the file.

    *Workaround - StreamDecodeLevel fallback:* When pikepdf saves with
    ``object_stream_mode=generate``, the resulting object-stream packaging makes
    individual streams unreadable at ``StreamDecodeLevel.none``
    (``PdfError: read_bytes called on unfilterable stream``). Fall back to
    ``StreamDecodeLevel.specialized`` which decodes FlateDecode / DCTDecode into
    raw pixel bytes. The hash is still consistent - two streams with identical
    decoded content always hash the same way.

    *Workaround - inline object objgen (0, 0):* PikePDF reports
    ``objgen == (0, 0)`` for every inline (non-indirect) dictionary, array, or
    name. A naive ``visited`` set would mark ``(0, 0)`` as "already seen" after
    the very first inline dict, preventing the walk from ever descending into
    nested inline structures (like ``/Resources`` -> ``/Pattern`` ->
    ``PatternStream`` -> ``/Resources`` -> ``/XObject`` -> Image). Exclude
    ``(0, 0)`` from cycle detection so the walk always enters inline objects.

    *Structural note - Patterns vs. Forms:* Chromium may wrap the SVG
    rasterization inside tiling **Pattern** objects instead of Form XObjects.
    The reference path is ``Page -> /Resources -> /Pattern -> PatternStream ->
    /Resources -> /XObject -> Image``. A walk that only recurses into Form
    XObjects would miss these entirely; the full graph walk handles them.

2. **``/Resources/ProcSet`` stripping**

    ``ProcSet`` arrays (``[/PDF /Text /ImageB /ImageC /ImageI]``) are obsolete
    since PDF 1.4 (2001) and ignored by every modern reader. Chromium still
    emits one on every page and inside every Form XObject. They are deleted from
    every ``/Resources`` dict encountered.

3. **Form XObject deduplication**

    After image deduplication, many Form XObjects that previously differed only
    in which copy of an image they referenced now have identical content
    streams. Each Form's stored bytes are hashed and duplicates are merged, the
    same way as for images above.
"""
import hashlib
from typing import Any

import pikepdf
from pikepdf import Name, Stream
from pikepdf._core import StreamDecodeLevel


def _stream_content_bytes(obj: Any) -> bytes:
    """Return the content bytes of *obj* for hashing.

    Tries ``StreamDecodeLevel.none`` first (raw stored bytes - fast, no
    decompression). If that fails (common when the PDF was saved into
    object streams with ``ObjectStreamMode.generate``), falls back to
    ``StreamDecodeLevel.specialized`` which decodes the stream through
    its filters.

    :param obj: A pikepdf stream object.
    :returns: Raw or decoded stream bytes.
    :raises Exception: If neither decode level succeeds.
    """
    try:
        return bytes(obj.get_stream_buffer(
            decode_level=StreamDecodeLevel.none))
    except Exception:
        return bytes(obj.get_stream_buffer(
            decode_level=StreamDecodeLevel.specialized))


def optimize_pdf(pdf: pikepdf.Pdf) -> None:
    """Deduplicate images, strip ProcSets, and merge identical Forms.

    Modifies *pdf* in place. See the module docstring for a detailed
    description of each optimization, the workarounds applied, and the
    rationale.

    :param pdf: An open :class:`pikepdf.Pdf` object to optimize in place.
    """
    _deduplicate_images(pdf)
    _strip_and_dedup_resources(pdf)
    pdf.remove_unreferenced_resources()


def _deduplicate_images(pdf: pikepdf.Pdf) -> None:
    """Find duplicate Image XObjects and rewire references.

    :param pdf: An open :class:`pikepdf.Pdf` object to modify in place.

    Build a replacement map
    ^^^^^^^^^^^^^^^^^^^^^^^
    Iterates *every* indirect object via ``pdf.objects``. For each
    ``/Subtype /Image`` stream, reads its content bytes (see
    :func:`_stream_content_bytes` for the decode-level workaround), computes a
    SHA-256 digest, and records:

    * First occurrence of a digest -> *canonical* object.
    * Subsequent occurrences -> added to ``image_replacements`` mapping
      ``duplicate.objgen -> canonical_object``.

    Rewrite references via a full object-graph walk
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    Recursively walks from every page object, descending into:

    * ``Stream.stream_dict`` (catches ``/SMask``, ``/Mask``, etc.)
    * ``Dictionary`` values (catches ``/XObject`` entries inside ``/Resources``,
      ``/Pattern`` resources, etc.)
    * ``Array`` elements (rare, but included for completeness)

    Any value whose ``objgen`` is in the replacement map gets
    overwritten with the canonical object.

    After this pass the duplicate Image objects have zero remaining inbound
    references and are automatically excluded when PikePDF serialises the file.

    .. note::
       Cycle detection uses a ``visited`` set keyed by ``objgen``. Inline
       (non-indirect) objects all share ``objgen == (0, 0)`` in PikePDF, so
       ``(0, 0)`` is *excluded* from the set to avoid blocking descent into
       nested inline dictionaries.
    """
    # Build replacement map
    image_hash_map: dict[bytes, pikepdf.Object] = {}
    image_replacements: dict[tuple[int, int], pikepdf.Object] = {}

    for obj in pdf.objects:
        if not isinstance(obj, Stream):
            continue
        subtype = obj.stream_dict.get(Name.Subtype)
        if subtype is None or "/Image" not in str(subtype):
            continue
        try:
            raw = _stream_content_bytes(obj)
        except Exception:
            continue
        digest = hashlib.sha256(raw).digest()
        if digest not in image_hash_map:
            image_hash_map[digest] = obj
        elif obj.objgen != image_hash_map[digest].objgen:
            image_replacements[obj.objgen] = image_hash_map[digest]

    if not image_replacements:
        return

    # Rewrite references
    visited: set[tuple[int, int]] = set()

    def _replace_in_dict(d: Any) -> None:
        for key in list(d.keys()):
            try:
                val = d[key]
            except Exception:
                continue
            val_og = getattr(val, "objgen", None)
            if val_og is not None and val_og in image_replacements:
                d[key] = image_replacements[val_og]
            else:
                _walk(val)

    def _walk(obj: Any) -> None:
        if obj is None:
            return
        og = getattr(obj, "objgen", None)
        # objgen (0, 0) is shared by ALL inline (non-indirect) objects in
        # PikePDF. Adding it to ``visited`` after the first inline dict would
        # block the walk from ever entering another inline dict, which is where
        # most nested Resources / XObject / Pattern dicts live.
        # We therefore only track *real* indirect objects for cycle detection.
        if og is not None and og != (0, 0):
            if og in visited:
                return
            visited.add(og)

        if isinstance(obj, Stream):
            _replace_in_dict(obj.stream_dict)
        elif hasattr(obj, "keys"):
            _replace_in_dict(obj)
        elif hasattr(obj, "__iter__") and not isinstance(obj, (str, bytes)):
            try:
                for i, val in enumerate(obj):
                    val_og = getattr(val, "objgen", None)
                    if val_og is not None and val_og in image_replacements:
                        obj[i] = image_replacements[val_og]
                    else:
                        _walk(val)
            except Exception:
                pass

    for page in pdf.pages:
        _walk(getattr(page, "obj", page))


def _strip_and_dedup_resources(pdf: pikepdf.Pdf) -> None:
    """Strip ``/ProcSet`` arrays and deduplicate Form XObjects.

    Walks every page's ``/Resources`` dictionary (recursing into Form
    XObjects' own ``/Resources``):

    * Deletes ``/ProcSet`` if present (obsolete since PDF 1.4).
    * Hashes each Form XObject's stored stream bytes and replaces
      duplicates with a reference to one canonical copy.

    :param pdf: An open :class:`pikepdf.Pdf` object to modify in place.
    """
    form_hash_map: dict[bytes, pikepdf.Object] = {}

    def _process_resources(resources: Any) -> None:
        if resources is None:
            return

        if Name.ProcSet in resources:
            del resources[Name.ProcSet]

        xobjects = resources.get(Name.XObject)
        if xobjects is None:
            return

        for key in list(xobjects.keys()):
            xobj = xobjects[key]
            if not isinstance(xobj, Stream):
                continue

            subtype = xobj.stream_dict.get(Name.Subtype)
            if subtype is None:
                continue

            if "/Form" in str(subtype):
                form_res = xobj.stream_dict.get(Name.Resources)
                if form_res is not None:
                    _process_resources(form_res)

                try:
                    raw = _stream_content_bytes(xobj)
                except Exception:
                    continue
                digest = hashlib.sha256(raw).digest()
                if digest not in form_hash_map:
                    form_hash_map[digest] = xobj
                elif xobj.objgen != form_hash_map[digest].objgen:
                    xobjects[key] = form_hash_map[digest]

    for page in pdf.pages:
        resources = page.get(Name.Resources)
        if resources is not None:
            _process_resources(resources)
