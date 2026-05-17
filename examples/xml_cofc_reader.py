"""CLI: convert a CoFC XML file to the target XML format."""

import argparse

from python_light_scripts.xmltools.cofc_reader import cofc_xml_reader

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert a CoFC XML file to NXD XML.")
    parser.add_argument("-in", dest="input_file", required=True, help="input CoFC XML file")
    parser.add_argument("-out", dest="output_file", required=True, help="output NXD XML file")
    args = parser.parse_args()

    cofc_xml_reader(args.input_file, args.output_file)
