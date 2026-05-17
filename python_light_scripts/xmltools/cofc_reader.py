"""Read a "CoFC" XML file and re-emit it in a target XML format.

Productionized from ``xml_parsers/metro_coin_parsers.demo.altered.py``: type
hints and docstrings added, pure logic kept separate from the CLI (which
lives in ``examples/xml_cofc_reader.py``). Behaviour preserved.

HARDENING (Phase 3): parsing uses an XXE-hardened lxml parser.

Author: Cristopher Magalang — Date: April 19, 2023
"""

from __future__ import annotations

from typing import Any

from lxml import etree


def _safe_parser() -> etree.XMLParser:
    """Build an lxml parser hardened against XXE / entity-expansion attacks.

    Disables external-entity resolution and network access so a malicious
    ``<!ENTITY ...>`` cannot read local files or exfiltrate data.
    """
    return etree.XMLParser(resolve_entities=False, no_network=True, dtd_validation=False)


def read_xml_file(file_path: str) -> etree._ElementTree:
    """Open and parse an XML file with an XXE-hardened parser."""
    return etree.parse(file_path, _safe_parser())


def extract_data(node: Any, xpath_queries: dict[str, str]) -> dict[str, Any]:
    """Extract data from an XML element using a dict of XPath queries.

    Args:
        node: an lxml element (or tree) to query.
        xpath_queries: mapping of result key -> XPath expression.

    Returns:
        A dict mapping each key to its text value(s) or child node(s). A key
        with a single match is unwrapped from its list.
    """
    data: dict[str, Any] = {}
    for tag_name, xpath_query in xpath_queries.items():
        results = node.xpath(xpath_query)
        item_values: list[Any] = []
        for result_node in results:
            if result_node.text and result_node.text.strip():
                item_values.append(result_node.text.strip())
            elif len(result_node.getchildren()) > 0:
                item_values.append(result_node)
        data[tag_name] = item_values[0] if len(item_values) == 1 else item_values
    return data


def cdsite_data_to_xml(docroot: Any, data: list[dict[str, Any]]) -> Any:
    """Append CD-site records to ``docroot`` as a ``<CD_BlockChain>`` element."""
    doc = etree.SubElement(docroot, "CD_BlockChain")
    for d in data:
        name = d["CdFeature"]
        tone = d["CdToneClear"]

        if not isinstance(d["PricingdCdSiteId"], list):
            d["PricingdCdSiteId"] = [d["PricingdCdSiteId"]]

        if not isinstance(d["PricingdCdGraph"], list):
            d["PricingdCdGraph"] = [d["PricingdCdGraph"]]

        for site_id, xy in zip(d["PricingdCdSiteId"], d["PricingdCdGraph"]):
            graph = etree.SubElement(doc, "Graph", SiteId=site_id)
            x, y = xy.split(",")
            etree.SubElement(graph, "X").text = x
            etree.SubElement(graph, "Y").text = y
        etree.SubElement(doc, "Name").text = name
        etree.SubElement(doc, "Tone").text = tone
    return docroot


def coin_data_to_xml(docroot: Any, data: dict[str, Any]) -> Any:
    """Append coin-registration records to ``docroot``."""
    coin_locs = data["CoinLocs"]

    doc = etree.SubElement(docroot, "Coinistration_Chain")

    name = etree.SubElement(doc, "Name")
    name.text = data["CoinistrFeature"]

    scale = etree.SubElement(doc, "Scale")
    etree.SubElement(scale, "X").text = data["PricingdCoinistrScale,X"]
    etree.SubElement(scale, "Y").text = data["PricingdCoinistrScale,Y"]

    etree.SubElement(doc, "Ortho").text = data["PricingdCoinistrOrtho"]

    for d in coin_locs:
        graph = etree.SubElement(doc, "Graph", {"MarkId": d["MarkId"]})
        etree.SubElement(graph, "X").text = d["Graph,X"]
        etree.SubElement(graph, "Y").text = d["Graph,Y"]

        res = etree.SubElement(doc, "Bitcoin", {"MarkId": d["MarkId"]})
        etree.SubElement(res, "X").text = d["Bitcoin,X"]
        etree.SubElement(res, "Y").text = d["Bitcoin,Y"]

    return docroot


# Backwards-compatible alias for the original (capitalized) function name.
Coin_data_to_xml = coin_data_to_xml


def create_xml(all_data: list[Any]) -> bytes:
    """Build the target XML document from ``[main, coin, cd]`` data.

    Returns the serialized XML as bytes.
    """
    main_data, coin_data, cd_data = all_data[0], all_data[1], all_data[2]

    root = etree.Element("BigDataMatrix", **main_data)
    root = coin_data_to_xml(root, coin_data)
    root = cdsite_data_to_xml(root, cd_data)

    return etree.tostring(root, encoding="utf8", xml_declaration=True, pretty_print=True)


def get_main_data(root: Any) -> dict[str, Any]:
    """Extract the top-level mask info from the source XML."""
    xpath_main_queries = {
        "MaskName": "//MaskName",
        "Tech": "//BestCurrency",
        "Best": "//BestBest",
    }
    return extract_data(root, xpath_main_queries)


def get_coinsite_data(root: Any) -> dict[str, Any]:
    """Extract coin-registration data from the source XML."""
    xpath_coin_path_queries = {
        "PricingdCoinistrMark": "//CoinistrPricingments/PricingdCoinistrMark",
        "CoinistrFeature": "//CoinistrPricingments/CoinistrFeature",
        "PricingdCoinistrScale,X": "//CoinistrPricingments/PricingdCoinistrScale/X",
        "PricingdCoinistrScale,Y": "//CoinistrPricingments/PricingdCoinistrScale/Y",
        "PricingdCoinistrOrtho": "//CoinistrPricingments/PricingdCoinistrOrtho",
    }

    sub_queries = {
        "MarkId": "./PricingdCoinistrMarkId",
        "Graph,X": "./PricingdCoinistrMarkGraph/X",
        "Graph,Y": "./PricingdCoinistrMarkGraph/Y",
        "Bitcoin,X": "./PricingdCoinistrMarkBitcoin/X",
        "Bitcoin,Y": "./PricingdCoinistrMarkBitcoin/Y",
    }

    mask_coin_data = extract_data(root, xpath_coin_path_queries)

    # extract_data unwraps a single match; normalize back to a list so a
    # document with exactly one mark is not mistaken for an iterable of
    # child elements.
    mark_nodes = mask_coin_data["PricingdCoinistrMark"]
    if not isinstance(mark_nodes, list):
        mark_nodes = [mark_nodes]
    coin_locs = [extract_data(node, sub_queries) for node in mark_nodes]

    mask_coin_data.pop("PricingdCoinistrMark")
    mask_coin_data.update({"CoinLocs": coin_locs})
    return mask_coin_data


# Backwards-compatible alias for the original function name.
get_Coinsite_data = get_coinsite_data


def get_cdsite_data(root: Any) -> list[dict[str, Any]]:
    """Extract CD-site data from the source XML."""
    xpath_cdsite_path_queries = {"CdGroupPricingments": "//CdGroupPricingments"}

    xpath_cdsite_sub_queries = {
        "CdToneClear": "./CdToneClear",
        "CdTarget": "./CdTarget",
        "CdOrientation": "./CdOrientation",
        "CdFeature": "./CdFeature",
        "PricingdCdSiteId": "./CdPricingment/PricingdCdSiteId",
        "PricingdCdGraph": "./CdPricingment/PricingdCdGraph",
        "PricingdCd": "./CdPricingment/PricingdCd",
    }

    mask_cd_site_data = extract_data(root, xpath_cdsite_path_queries)

    # Normalize a single unwrapped match back to a list (see get_coinsite_data).
    cd_group_nodes = mask_cd_site_data["CdGroupPricingments"]
    if not isinstance(cd_group_nodes, list):
        cd_group_nodes = [cd_group_nodes]
    return [extract_data(node, xpath_cdsite_sub_queries) for node in cd_group_nodes]


def cofc_xml_reader(input_file: str, output_file: str) -> bytes:
    """Read a CoFC XML file and write the reformatted XML to ``output_file``.

    Returns the serialized XML as bytes.
    """
    root = read_xml_file(input_file)

    all_data = [
        get_main_data(root),
        get_coinsite_data(root),
        get_cdsite_data(root),
    ]
    xml_string = create_xml(all_data)

    with open(output_file, "wb") as f:
        f.write(xml_string)
    return xml_string
