import pandas as pd
import xml.etree.ElementTree as ET

import sys

grondwaterlocaties_tab = pd.read_excel(
    'C:/Users/RubenVijverman/PycharmProjects/xls2xml/data_voorbeeld/Data_input_dev.xlsx',
    sheet_name='grondwaterlocaties')

print(grondwaterlocaties_tab)

print('---------\n')

# root = minidom.Document()
#
# xml = root.createElement('ns3:dov-schema')
# root.appendChild(xml)
# xml.setAttribute('xmlns:ns3', 'http://kern.schemas.dov.vlaanderen.be')
#
# for i, row in list(grondwaterlocaties_tab.iterrows())[6:]:
#     grondwater_root = root.createElement('grondwaterlocatie')
#     xml.appendChild(grondwater_root)
#
#     identif = root.createElement('identificatie')
#     identif.set
#     grondwater_root.appendChild(identif)
#
# xml_str = root.toprettyxml(indent="\t")
# print(xml_str)


root = ET.Element('ns3:dov-schema')
root.set('xmlns:ns3', 'http://kern.schemas.dov.vlaanderen.be')

doc = ET.ElementTree(root)

print(ET.tostring(doc.getroot(), encoding='utf8'))

print(ET.tostring(root, encoding='utf8'))
