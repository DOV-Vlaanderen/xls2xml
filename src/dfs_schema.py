import json
import os
from pathlib import Path
from typing import List
from xmlschema.validators.elements import XsdElement
from xmlschema.validators.complex_types import XsdComplexType
from xmlschema.validators.simple_types import XsdList, XsdUnion
from xmlschema.validators.groups import XsdGroup
from xmlschema.validators.attributes import XsdAttribute
import xmlschema
import math

# Global variables to store schema data
TYPE_LIJST = dict()
dov_schema_id = None
DEFAULT_TYPE = "java.lang.Object"

def init(config_filename="xsd_schema.json") -> None:
    """
    Initializes global variables TYPE_LIJST and dov_schema_id with schema data from xsd_schema.json file.
    """
    xsd_schema = Path(os.path.dirname(__file__) + f"/config/schemas/{config_filename}")
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
        self.binding = None
        self.priority = None
        self.source = None

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
            self.enum = enums[0]

        bindings = [restriction['binding'] for restriction in self.constraints if 'binding' in restriction]

        self.binding = DEFAULT_TYPE if not bindings else bindings[0]

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


CONVERTOR = {'boolean': 'java.lang.Boolean',
             'date': 'java.sql.Date',
             'decimal': 'java.math.BigDecimal',
             'double': 'java.lang.Double',
             'string': 'java.lang.String',
             'anyURI': 'java.net.URI',
             'time': 'java.sql.Time',
             'dateTime': 'java.sql.Timestamp',
             None: DEFAULT_TYPE}


def get_content(current_type):
    content = []

    if not isinstance(current_type.content, XsdList):
        content += list(current_type.content)

    if isinstance(current_type, XsdComplexType):
        content += list(current_type.attributes._attribute_group.values())

    if current_type.local_name == 'PointType':
        content = content[1:] + content[:1]  # For some reason Point is in the wrong order? Bit of a dirty hack

    return list(content)


def get_child_node(child_type, choices, sequences):
    if isinstance(child_type, XsdGroup):
        if child_type.model == 'choice':
            child_node = ChoiceNode()
            choices += 1
            child_node.name = f'choice_{choices}'
        else:
            child_node = SequenceNode()
            sequences += 1
            child_node.name = f'sequence_{sequences}'
    else:
        child_node = Node()
        child_node.name = child_type.local_name

    return child_node, choices, sequences


def get_binding(current_type):
    if isinstance(current_type, XsdUnion):
        return get_binding(current_type.member_types[0])

    if isinstance(current_type, XsdAttribute):
        return get_binding(current_type.type)

    if current_type.id == 'integer':
        return 'java.math.BigInteger'

    if current_type.base_type:
        return get_binding(current_type.base_type)

    return CONVERTOR[current_type.id]


def recursive_fill(current_node, current_type):
    choices = 0
    sequences = 0
    content = []
    if isinstance(current_type, XsdGroup):
        current_node.min_amount = current_type.min_occurs
        current_node.max_amount = current_type.max_occurs if current_type.max_occurs is not None else math.inf

    elif isinstance(current_type, XsdAttribute):
        current_node.min_amount = 0
        current_node.max_amount = 1

    elif isinstance(current_type, XsdElement):
        current_node.min_amount = current_type.min_occurs
        current_node.max_amount = current_type.max_occurs if current_type.max_occurs is not None else math.inf
        current_type = current_type.type

    if isinstance(current_type, XsdComplexType) or (
            isinstance(current_type, XsdGroup) and (
            isinstance(current_node, ChoiceNode) or isinstance(current_node, SequenceNode))):
        content = get_content(current_type)

    for child_type in content:
        child_node, choices, sequences = get_child_node(child_type, choices, sequences)
        current_node.children.append(recursive_fill(child_node, child_type))

    if not isinstance(current_node, ChoiceNode) and not isinstance(current_node, SequenceNode):
        current_node.binding = DEFAULT_TYPE
    if not content:
        try:
            current_node.binding = get_binding(current_type)
        except AttributeError:
            pass
        try:
            if isinstance(current_type, XsdUnion):
                current_node.enum = [str(e) for member in current_type.member_types for e in member.enumeration]
            else:
                if current_type.enumeration:
                    current_node.enum = [str(e) for e in current_type.enumeration]
        except AttributeError:
            pass

    return current_node


def clean_sequence_nodes(current_node, prev_node):
    for child_node in current_node.children:
        clean_sequence_nodes(child_node, current_node)

    if isinstance(current_node, SequenceNode) and (
            not isinstance(prev_node, ChoiceNode) or len(current_node.children) <= 1):
        index = prev_node.children.index(current_node)
        prev_node.children = prev_node.children[:index] + current_node.children + prev_node.children[index + 1:]


def compare_nodes(node1, node2):
    assert (node1.name, node1.min_amount, node1.max_amount, len(node1.children)) == (
        node2.name, node2.min_amount, node2.max_amount, len(node2.children))

    if not node1.children:
        assert node1.binding == node2.binding

    assert (node1.enum and node2.enum) or (not node1.enum and not node2.enum)

    if node1.enum:
        assert not set(node1.enum).symmetric_difference(set(node2.enum))

    for child1, child2 in zip(node1.children, node2.children):
        compare_nodes(child1, child2)


def get_dfs_schema_from_url(url="https://www.dov.vlaanderen.be/xdov/schema/latest/xsd/kern/dov.xsd"):
    xml_schema = xmlschema.XMLSchema(url)
    root_node = Node()
    root_type = xml_schema.root_elements[0]

    recursive_fill(root_node, root_type)
    clean_sequence_nodes(root_node, None)

    return root_node


def get_dfs_schema_from_local(config_filename="xsd_schema.json") -> Node:
    """
   Gets the depth-first schema tree.

   Returns:
       Node: Root node of the depth-first schema tree.
   """
    init(config_filename=config_filename)
    root = create_dfs_schema(TYPE_LIJST[dov_schema_id])
    root.min_amount = 1
    root.max_amount = 1

    return root


def get_dfs_schema(xsd_source="productie", mode='local') -> Node:
    """
   Gets the depth-first schema tree.

   Returns:
       Node: Root node of the depth-first schema tree.
   """
    assert xsd_source in ('productie', 'ontwikkel', 'oefen')
    assert mode in ('local', 'online')

    if mode == 'local':
        file = f'xsd_schema{"" if xsd_source == "productie" else "_" + xsd_source}.json'
        root = get_dfs_schema_from_local(file)
    else:

        url = f"https://{'www' if xsd_source == 'productie' else xsd_source}.dov.vlaanderen.be/xdov/schema/latest/xsd/kern/dov.xsd"
        root = get_dfs_schema_from_url(url)

    root.source = (mode, xsd_source)
    return root
