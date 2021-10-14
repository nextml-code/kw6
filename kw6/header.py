import re
import xml.etree.ElementTree as ET


CHILD_TEXT_PATTERN = re.compile(r"""
kw6Byte = "(?P<byte_position>\d*)"
kw6Pos = "(?P<kw6_pos>\d*)"
""")


def positions(header):
    root = ET.fromstring(header)
    positions = [
        CHILD_TEXT_PATTERN.match(child.text).groupdict()
        for child in root
        if child.tag == "kw6Index"
    ]

    return {
        int(position["kw6_pos"]) // 10: int(position["byte_position"])
        for position in positions
    }


def test_positions():
    from pathlib import Path
    assert positions(
        Path("tests/owlsbtlwear20210409_132606_2011TA.hdr").read_text()
    )[0] == 19
