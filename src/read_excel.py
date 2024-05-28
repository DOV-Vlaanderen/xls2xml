import math
from collections import defaultdict
import xmlschema
import pandas as pd
import numpy as np
from src.dfs_schema import ChoiceNode, get_dfs_schema
import traceback
import warnings

warnings.filterwarnings("ignore", message="Data Validation extension is not supported and will be removed")


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
                   'java.sql.Date': lambda x: x.strftime("%Y-%m-%d"),
                   'java.math.BigDecimal': lambda x: float(x),
                   'java.lang.Double': lambda x: float(x),
                   'java.lang.String': lambda x: str(x)
                   }

        bindings = [restriction['binding'] for restriction in schema_node.constraints if 'binding' in restriction]
        if bindings:
            try:
                data = cleaner[bindings[0]](data)
            except KeyError:
                print(bindings[0])
                raise NotImplementedError

        return data


def get_identifiers(node, current_lijst, identifiers):
    """
    Retrieves identifiers for data partitioning.

    Args:
        node (Node): Current node in the schema tree.
        current_lijst (List[str]): Current list of identifiers.
        identifiers (List[str]): List to store final identifiers.
    """

    relevant_children = [c for c in node.children if c.min_amount > 0]

    if any(c.max_amount > 1 for c in relevant_children):
        print('Undefined behaviour! 1')

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
    posibilities = set()

    for i, row in df[filter].loc[:, identifiers].iterrows():
        if not any(isinstance(x, float) and math.isnan(x) for x in tuple(row)):
            posibilities.add(tuple(row))

    new_filters = []
    for pos in posibilities:
        started = False
        new_filter = []
        for i, row in df.loc[:, identifiers].iterrows():
            if tuple(row) == pos or (any(isinstance(x, float) and math.isnan(x) for x in tuple(row)) and started):
                started = True
                new_filter.append(True)
            else:
                started = False
                new_filter.append(False)

        new_filters.append(filter * np.array(new_filter))
    assert not new_filters or all(sum(new_filters) == filter), 'Not a perfect partition?'
    return new_filters


def recursive_data_read(df, filter, schema_node, current_lijst) -> DataNode:
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
        data = set()
        column = '-'.join(current_lijst)
        for d in df[filter].loc[:, column]:
            d = clean_data(d, schema_node)
            if d is not None:
                data.add(d)
        data_node.data += list(data)

    for c in schema_node.children:
        current_lijst.append(c.name)
        if c.max_amount > 1:
            partition = get_partition(df, filter, current_lijst, c)
        else:
            partition = [filter]

        for part in partition:
            data_node.children[c.name].append(recursive_data_read(df, part, c, current_lijst))
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
        return data_node.data
    assert not (schema_node.children and data_node.data), 'Undefined behaviour!'
    json_dict = dict()

    for c in schema_node.children:

        if c.name in data_node.children:
            for prop_c in data_node.children[c.name]:
                if isinstance(c, ChoiceNode):
                    for key, val in data_node_to_json(prop_c, c)[0].items():
                        json_dict[key] = json_dict.get(key, []) + val
                else:
                    json_dict[c.name] = json_dict.get(c.name, []) + data_node_to_json(prop_c, c)

    return [json_dict]


def read_sheets(filename, sheets):
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

    root = get_dfs_schema()
    for sheet in sheets:
        try:
            df = pd.read_excel(filename, sheet_name=sheet, dtype={'meetnet': str}).iloc[
                 root.get_specific_child(sheet).get_max_depth():,
                 :].reset_index(
                drop=True)
            base = root.get_specific_child(sheet)
            partition = get_partition(df, np.ones(df.shape[0], dtype='bool'), [], base)
            for part in partition:
                data_root.children[sheet].append(recursive_data_read(df, part, base, []))
        except ValueError:
            print(f'No {sheet} sheet found.')

    data_root.delete_empty()
    json_dict = data_node_to_json(data_root, root)[0]

    my_schema = xmlschema.XMLSchema('https://www.dov.vlaanderen.be/xdov/schema/latest/xsd/kern/dov.xsd')
    filled_xml = my_schema.encode(json_dict)

    return filled_xml


def write_xml(xml, filename):
    """
    Writes XML data to a file.

    Args:
        xml (Any): XML data to be written.
        filename (str): Path to the output file.
    """

    with open(filename, 'w') as f:
        f.write('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n')
        f.write(xmlschema.etree_tostring(xml))


def read_to_xml(input_filename, output_filename='./dist/result.xml', sheets=None):
    """
    Reads data from Excel sheets and generates filled XML.

    Args:
        input_filename (str): Path to the input Excel file.
        output_filename (str, optional): Path to the output XML file. Defaults to './dist/result.xml'.
        sheets (List[str], optional): List of sheet names to be read. Defaults to None.
    """
    filled_xml = read_sheets(input_filename, sheets)
    write_xml(filled_xml, output_filename)


if __name__ == '__main__':
    sheets = ["opdracht", "grondwaterlocatie", "filter", "filtermeting", "bodemlocatie", "bodemmonster",
              "bodemobservatie"]

    read_to_xml('../data_voorbeeld/template_w.xlsx', '../dist/dev.xml', sheets)
