import json
import math
import os
from pathlib import Path

TYPE_LIJST = dict()
dov_schema_id = None


def init():
    xsd_schema = Path(os.path.dirname(__file__)+"/config/xsd_schema.json")
    with open(xsd_schema) as f:
        data = json.load(f)

    global TYPE_LIJST
    TYPE_LIJST = {x["id"]: x for x in data["schemas"][0]["types"]}
    global dov_schema_id
    dov_schema_id = [x["id"] for x in data["schemas"][0]["types"] if x["name"] == "DovSchemaType"][0]


class Node:

    def __init__(self):
        self.children = []
        self.min_amount = None
        self.max_amount = None
        self.name = None
        self.constraints = []
        self.enum = None
        self.valid = None

    def set_metadata(self, metadata):

        self.name = metadata["name"]
        self.min_amount, self.max_amount = [math.inf if x == "n" else int(x) for x in
                                            metadata["constraints"]['cardinality'].split('..')]
        constraint_stack = [metadata]
        while constraint_stack:
            cm = constraint_stack.pop(0)
            self.constraints.append(cm["constraints"])
            if "propertyType" in cm:
                if 'ref' in cm['propertyType']:
                    constraint_stack.append(TYPE_LIJST[cm['propertyType']['ref']])
                else:
                    constraint_stack.append(cm['propertyType'])
            if "superType" in cm:
                constraint_stack.append(TYPE_LIJST[cm['superType']['ref']])
        enums = [c['values'] for c in [c['enumeration']['@value'] for c in self.constraints if 'enumeration' in c] if
                 c['allowOthers'] == False]

        if enums:
            self.enum = enums

    def __str__(self):
        return f'Node(name="{self.name}", {self.min_amount}..{self.max_amount})'

    def __repr__(self):
        return str(self)

    def pprint_lines(self):
        lines = [str(self)]
        for child in self.children:
            lines += ['\t' + l for l in child.pprint_lines()]

        return lines

    def pprint(self):
        for line in self.pprint_lines():
            print(line)

    def get_specific_child(self, name):

        for child in self.children:
            if child.name == name:
                return child

    def get_max_depth(self):
        return 1 + max([0] + [c.get_max_depth() for c in self.children])

    def validate(self, children_bools):
        return all(children_bools)


class ChoiceNode(Node):

    def __init__(self):
        super().__init__()

    def __str__(self):
        return f'ChoiceNode(name="{self.name}", {self.min_amount}..{self.max_amount})'

    def validate(self, children_bools):
        val = False

        for child_bool in children_bools:
            val = val ^ child_bool

        return val


class SequenceNode(Node):

    def __init__(self):
        super().__init__()

    def __str__(self):
        return f'SequenceNode(name="{self.name}", {self.min_amount}..{self.max_amount})'


def create_dfs_schema(node, old_node=None):
    if not old_node:
        if 'choice' in node['constraints'] and node['constraints']["choice"]:
            current_node = ChoiceNode()
        elif node['name'].startswith('sequence'):
            current_node = SequenceNode()
        else:
            current_node = Node()
    else:
        current_node = old_node

    if "superType" in node:
        create_dfs_schema(TYPE_LIJST[node['superType']['ref']], old_node=current_node)

    if "declares" in node:
        for child in node["declares"]:
            if "propertyType" in child:
                if 'ref' in child['propertyType']:
                    child_node = create_dfs_schema(TYPE_LIJST[child['propertyType']['ref']])
                else:
                    child_node = Node()
            else:
                child_node = create_dfs_schema(child)
            current_node.children.append(child_node)
            child_node.set_metadata(child)

    return current_node


def get_dfs_schema():
    init()
    root = create_dfs_schema(TYPE_LIJST[dov_schema_id])
    return root
