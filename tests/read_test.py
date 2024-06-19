import numbers
import unittest
import xmlschema
import xml.etree.ElementTree as et
from src.read_excel import read_sheets


class ValidationNode:

    def __init__(self, element):
        self.tag = element.tag
        try:
            value = float(element.text)
        except ValueError:
            value = element.text

        self.value = value

        self.children = [ValidationNode(child) for child in element]

    def __eq__(self, other):
        if (self.tag != other.tag) or (self.value != other.value):
            return False

        matching, indices, other_indices = self.__compare_children__(other)

        return not indices and not other_indices

    def __compare_children__(self, other):
        if any(c1.tag != c2.tag for c1, c2 in zip(self.children, other.children)):
            return False

        indices = set(range(len(self.children)))
        other_indices = set(range(len(other.children)))
        matching = dict()
        i = 0
        while i < len(self.children):
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
            i += 1
        return matching, indices, other_indices


def xls2xml_test(xls_filename, xml_filename, sheets):
    valid_xml = ValidationNode(et.parse(xml_filename).getroot())
    generated_xml = ValidationNode(read_sheets(xls_filename, sheets))

    assert valid_xml == generated_xml







class BodemTemplateTest(unittest.TestCase):

    def test_bodemlocatie(self):
        xls2xml_test('./data/filled_templates/bodem_template_full.xlsx',
                     './data/verification_xml/bodemlocatie1.xml', ['bodemlocatie'])

    def test_bodemsite(self):
        xls2xml_test('./data/filled_templates/bodem_template_full.xlsx',
                     './data/verification_xml/bodemsite1.xml', ['bodemsite'])


class GrondwaterTemplateTest(unittest.TestCase):

    def test_grondwaterlocatie(self):
        xls2xml_test('./data/filled_templates/bodem_template_full.xlsx',
                     './data/verification_xml/bodemlocatie1.xml', ['bodemlocatie'])



if __name__ == '__main__':
    unittest.main()