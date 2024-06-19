import unittest
import math
from collections import defaultdict
from unittest.mock import patch, Mock
import pandas as pd
import numpy as np
from src.read_excel import DataNode, clean_data, get_identifiers, get_partition, recursive_data_read, get_dfs_schema, \
    ChoiceNode  # Adjust the import according to your file structure


class TestDataNode(unittest.TestCase):

    def test_is_empty(self):
        node = DataNode("test")
        self.assertTrue(node.is_empty())
        node.data.append("data")
        self.assertFalse(node.is_empty())

    def test_delete_empty(self):
        node = DataNode("test")
        child_node = DataNode("child")
        node.children["child"].append(child_node)
        self.assertFalse(node.is_empty())
        node.delete_empty()
        self.assertTrue(node.is_empty())

    def test_repr(self):
        node = DataNode("test")
        self.assertEqual(repr(node), "DataNode(name=test, children=[], data=[])")


class TestCleanData(unittest.TestCase):

    def setUp(self):
        self.schema_node_mock = Mock()
        self.schema_node_mock.constraints = [{'binding': 'java.lang.String'}]

    def test_clean_data_nan(self):
        self.assertIsNone(clean_data(float('nan'), self.schema_node_mock))

    def test_clean_data_bindings(self):
        self.assertEqual(clean_data(123, self.schema_node_mock), "123")

    def test_clean_data_invalid_binding(self):
        self.schema_node_mock.constraints = [{'binding': 'invalid.binding'}]
        with self.assertRaises(NotImplementedError):
            clean_data(123, self.schema_node_mock)


class TestGetIdentifiers(unittest.TestCase):

    def test_get_identifiers_simple(self):
        node = Mock()
        node.name = 'node'
        child1 = Mock()
        child1.name = 'child1'
        child1.min_amount = 1
        child1.max_amount = 1
        child1.children = []

        node.children = [child1]
        current_lijst = []
        identifiers = []
        get_identifiers(node, current_lijst, identifiers)
        self.assertEqual(identifiers, ['child1'])

    def test_get_identifiers(self):
        node = Mock()

        child1 = Mock()
        child1.name = 'child1'
        child1.min_amount = 1
        child1.max_amount = 1
        child1.children = []

        child2 = Mock()
        child2.name = 'child2'
        child2.min_amount = 2
        child2.max_amount = 4
        child2.children = []

        child3 = Mock()
        child3.name = 'child3'
        child3.min_amount = 0
        child3.max_amount = 500
        child3.children = []

        child4 = Mock()
        child4.name = 'child4'
        child4.min_amount = 1
        child4.max_amount = 1
        child4.children = []

        sub_child1 = Mock()
        sub_child1.name = 'sub_child1'
        sub_child1.min_amount = 1
        sub_child1.max_amount = 1
        sub_child1.children = []

        sub_child2 = Mock()
        sub_child2.name = 'sub_child2'
        sub_child2.min_amount = 0
        sub_child2.max_amount = 1
        sub_child2.children = []

        child4.children = [sub_child1, sub_child2]

        child5 = DataNode('child4')
        child5.min_amount = 1
        child5.max_amount = 20

        sub_child1 = DataNode('sub_child1')
        sub_child1.min_amount = 1
        sub_child1.max_amount = 1
        sub_child1.children = []

        sub_child2 = DataNode('sub_child2')
        sub_child2.min_amount = 0
        sub_child2.max_amount = 1
        sub_child2.children = []

        child5.children = [sub_child1, sub_child2]

        node.children = [child1, child2, child3, child4, child5]
        current_lijst = []
        identifiers = []
        get_identifiers(node, current_lijst, identifiers)
        self.assertEqual(identifiers, ['child1', 'child4-sub_child1'])


class TestGetPartition(unittest.TestCase):

    def setUp(self):
        self.df = pd.DataFrame({
            'id': [1, 1, 1, 2, float('nan'), float('nan')],
            'location-pos': [0, 0, 1, 1, float('nan'), float('nan')],
            'location-name': ['a', 'b', 'c', 'd', float('nan'), float('nan')],
            'value': [10, 20, 30, 40, 50, 60]
        })

        self.filter = np.array([True] * 6)

        self.root = Mock()
        self.root.name = 'root'
        self.root.min_amount = 1
        self.root.max_amount = 1
        self.root.children = []

        child1 = Mock()
        child1.name = 'id'
        child1.max_amount = 1
        child1.min_amount = 1
        child1.children = []
        self.root.children.append(child1)

        child3 = Mock()
        child3.name = 'location'
        child3.max_amount = 1
        child3.min_amount = 1
        child3.children = []
        self.root.children.append(child3)

        subchild1 = Mock()
        subchild1.name = 'pos'
        subchild1.max_amount = 1
        subchild1.min_amount = 1
        subchild1.children = []
        child3.children.append(subchild1)

        subchild2 = Mock()
        subchild2.name = 'name'
        subchild2.max_amount = 1
        subchild2.min_amount = 0
        subchild2.children = []
        child3.children.append(subchild2)

        child4 = Mock()
        child4.name = 'value'
        child4.max_amount = math.inf
        child4.min_amount = 0
        child4.children = []
        self.root.children.append(child4)

    def test_get_partition(self):
        current_lijst = []
        partitions = get_partition(self.df, self.filter, current_lijst, self.root)
        self.assertEqual(len(partitions), 3)
        self.assertTrue(np.all(partitions[0] == np.array([True, True, False, False, False, False])))
        self.assertTrue(np.all(partitions[1] == np.array([False, False, True, False, False, False])))
        self.assertTrue(np.all(partitions[2] == np.array([False, False, False, True, True, True])))


class TestRecursiveDataRead(unittest.TestCase):

    def setUp(self):
        self.df = pd.DataFrame({
            'id': [1, 2, 3],
            'value': [10, 20, 30]
        })
        self.filter = np.array([True, True, True])
        self.node_mock = Mock()
        self.node_mock.children = []
        self.node_mock.name = 'root'

    @patch('src.read_excel.clean_data', return_value=10)  # Adjust the import according to your file structure
    def test_recursive_data_read(self, clean_data_mock):
        current_lijst = ['id']
        data_node = recursive_data_read(self.df, self.filter, self.node_mock, current_lijst)
        self.assertEqual(data_node.name, 'root')
        self.assertEqual(data_node.data, [10])


if __name__ == '__main__':
    unittest.main()
