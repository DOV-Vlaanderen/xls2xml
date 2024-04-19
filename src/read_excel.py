import datetime
import math
from collections import defaultdict, OrderedDict

import xmlschema

from dfs_schema import create_dfs_schema, Node, Choice_Node, Sequence_Node
import json
import pandas as pd
import numpy as np
from pprint import pprint
import json
import xlsxwriter

with open("./config/xsd_test.json") as f:
    data = json.load(f)

sheets = ["opdracht", "grondwaterlocatie", "filter", "filtermeting", "bodemlocatie", "bodemmonster", "bodemobservatie"]

TYPE_LIJST = {x["id"]: x for x in data["schemas"][0]["types"]}

dov_schema_id = [x["id"] for x in data["schemas"][0]["types"] if x["name"] == "DovSchemaType"][0]

root = create_dfs_schema(TYPE_LIJST[dov_schema_id])


class DataNode():

    def __init__(self, name):
        self.name = name
        self.children = defaultdict(list)
        self.data = []

    def is_empty(self):
        return len(self.data) == 0 and len(self.children.keys()) == 0

    def delete_empty(self):
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

    def __repr__(self):
        return f'DataNode(name={self.name}, children=[{", ".join(str(key) + ":" + str(len(val)) for key, val in self.children.items() if len(val) > 0)}], data={self.data}) '


data_root = DataNode('schema')


def clean_data(data, schema_node):
    if isinstance(data, float) and math.isnan(data):
        return None
    else:
        for restriction in schema_node.constraints:
            try:
                if restriction['binding'] not in ['java.lang.Object', 'java.lang.String', 'java.sql.Date',
                                                  'java.math.BigDecimal', 'java.lang.Double']:
                    print(restriction['binding'])
            except:
                pass

        if any(('binding' in restriction and restriction['binding'] == 'java.sql.Date') for restriction in
               schema_node.constraints):
            data = data.strftime("%Y-%m-%d")

        if any(('binding' in restriction and restriction['binding'] == 'java.math.BigDecimal') for restriction in
               schema_node.constraints):
            data = float(data)

        if any(('binding' in restriction and restriction['binding'] == 'java.lang.Double') for restriction in
               schema_node.constraints):
            data = float(data)

        if any(('binding' in restriction and restriction['binding'] == 'java.lang.String') for restriction in
               schema_node.constraints):
            data = str(data)

        return data


def get_identifiers(node, current_lijst, identifiers):
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
    identifiers = []
    get_identifiers(node, current_lijst, identifiers)
    posibilities = set()

    for i, row in df[filter].loc[:, identifiers].iterrows():
        posibilities.add(tuple(row))

    new_filters = []
    for pos in posibilities:
        new_filters.append(filter * np.array([tuple(row) == pos for _, row in df.loc[:, identifiers].iterrows()]))
    assert all(sum(new_filters) == filter), 'Not a perfect partition?'
    return new_filters


def recursive_data_read(df, filter, schema_node, current_lijst):
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
    if not schema_node.children:
        return data_node.data
    assert not (schema_node.children and data_node.data), 'Undefined behaviour!'
    json_dict = dict()

    for c in schema_node.children:

        if c.name in data_node.children:
            for prop_c in data_node.children[c.name]:
                if isinstance(c, Choice_Node):
                    for key, val in data_node_to_json(prop_c, c)[0].items():
                        json_dict[key] = json_dict.get(key, []) + val
                else:
                    json_dict[c.name] = json_dict.get(c.name, []) + data_node_to_json(prop_c, c)

    return [json_dict]


for sheet in sheets:
    df = pd.read_excel('dev2.xlsx', sheet_name=sheet, dtype={'meetnet': str}).iloc[
         root.get_specific_child(sheet).get_max_depth():,
         :].reset_index(
        drop=True)
    base = root.get_specific_child(sheet)
    partition = get_partition(df, np.ones(df.shape[0], dtype='bool'), [], base)
    for part in partition:
        data_root.children[sheet].append(recursive_data_read(df, part, base, []))

data_root.delete_empty()
json_dict = data_node_to_json(data_root, root)[0]

my_schema = xmlschema.XMLSchema('https://www.dov.vlaanderen.be/xdov/schema/latest/xsd/kern/dov.xsd')
filled_xml = my_schema.encode(json_dict)

with open('../dist/dev.xml', 'w') as f:
    f.write('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n')
    f.write(xmlschema.etree_tostring(filled_xml))
