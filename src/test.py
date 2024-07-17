from xmlschema.validators.elements import XsdElement
from xmlschema.validators.complex_types import XsdType, XsdComplexType
from xmlschema.validators.simple_types import XsdList, XsdUnion
from xmlschema.validators.groups import XsdGroup
from xmlschema.validators.attributes import XsdAttribute
from dfs_schema import get_dfs_schema
import xmlschema
import math

from dfs_schema import Node, ChoiceNode, SequenceNode

xml_schema = xmlschema.XMLSchema('https://www.dov.vlaanderen.be/xdov/schema/latest/xsd/kern/dov.xsd')

dfs_schema = get_dfs_schema()

root_node = Node()
root_type = xml_schema.root_elements[0]

CONVERTOR = {'boolean': 'java.lang.Boolean',
             'date': 'java.sql.Date',
             'decimal': 'java.math.BigDecimal',
             'double': 'java.lang.Double',
             'string': 'java.lang.String',
             'anyURI': 'java.net.URI',
             'time': 'java.sql.Time',
             'dateTime': 'java.sql.Timestamp',
             None: 'java.lang.Object'}


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


    if not isinstance(current_node,ChoiceNode) and not isinstance(current_node,SequenceNode):
        current_node.binding = 'java.lang.Object'
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


recursive_fill(root_node, root_type)
clean_sequence_nodes(root_node, None)

dfs_schema.min_amount = 1
dfs_schema.max_amount = 1


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


compare_nodes(root_node, dfs_schema)
