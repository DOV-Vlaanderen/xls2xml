from src.dfs_schema import get_dfs_schema, get_dfs_schema_from_url, compare_nodes
import unittest


def compare_schemas(filename, omgeving):
    url = f"https://{omgeving}.dov.vlaanderen.be/xdov/schema/latest/xsd/kern/dov.xsd"

    schema_local = get_dfs_schema(filename)
    schema_url = get_dfs_schema_from_url(url)
    compare_nodes(schema_local, schema_url)


class XsdSchemaTest(unittest.TestCase):

    def test_ontwikkel(self):
        compare_schemas("xsd_schema_ontwikkel.json", "ontwikkel")

    def test_oefen(self):
        compare_schemas("xsd_schema_oefen.json", "oefen")

    def test_productie(self):
        compare_schemas("xsd_schema.json", "www")


if __name__ == '__main__':
    unittest.main()
