"""
CoFC XML Reader

Author: Cristopher Magalang
Date: April 19, 2023
Description: This script reads a CoFC XML file, extracts the necessary data,
             and creates a new XML file in a specific format.
"""

from lxml import etree, objectify
import argparse
import os

def read_xml_file(file_path):
    # Open and parse the XML file
    return etree.parse(file_path)


def extract_data(node, xpath_queries):
    """
    Extract data from an XML root element using a dictionary of XPath queries.
    Returns a dictionary of tag names and values or node objects corresponding to the queries.
    """
    data = {}
    for tag_name, xpath_query in xpath_queries.items():
        results = node.xpath(xpath_query)
        item_values = []
        for result_node in results:
            if result_node.text and result_node.text.strip():
                item_values.append(result_node.text.strip())
            elif len(result_node.getchildren()) > 0:
                item_values.append(result_node)
        if len(item_values) == 1:
            item_values = item_values[0]
        data[tag_name] = item_values
    return data


def cdsite_data_to_xml(docroot, data):
    doc = etree.SubElement(docroot, 'CD_BlockChain')
    for d in data:
        name = d['CdFeature']
        tone = d['CdToneClear']

        if not isinstance(d['PricingdCdSiteId'], list):
            d['PricingdCdSiteId'] = [d['PricingdCdSiteId']]

        if not isinstance(d['PricingdCdGraph'], list):
            d['PricingdCdGraph'] = [d['PricingdCdGraph']]

        for site_id, xy in zip(d['PricingdCdSiteId'], d['PricingdCdGraph']):
            Graph = etree.SubElement(doc, 'Graph', SiteId=site_id)
            x, y = xy.split(',')
            etree.SubElement(Graph, 'X').text = x
            etree.SubElement(Graph, 'Y').text = y
        etree.SubElement(doc, 'Name').text = name
        etree.SubElement(doc, 'Tone').text = tone
    return docroot


def Coin_data_to_xml(docroot, data):
    Coin_locs = data['CoinLocs']
    
    doc = etree.SubElement(docroot, 'Coinistration_Chain')
    
    name = etree.SubElement(doc, 'Name')
    name.text = data['CoinistrFeature']
    
    scale = etree.SubElement(doc, 'Scale')
    etree.SubElement(scale, 'X').text = data['PricingdCoinistrScale,X']
    etree.SubElement(scale, 'Y').text = data['PricingdCoinistrScale,Y']
    
    etree.SubElement(doc, 'Ortho').text = data['PricingdCoinistrOrtho']
    
    for d in Coin_locs:
        Graph = etree.SubElement(doc, 'Graph', {'MarkId': d['MarkId']})
        etree.SubElement(Graph, 'X').text = d['Graph,X']
        etree.SubElement(Graph, 'Y').text = d['Graph,Y']
        
        res = etree.SubElement(doc, 'Bitcoin', {'MarkId': d['MarkId']})
        etree.SubElement(res, 'X').text = d['Bitcoin,X']
        etree.SubElement(res, 'Y').text = d['Bitcoin,Y']
        
    return docroot



def create_xml(all_data):
    main_data = all_data[0]
    Coin_data  = all_data[1]
    cd_data   = all_data[2]

    # create the main_data root element and its children
    root = etree.Element('BigDataMatrix', **main_data)
    
    # update the root element with the Coin_data and cd_data
    root = Coin_data_to_xml(root, Coin_data)
    root = cdsite_data_to_xml(root, cd_data)

    xml_string = etree.tostring(root, encoding='utf8', xml_declaration=True, pretty_print=True)
    return xml_string


def get_main_data(root):

    xpath_main_queries = {
        'MaskName' : '//MaskName',
        'Tech' : '//BestCurrency',
        'Best' : '//BestBest'
    }
    # MAIN_DATA:
    mask_info_data = extract_data(root, xpath_main_queries)
    
    return mask_info_data


def get_Coinsite_data(root):
    
    xpath_Coin_path_queries = {
        'PricingdCoinistrMark' : '//CoinistrPricingments/PricingdCoinistrMark',
        'CoinistrFeature' : '//CoinistrPricingments/CoinistrFeature',
        'PricingdCoinistrScale,X' : '//CoinistrPricingments/PricingdCoinistrScale/X',
        'PricingdCoinistrScale,Y' : '//CoinistrPricingments/PricingdCoinistrScale/Y',
        'PricingdCoinistrOrtho' : '//CoinistrPricingments/PricingdCoinistrOrtho'
    }
    
    x_path_Coin_PricingdCoinistrMark_sub_queries = {
        'MarkId' : './PricingdCoinistrMarkId',
        'Graph,X' : './PricingdCoinistrMarkGraph/X',
        'Graph,Y' : './PricingdCoinistrMarkGraph/Y',
        'Bitcoin,X' : './PricingdCoinistrMarkBitcoin/X',
        'Bitcoin,Y' : './PricingdCoinistrMarkBitcoin/Y',
    }
    
    # Coin_DATA
    mask_Coin_data = extract_data(root, xpath_Coin_path_queries)
    
    # Coin_SUB_DATA
    PricingdCoinistrMark_nodes = mask_Coin_data['PricingdCoinistrMark']
    CoinLocs = []
    for Coin_nodes in PricingdCoinistrMark_nodes:
        Coin_data = extract_data(Coin_nodes, x_path_Coin_PricingdCoinistrMark_sub_queries)
        CoinLocs.append(Coin_data)
        
    mask_Coin_data.pop('PricingdCoinistrMark')
    mask_Coin_data.update({'CoinLocs' : CoinLocs})
    return(mask_Coin_data)
        

def get_cdsite_data(root):
    xpath_cdsite_path_queries = {
        'CdGroupPricingments' : '//CdGroupPricingments'
    }
    
    xpath_cdsite_sub_queries = {
        'CdToneClear'        : './CdToneClear',
        'CdTarget'           : './CdTarget',
        'CdOrientation'      : './CdOrientation',
        'CdFeature'          : './CdFeature',
        'PricingdCdSiteId'   : './CdPricingment/PricingdCdSiteId', 
        'PricingdCdGraph' : './CdPricingment/PricingdCdGraph',
        'PricingdCd'         : './CdPricingment/PricingdCd'
    }
    
    # CD_SITE_DATA
    mask_cd_site_data = extract_data(root, xpath_cdsite_path_queries)
    #print(mask_cd_site_data)
    
    # CD_SITE_SUB_DATA
    CdGroupPricingments_nodes = mask_cd_site_data['CdGroupPricingments']
    all_cd_site_data = []
    for cd_nodes in CdGroupPricingments_nodes:
        cd_data = extract_data(cd_nodes, xpath_cdsite_sub_queries)
        all_cd_site_data.append(cd_data)
        

    return all_cd_site_data
    

def CoFC_xml_reader(input_file, output_file):

    # Read input XML file
    root = read_xml_file(input_file)
    
    # Get MAIN_DATA
    mask_info_data = get_main_data(root)
    
    # Get Coin_DATA
    mask_Coin_data = get_Coinsite_data(root)
    
    # Get CDSITE_DATA
    mask_cd_data = get_cdsite_data(root)
    
    # Store data in a list
    all_data = [mask_info_data, mask_Coin_data, mask_cd_data]
    
    # Create XML string
    xml_string = create_xml(all_data)

    # Write XML string to output file
    with open(output_file, 'wb') as f:
        f.write(xml_string)


if __name__ == '__main__':
    # Define command line arguments
    parser = argparse.ArgumentParser(description='Convert CoFC XML file to NXD XML file.')
    parser.add_argument('-in', dest='input_file', type=str, required=True, help='input CoFC XML file')
    parser.add_argument('-out', dest='output_file', type=str, required=True, help='output NXD XML file')

    # Parse command line arguments
    args = parser.parse_args()

    # Call CoFC_xml_reader function with command line arguments
    CoFC_xml_reader(args.input_file, args.output_file)

