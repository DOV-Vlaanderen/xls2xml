import json
import math
import os
from pathlib import Path
from typing import List

# Global variables to store schema data
TYPE_LIJST = dict()
dov_schema_id = None


def init() -> None:
    """
    Initializes global variables TYPE_LIJST and dov_schema_id with schema data from xsd_schema.json file.
    """
    xsd_schema = Path(os.path.dirname(__file__) + "/config/xsd_schema.json")
    with open(xsd_schema) as f:
        data = json.load(f)

    global TYPE_LIJST
    TYPE_LIJST = {x["id"]: x for x in data["schemas"][0]["types"]}
    global dov_schema_id
    dov_schema_id = [x["id"] for x in data["schemas"][0]["types"] if x["name"] == "DovSchemaType"][0]


class Node:
    """
    Represents a node in the schema tree.
    """

    def __init__(self):
        self.children = []
        self.min_amount = None
        self.max_amount = None
        self.name = None
        self.constraints = []
        self.enum = None
        self.valid = None

    def set_metadata(self, metadata: dict) -> None:
        """
        Sets metadata for the node.

        Args:
            metadata (dict): Metadata information for the node.
        """

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

    def __str__(self) -> str:
        return f'Node(name="{self.name}", {self.min_amount}..{self.max_amount})'

    def __repr__(self) -> str:
        return str(self)

    def pprint_lines(self) -> List[str]:
        """
        Pretty prints the node and its children as lines.

        Returns:
            list: List of lines representing the node and its children.
        """
        lines = [str(self)]
        for child in self.children:
            lines += ['\t' + l for l in child.pprint_lines()]

        return lines

    def pprint(self) -> None:

        """
        Pretty prints the node and its children.
        """
        for line in self.pprint_lines():
            print(line)

    def get_specific_child(self, name: str):
        """
        Retrieves a specific child node by name.

        Args:
            name (str): Name of the child node to retrieve.

        Returns:
            Node: The child node with the specified name.
        """
        for child in self.children:
            if child.name == name:
                return child

        raise ValueError(f'Child {name} not found')

    def get_max_depth(self) -> int:
        """
        Recursively calculates the maximum depth of the schema tree.

        Returns:
            int: Maximum depth of tree starting at this node.
        """
        return 1 + max([0] + [c.get_max_depth() for c in self.children])

    def validate(self, children_bools: List[bool]) -> bool:
        """
        Validates the node based on the boolean values of its children.

        Args:
            children_bools (list): List of boolean values indicating the validity of children nodes.

        Returns:
            bool: True if all children nodes are valid, False otherwise.
        """
        return all(children_bools)


class ChoiceNode(Node):
    """
    Represents a choice node in the schema tree.
    """

    def __init__(self):
        super().__init__()

    def __str__(self) -> str:
        return f'ChoiceNode(name="{self.name}", {self.min_amount}..{self.max_amount})'

    def validate(self, children_bools: List[bool]) -> bool:
        val = False

        for child_bool in children_bools:
            val = val ^ child_bool

        return val


class SequenceNode(Node):
    """
    Represents a sequence node in the schema tree.
    """

    def __init__(self):
        super().__init__()

    def __str__(self) -> str:
        return f'SequenceNode(name="{self.name}", {self.min_amount}..{self.max_amount})'


def create_dfs_schema(node, old_node: Node = None) -> Node:
    """
    Recursively creates a depth-first schema tree starting from the given node.

    Args:
        node (dict): Dictionary representing the node in the schema.
        old_node (Node): Node to which the current constraints should be added (default is None).

    Returns:
        Node: Root node of the created schema tree.
    """

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
                elif 'declares' in child['propertyType']:
                    child_node = create_dfs_schema(child['propertyType'])
                else:
                    child_node = Node()
            else:
                child_node = create_dfs_schema(child)
            current_node.children.append(child_node)
            child_node.set_metadata(child)

    return current_node


def get_dfs_schema() -> Node:
    """
   Gets the depth-first schema tree.

   Returns:
       Node: Root node of the depth-first schema tree.
   """
    init()
    root = create_dfs_schema(TYPE_LIJST[dov_schema_id])
    return root
