#!/usr/bin/env python3
"""Check that every image a manifest references actually exists in this repo.

Manifests reference icons and screenshots by absolute URL rather than shipping
them inside the store payload, and those URLs point at our own bucket, which is
populated by syncing this directory. So a URL is only good if the matching file
is committed here under the matching path.

Nothing enforced that, and four separate ways of getting it wrong had all
reached main at once:

  - an icon field left empty
  - a relative path ("icon.png"), which resolves against the store host, not
    the app directory
  - a URL still pointing at icon.casaos.io, jsdelivr or a vendor's own site
  - a URL correctly under our prefix, naming a file that does not exist

Run with no arguments from the repository root.
"""

import glob
import json
import os
import re
import struct
import sys

S3_PREFIX = "https://nimoos-public.s3.us-east-2.amazonaws.com/nimoos/appstore/"

# Manifests come in three shapes. Matching only docker-compose.yml, as an
# earlier sweep did, silently skips 53 apps.
MANIFEST_GLOBS = ("Apps/*/*.yml", "Apps/*/*.yaml", "Apps/*/*.json")

IMAGE_URL = re.compile(r'https?://[^\s"\'<>,\]]+\.(?:png|jpg|jpeg|svg|webp|gif)', re.I)

# An app icon appears both at the top level of x-casaos (two spaces) and inside
# each service's own x-casaos block (six). Anchoring to a fixed indent misses
# the nested ones.
ICON_FIELD = re.compile(r"^([ \t]+)icon:[ \t]*(.*)$", re.M)


def png_dimensions(path):
    with open(path, "rb") as handle:
        head = handle.read(26)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", head[16:24])


def check():
    problems = []
    manifests = sorted({p for pattern in MANIFEST_GLOBS for p in glob.glob(pattern)})
    urls_checked = 0

    for manifest in manifests:
        app = manifest.split(os.sep)[1]
        with open(manifest, encoding="utf-8") as handle:
            text = handle.read()

        if manifest.endswith(".json"):
            try:
                json.loads(text)
            except ValueError as exc:
                problems.append((manifest, "invalid JSON", str(exc)))

        for url in IMAGE_URL.findall(text):
            urls_checked += 1
            if not url.startswith(S3_PREFIX):
                problems.append((manifest, "not served by us", url))
                continue
            local = url[len(S3_PREFIX):]
            if not os.path.isfile(local):
                problems.append((manifest, "no such file in repo", local))
                continue
            size = png_dimensions(local)
            if size and max(size) <= 2:
                problems.append(
                    (manifest, "placeholder pixel, not artwork", "%s (%dx%d)" % (local, *size))
                )

        for _indent, raw in ICON_FIELD.findall(text):
            value = raw.strip().strip("\"'")
            if not value:
                problems.append((manifest, "icon field is empty", ""))
            elif not value.startswith("http"):
                problems.append((manifest, "icon is a relative path", value))

    print("manifests scanned : %d" % len(manifests))
    print("image URLs checked: %d" % urls_checked)

    if not problems:
        print("all artwork resolves to a file in this repository")
        return 0

    print("\n%d problem(s):\n" % len(problems))
    width = max(len(kind) for _m, kind, _d in problems)
    for manifest, kind, detail in problems:
        print("  %-34s %-*s %s" % (manifest, width, kind, detail))
    print(
        "\nEvery icon and screenshot must live in this repository under the path its\n"
        "URL names, so that the S3 sync publishes it. Add the file, or point the\n"
        "manifest at one that exists."
    )
    return 1


if __name__ == "__main__":
    sys.exit(check())
