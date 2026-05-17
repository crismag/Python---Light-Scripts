"""Tests for python_light_scripts.xmltools.cofc_reader.

Uses the sample input at ``tests/data/cofc_sample.xml``. Skipped if ``lxml``
is not installed.
"""

from pathlib import Path

import pytest

lxml_etree = pytest.importorskip("lxml.etree")

from python_light_scripts.xmltools import cofc_reader  # noqa: E402

DATA = Path(__file__).parent / "data"
SAMPLE = DATA / "cofc_sample.xml"


def test_get_main_data():
    root = cofc_reader.read_xml_file(str(SAMPLE))
    main = cofc_reader.get_main_data(root)
    assert main == {"MaskName": "MASK01", "Tech": "N7", "Best": "BEST_A"}


def test_get_coinsite_data_has_two_marks():
    root = cofc_reader.read_xml_file(str(SAMPLE))
    coin = cofc_reader.get_coinsite_data(root)
    assert coin["CoinistrFeature"] == "FEAT_C"
    assert len(coin["CoinLocs"]) == 2
    assert {loc["MarkId"] for loc in coin["CoinLocs"]} == {"M1", "M2"}


def test_get_cdsite_data():
    root = cofc_reader.read_xml_file(str(SAMPLE))
    cd = cofc_reader.get_cdsite_data(root)
    assert len(cd) == 1
    assert cd[0]["CdFeature"] == "CDF1"
    assert cd[0]["PricingdCdGraph"] == "5,6"


def test_cofc_xml_reader_end_to_end(tmp_path):
    out = tmp_path / "out.xml"
    result = cofc_reader.cofc_xml_reader(str(SAMPLE), str(out))

    assert out.exists()
    parsed = lxml_etree.fromstring(result)

    # Root carries the main data as attributes.
    assert parsed.tag == "BigDataMatrix"
    assert parsed.get("MaskName") == "MASK01"

    # Coin chain: two Graph + two Bitcoin elements.
    chain = parsed.find("Coinistration_Chain")
    assert chain.findtext("Name") == "FEAT_C"
    assert len(chain.findall("Graph")) == 2
    assert len(chain.findall("Bitcoin")) == 2

    # CD chain: one site with split X/Y coordinates.
    cd_block = parsed.find("CD_BlockChain")
    graph = cd_block.find("Graph")
    assert graph.get("SiteId") == "S1"
    assert graph.findtext("X") == "5"
    assert graph.findtext("Y") == "6"


def test_parser_does_not_resolve_external_entities(tmp_path):
    """An XXE payload must not be expanded into document content."""
    secret = tmp_path / "secret.txt"
    secret.write_text("TOP-SECRET")
    malicious = tmp_path / "xxe.xml"
    malicious.write_text(
        f'<?xml version="1.0"?>\n'
        f'<!DOCTYPE r [<!ENTITY x SYSTEM "file://{secret}">]>\n'
        f"<r>&x;</r>"
    )

    tree = cofc_reader.read_xml_file(str(malicious))
    # With resolve_entities=False the secret is never inlined.
    assert "TOP-SECRET" not in lxml_etree.tostring(tree, encoding="unicode")
