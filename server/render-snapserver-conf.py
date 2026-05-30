#!/usr/bin/env python3
import sys
from pathlib import Path

SOURCE_LINE = (
    "source = pipe:///tmp/snapfifo?"
    "name=Spotify&sampleformat=48000:16:2&codec=pcm&chunk_ms=20"
)
BUFFER_LINE = "buffer = 6000"


def replace_or_append(lines, prefix, replacement):
    for index, line in enumerate(lines):
        if line.startswith(prefix):
            lines[index] = replacement
            return
    lines.append(replacement)


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: render-snapserver-conf.py /etc/snapserver.conf")

    path = Path(sys.argv[1])
    lines = path.read_text().splitlines()
    replace_or_append(lines, "source = pipe:///tmp/snapfifo?", SOURCE_LINE)
    replace_or_append(lines, "buffer =", BUFFER_LINE)
    path.write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
