"""Hand the rendered front page to make.fun as the entry image.

The renderer (tools/render_news.py) produces ``news-21-nov-2026.png``.
This script only checks that file is a genuine, well-formed PNG of the
right size and shape, then copies it to ``entry.png`` inside the output
folder make.fun expects.

The output folder comes from MAKEFUN_OUTPUT_DIR; an empty value counts
as unset and the default ``/output`` is used instead.
"""

import os
import shutil
import struct
import sys

SOURCE_NAME = "news-21-nov-2026.png"
TARGET_NAME = "entry.png"
MAX_BYTES = 1048576
WANT_WIDTH = 1024
WANT_HEIGHT = 1024

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
IEND_TAIL = b"\x00\x00\x00\x00IEND\xaeB`\x82"


class EntryProblem(Exception):
    """Raised when the rendered page fails a pre-copy check."""


def source_path():
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(here, SOURCE_NAME)


def output_folder():
    folder = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    return folder


def read_source(path):
    if not os.path.isfile(path):
        raise EntryProblem("rendered page not found: " + path)
    with open(path, "rb") as handle:
        blob = handle.read()
    return blob


def check_png(blob, path):
    if len(blob) > MAX_BYTES:
        raise EntryProblem(
            "{} is {} bytes, over the {} byte limit".format(
                path, len(blob), MAX_BYTES))
    if len(blob) < 33 or blob[:8] != PNG_MAGIC:
        raise EntryProblem(path + " does not start with PNG magic bytes")
    if blob[12:16] != b"IHDR":
        raise EntryProblem(path + " has no IHDR chunk where expected")
    width, height = struct.unpack(">II", blob[16:24])
    if (width, height) != (WANT_WIDTH, WANT_HEIGHT):
        raise EntryProblem(
            "{} is {}x{}, expected {}x{}".format(
                path, width, height, WANT_WIDTH, WANT_HEIGHT))
    if blob[-12:] != IEND_TAIL:
        raise EntryProblem(path + " is missing a valid IEND trailer")


def main():
    try:
        src = source_path()
        blob = read_source(src)
        check_png(blob, src)
        folder = output_folder()
        os.makedirs(folder, exist_ok=True)
        dest = os.path.join(folder, TARGET_NAME)
        shutil.copyfile(src, dest)
    except EntryProblem as problem:
        print("error: " + str(problem), file=sys.stderr)
        return 1
    print("copied {} -> {}".format(src, dest))
    return 0


if __name__ == "__main__":
    sys.exit(main())
