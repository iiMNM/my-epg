#!/usr/bin/env python3
"""Download several XMLTV (.xml.gz) EPG files and merge them into one epg.xml / epg.xml.gz."""
import gzip
import io
import sys
import urllib.request
import xml.etree.ElementTree as ET

SOURCES = [
    "https://www.open-epg.com/files/egypt2.xml.gz",
    "https://www.open-epg.com/files/qatar5.xml.gz",
    "https://www.open-epg.com/files/qatar6.xml.gz",
    "https://www.open-epg.com/files/saudiarabia.xml.gz",
    "https://www.open-epg.com/files/qatar1.xml.gz",
]

OUT_XML = "epg.xml"
OUT_GZ = "epg.xml.gz"


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (EPG merger)"})
    with urllib.request.urlopen(req, timeout=120) as r:
        data = r.read()
    if data[:2] == b"\x1f\x8b":  # gzip magic
        data = gzip.decompress(data)
    return data


def main():
    channels = {}      # id -> element
    programmes = {}    # (channel, start) -> element
    ok = 0

    for url in SOURCES:
        try:
            root = ET.parse(io.BytesIO(fetch(url))).getroot()
        except Exception as e:  # keep going if one source fails
            print(f"[!] failed {url}: {e}", file=sys.stderr)
            continue
        ok += 1
        nc = np = 0
        for ch in root.findall("channel"):
            cid = ch.get("id")
            if cid and cid not in channels:
                channels[cid] = ch
                nc += 1
        for pr in root.findall("programme"):
            key = (pr.get("channel"), pr.get("start"))
            if key not in programmes:
                programmes[key] = pr
                np += 1
        print(f"[+] {url}: {nc} channels, {np} programmes")

    if ok == 0:
        sys.exit("No source could be downloaded; keeping the old file.")

    tv = ET.Element("tv", {"generator-info-name": "merged-epg"})
    tv.extend(channels.values())
    tv.extend(sorted(programmes.values(), key=lambda p: (p.get("channel") or "", p.get("start") or "")))

    xml_bytes = ET.tostring(tv, encoding="utf-8", xml_declaration=True)
    with open(OUT_XML, "wb") as f:
        f.write(xml_bytes)
    with gzip.GzipFile(OUT_GZ, "wb", mtime=0) as f:  # mtime=0 -> no change when content is the same
        f.write(xml_bytes)

    print(f"[=] total: {len(channels)} channels, {len(programmes)} programmes -> {OUT_XML}, {OUT_GZ}")


if __name__ == "__main__":
    main()
