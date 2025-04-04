import math
from collections import defaultdict
import xmlschema
import pandas as pd
import numpy as np
from src.dfs_schema import ChoiceNode, SequenceNode, get_dfs_schema, get_XML_schema
import traceback
from pathlib import Path
import os
import warnings
import dateutil.parser as parser
from tqdm import tqdm

from ordered_set import OrderedSet

warnings.filterwarnings("ignore", message="Data Validation extension is not supported and will be removed")

PROJECT_ROOT = Path(os.path.dirname(os.path.dirname(__file__)))


class DataNode:
    """
    Represents a node in the data tree.
    """

    def __init__(self, name):
        self.name = name
        self.children = defaultdict(list)
        self.data = []

    def is_empty(self) -> bool:
        """
       Checks if the data node is empty.

       Returns:
           bool: True if the data node is empty, False otherwise.
       """
        return len(self.data) == 0 and len(self.children.keys()) == 0

    def delete_empty(self) -> None:
        """
        Deletes empty child nodes recursively.
        """
        to_pop = []
        for key, property_children in self.children.items():
            property_can_be_removed = True
            for child in property_children:
                child.delete_empty()
                property_can_be_removed = property_can_be_removed and child.is_empty()
            if property_can_be_removed:
                to_pop.append(key)

        for key in to_pop:
            self.children.pop(key)

    def __repr__(self) -> str:
        return f'DataNode(name={self.name}, children=[{", ".join(str(key) + ":" + str(len(val)) for key, val in self.children.items() if len(val) > 0)}], data={self.data})'


def parse_date(d):
    if isinstance(d, str):
        d = parser.parse(d, dayfirst=True)
    return d.strftime("%Y-%m-%d")


def parse_time(t):
    if isinstance(t, str):
        t = parser.parse(t, dayfirst=True)
    return t.strftime("%H:%M:%S")


def parse_float(f):
    if isinstance(f, str):
        f = float(f.replace(',', '.'))

    return float(f)


def clean_data(data, schema_node):
    """
    Cleans the data according to schema constraints.

    Args:
        data (Any): Data to be cleaned.
        schema_node (Node): Schema node containing constraints.

    Returns:
        Any: Cleaned data.
    """

    if isinstance(data, float) and math.isnan(data):
        return None
    else:

        cleaner = {'java.lang.Boolean': lambda x: bool(x),
                   'java.math.BigInteger': lambda x: int(x),
                   'java.sql.Date': parse_date,
                   'java.math.BigDecimal': parse_float,
                   'java.lang.Double': parse_float,
                   'java.lang.String': lambda x: str(x),
                   'java.net.URI': lambda x: str(x),
                   'java.sql.Time': parse_time,
                   'java.lang.Object': lambda x: str(x)}

        binding = schema_node.binding
        if binding:
            try:
                data = cleaner[binding](data)
            except KeyError:
                print(binding)
                raise NotImplementedError(f'{data} in node {schema_node} has {binding}')
            except AttributeError:
                raise AttributeError(f'{data} in node {schema_node} is not {binding}')

        return data


def get_identifiers(node, current_lijst, identifiers):
    """
    Retrieves identifiers for data partitioning.

    Args:
        node (Node): Current node in the schema tree.
        current_lijst (List[str]): Current list of identifiers.
        identifiers (List[str]): List to store final identifiers.
    """
    # if 'choice' in node.name:
    #     return

    relevant_children = [c for c in node.children if c.max_amount <= 1]

    for c in relevant_children:
        current_lijst.append(c.name)
        if not c.children:
            identifiers.append('-'.join(current_lijst))
        else:
            get_identifiers(c, current_lijst, identifiers)
        del current_lijst[-1]


def get_partition(df, filter, current_lijst, node):
    """
    Performs data partitioning based on identifiers.

    Args:
        df (pd.DataFrame): DataFrame containing data.
        filter (np.ndarray): Boolean filter indicating relevant rows.
        current_lijst (List[str]): Current list of identifiers.
        node (Node): Current node in the schema tree.

    Returns:
        List[np.ndarray]: List of filters for data partitioning.
    """

    identifiers = []
    get_identifiers(node, current_lijst, identifiers)
    possibilities = OrderedSet()
    identifiers = [i for i in identifiers if i in df.columns]

    last_row = None
    for i, row in df[filter].loc[:, identifiers].iterrows():
        if last_row is None or not all(
                [(x == y or (isinstance(x, float) and math.isnan(x))) for x, y in zip(tuple(row), last_row)]):
            last_row = tuple(row)
            possibilities.add(tuple(row))

    pos2index = {pos: i for i, pos in enumerate(possibilities)}
    new_filters = [np.zeros(df.shape[0], dtype=bool) for _ in possibilities]

    prev_row = None
    prev_pos = None

    for i, (index, row) in enumerate(df.loc[:, identifiers].iterrows()):

        if filter[i]:

            if prev_row is not None and all([(x == y or (isinstance(x, float) and math.isnan(x))) for x, y in
                                             zip(tuple(row), prev_row)]):
                new_filters[prev_pos][i] = True

            else:
                j = pos2index[tuple(row)]
                new_filters[j][i] = True
                prev_row = tuple(row)
                prev_pos = j

    new_filters = [filter * nf for nf in new_filters]

    assert not new_filters or all(sum(new_filters) == filter), 'Not a perfect partition?'
    return new_filters


def recursive_data_read(df, schema_node, current_lijst) -> DataNode:
    """
    Recursively reads data from DataFrame and constructs data nodes.

    Args:
        df (pd.DataFrame): DataFrame containing data.
        filter (np.ndarray): Boolean filter indicating relevant rows.
        schema_node (Node): Current node in the schema tree.
        current_lijst (List[str]): Current list of identifiers.

    Returns:
        DataNode: Constructed data node.
    """

    data_node = DataNode(schema_node.name)
    if not schema_node.children:
        data = OrderedSet()
        column = '-'.join(current_lijst)
        if column in df.columns:
            for d in df.loc[:, column]:
                d = clean_data(d, schema_node)
                if d is not None:
                    data.add(d)
        data_node.data += list(data)

    for c in schema_node.children:
        current_lijst.append(c.name)
        if c.max_amount > 1 or (isinstance(schema_node, ChoiceNode) and schema_node.max_amount > 1):
            partition = get_partition(df, np.ones(df.shape[0], dtype=bool), current_lijst, c)
        else:
            partition = [np.ones(df.shape[0], dtype=bool)]

        for part in partition:
            data_node.children[c.name].append(recursive_data_read(df[part], c, current_lijst))
        del current_lijst[-1]
    return data_node


def data_node_to_json(data_node, schema_node):
    """
    Converts data nodes to JSON format.

    Args:
        data_node (DataNode): Data node to be converted.
        schema_node (Node): Corresponding schema node.

    Returns:
        List[Dict[str, Any]]: JSON representation of data nodes.
    """

    if not schema_node.children:
        if data_node.data[0] == 'empty_field':
            return [None]
        return data_node.data
    assert not (schema_node.children and data_node.data), 'Undefined behaviour!'
    json_dict = dict()

    for c in schema_node.children:

        if c.name in data_node.children:
            for prop_c in data_node.children[c.name]:
                if isinstance(c, ChoiceNode) or isinstance(c, SequenceNode):
                    for key, val in data_node_to_json(prop_c, c)[0].items():
                        json_dict[key] = json_dict.get(key, []) + val
                else:
                    json_dict[c.name] = json_dict.get(c.name, []) + data_node_to_json(prop_c, c)

    return [json_dict]


def read_sheets(filename, sheets, xml_schema=None, mode='local', xsd_source='productie'):
    """
    Reads data from Excel sheets and generates filled XML.

    Args:
        filename (str): Path to the Excel file.
        sheets (List[str]): List of sheet names to be read.

    Returns:
        str: Filled XML data.
    """

    data_root = DataNode('schema')
    if not sheets:
        xl = pd.ExcelFile(filename)
        sheets = xl.sheet_names
        sheets.remove('Codelijsten')
        sheets.remove('metadata')

    root = get_dfs_schema(PROJECT_ROOT, xsd_source, mode)
    for sheet in sheets:
        print(f"Processing Sheet: {sheet} ")
        sheet_available = False
        try:
            df = pd.read_excel(filename, sheet_name=sheet, dtype={'meetnet': str}).iloc[
                 root.get_specific_child(sheet).get_max_depth():,
                 :].reset_index(
                drop=True)
            sheet_available = True
        except ValueError:
            print(f'No {sheet} sheet found.')

        if sheet_available:
            try:
                base = root.get_specific_child(sheet)
                partition = get_partition(df, np.ones(df.shape[0], dtype='bool'), [], base)
                for part in tqdm(partition, 
                        desc=f"Processing {sheet}", 
                        unit=" nodes",
                        leave=True):
                    data_root.children[sheet].append(recursive_data_read(df[part], base, []))
            except ValueError:
                print(f'Conversion of sheet {sheet} failed')
        print("-------------------")
    data_root.delete_empty()

    print("Start node mapping")
    json_dict = data_node_to_json(data_root, root)[0]

    print("Start xml checking")
    if xml_schema is None:
        xml_schema = get_XML_schema(xsd_source)
    filled_xml = xml_schema.encode(json_dict)

    return filled_xml


def write_xml(xml, filename):
    """
    Writes XML data to a file.

    Args:
        xml (Any): XML data to be written.
        filename (str): Path to the output file.
    """

    with open(filename, 'w', encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n')
        f.write(xmlschema.etree_tostring(xml))


def read_to_xml(input_filename, output_filename='./dist/result.xml', sheets=None, mode='local',
                xsd_source='productie', project_root=None, xml_schema=None):
    """
    Reads data from Excel sheets and generates filled XML.

    Args:
        input_filename (str): Path to the input Excel file.
        output_filename (str, optional): Path to the output XML file. Defaults to './dist/result.xml'.
        sheets (List[str], optional): List of sheet names to be read. Defaults to None.
    """
    if project_root is not None:
        global PROJECT_ROOT
        PROJECT_ROOT = project_root

    filled_xml = read_sheets(input_filename, sheets=sheets, mode=mode, xsd_source=xsd_source, xml_schema=xml_schema)
    write_xml(filled_xml, output_filename)


if __name__ == '__main__':
    # read_to_xml('../tests/data/filled_templates/bodem_template_full2.xlsx', '../dist/dev.xml', sheets=['bodemlocatie'])
    read_to_xml('../data_voorbeeld/ovam_test.xlsx', '../dist/ovam_test.xml',
                xsd_source='productie')
