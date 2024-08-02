import numbers
import unittest
import xmlschema
import xml.etree.ElementTree as et
from src.read_excel import read_sheets
import xmlschema
import re

XML_SCHEMA = xmlschema.XMLSchema('https://www.dov.vlaanderen.be/xdov/schema/latest/xsd/kern/dov.xsd')

DATA_FOLDER = 'tests/data'


class ValidationNode:

    def __init__(self, element):
        self.tag = element.tag
        try:
            value = float(element.text)
        except ValueError:
            value = re.sub(r'\n( )*', ' ', element.text).strip(' ')
        except TypeError:
            value = None

        self.value = value

        self.children = [ValidationNode(child) for child in element]

    def __eq__(self, other):
        if (self.tag != other.tag) or (self.value != other.value):
            return False

        _, indices, other_indices = self.__compare_children__(other)

        return (not indices) and (not other_indices)

    def __compare_children__(self, other):
        indices = set(range(len(self.children)))
        other_indices = set(range(len(other.children)))
        matching = dict()

        if any(c1.tag != c2.tag for c1, c2 in zip(self.children, other.children)):
            return matching, indices, other_indices

        i = 0
        equal = True
        while i < len(self.children) and equal:
            match = False
            child = self.children[i]
            j = 0
            while not match and j < len(other.children):
                if j in other_indices:
                    other_child = other.children[j]
                    match = (child == other_child)
                    if match:
                        matching[i] = j
                        indices.remove(i)
                        other_indices.remove(j)
                j += 1
            equal = equal and match
            i += 1
        return matching, indices, other_indices


def xls2xml_test(xls_filename, xml_filename, sheets):
    valid_xml = ValidationNode(et.parse(xml_filename).getroot())
    generated_xml = ValidationNode(read_sheets(xls_filename, sheets, XML_SCHEMA))

    assert valid_xml == generated_xml


class BodemTemplateTest(unittest.TestCase):

    def test_bodemlocatie(self):
        xls2xml_test(f'{DATA_FOLDER}/filled_templates/bodem_template_full.xlsx',
                     f'{DATA_FOLDER}/verification_xml/bodemlocatie1.xml', ['bodemlocatie'])

    def test_bodemsite(self):
        xls2xml_test(f'{DATA_FOLDER}/filled_templates/bodem_template_full.xlsx',
                     f'{DATA_FOLDER}/verification_xml/bodemsite1.xml', ['bodemsite'])

    def test_bodemmonster(self):
        xls2xml_test(f'{DATA_FOLDER}/filled_templates/bodem_template_full.xlsx',
                     f'{DATA_FOLDER}/verification_xml/bodemmonster1.xml', ['bodemmonster'])

    def test_bodemobservatie(self):
        xls2xml_test(f'{DATA_FOLDER}/filled_templates/bodem_template_full.xlsx',
                     f'{DATA_FOLDER}/verification_xml/bodemobservatie1.xml', ['bodemobservatie'])

    def test_bodemlocatieclassificatie(self):
        xls2xml_test(f'{DATA_FOLDER}/filled_templates/bodem_template_full.xlsx',
                     f'{DATA_FOLDER}/verification_xml/bodemlocatieclassificatie1.xml', ['bodemlocatieclassificatie'])

    def test_bodemkundigeopbouw(self):
        xls2xml_test(f'{DATA_FOLDER}/filled_templates/bodem_template_full.xlsx',
                     f'{DATA_FOLDER}/verification_xml/bodemkundigeopbouw1.xml', ['bodemkundigeopbouw'])


class GrondwaterTemplateTest(unittest.TestCase):

    def test_grondwaterlocatie(self):
        xls2xml_test(f'{DATA_FOLDER}/filled_templates/grondwater_template_full.xlsx',
                     f'{DATA_FOLDER}/verification_xml/grondwaterlocatie1.xml', ['grondwaterlocatie'])

    def test_filter(self):
        xls2xml_test(f'{DATA_FOLDER}/filled_templates/grondwater_template_full.xlsx',
                     f'{DATA_FOLDER}/verification_xml/filter1.xml', ['filter'])

    def test_filtermeting(self):
        xls2xml_test(f'{DATA_FOLDER}/filled_templates/grondwater_template_full.xlsx',
                     f'{DATA_FOLDER}/verification_xml/filtermeting1.xml', ['filtermeting'])

    def test_filterdebietmeter(self):
        xls2xml_test(f'{DATA_FOLDER}/filled_templates/grondwater_template_full.xlsx',
                     f'{DATA_FOLDER}/verification_xml/filterdebietmeter1.xml', ['filterdebietmeter'])


class GeologieTemplateTest(unittest.TestCase):

    def test_boring(self):
        xls2xml_test(f'{DATA_FOLDER}/filled_templates/geologie_template_full.xlsx',
                     f'{DATA_FOLDER}/verification_xml/boring1.xml', ['boring'])

    def test_interpretaties(self):
        xls2xml_test(f'{DATA_FOLDER}/filled_templates/geologie_template_full.xlsx',
                     f'{DATA_FOLDER}/verification_xml/interpretaties1.xml', ['interpretaties'])

    def test_grondmonster(self):
        xls2xml_test(f'{DATA_FOLDER}/filled_templates/geologie_template_full.xlsx',
                     f'{DATA_FOLDER}/verification_xml/grondmonster1.xml', ['grondmonster'])


class OpdrachtTemplateTest(unittest.TestCase):

    def test_opdracht(self):
        xls2xml_test(f'{DATA_FOLDER}/filled_templates/opdracht_template_full.xlsx',
                     f'{DATA_FOLDER}/verification_xml/opdracht1.xml', ['opdracht'])


if __name__ == '__main__':
    unittest.main()
