import json
import math
import xlsxwriter

with open("../code_lijsten/xsd_test.json") as f:
    data = json.load(f)

sheets = ["opdracht", "grondwaterlocatie", "filter", "filtermeting", "bodemlocatie", "bodemmonster", "bodemobservatie"]

TYPE_LIJST = {x["id"]: x for x in data["schemas"][0]["types"]}

dov_schema_id = [x["id"] for x in data["schemas"][0]["types"] if x["name"] == "DovSchemaType"][0]


class Node:

    def __init__(self):
        self.children = []
        self.min_amount = None
        self.max_amount = None
        self.name = None
        self.constraints = []
        self.enum = None

    def set_metadata(self, metadata):

        self.name = metadata["name"]
        self.min_amount, self.max_amount = [math.inf if x == "n" else int(x) for x in
                                            metadata["constraints"]['cardinality'].split('..')]
        constraint_stack = [metadata]
        while constraint_stack:
            cm = constraint_stack.pop(0)
            self.constraints.append(cm["constraints"])
            if "propertyType" in cm and 'ref' in cm['propertyType']:
                constraint_stack.append(TYPE_LIJST[cm['propertyType']['ref']])
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


class Choice_Node(Node):

    def __init__(self):
        super().__init__()

    def __str__(self):
        return f'Choice_Node(name="{self.name}", {self.min_amount}..{self.max_amount})'


class Sequence_Node(Node):

    def __init__(self):
        super().__init__()

    def __str__(self):
        return f'Sequence_Node(name="{self.name}", {self.min_amount}..{self.max_amount})'


def create_dfs_schema(node, old_node=None):
    if not old_node:
        if 'choice' in node['constraints'] and node['constraints']["choice"]:
            current_node = Choice_Node()
        elif node['name'].startswith('sequence'):
            current_node = Sequence_Node()
        else:
            current_node = Node()
    else:
        current_node = old_node

    if "declares" in node:
        for child in node["declares"]:
            if "propertyType" in child and 'ref' in child['propertyType']:
                child_node = create_dfs_schema(TYPE_LIJST[child['propertyType']['ref']])
            else:
                child_node = create_dfs_schema(child)
            current_node.children.append(child_node)
            child_node.set_metadata(child)

    if "superType" in node:
        create_dfs_schema(TYPE_LIJST[node['superType']['ref']], old_node=current_node)

    return current_node


def get_nth_col_name(n):
    alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    l = len(alphabet)
    name = [alphabet[n % l]]
    n = (n // l)
    while n > 0:
        n -= 1
        name.append(alphabet[n % l])
        n = (n // l)
    return ''.join(reversed(name))


def excel_dfs(current_node, current_lijst, column, sheet_data, constraint_data, is_needed=True, first = False):
    current_lijst.append(current_node.name)
    length = 0
    min_occur, max_occur = [math.inf if x == 'n' else int(x) for x in
                            current_node.constraints[0]['cardinality'].split('..')]
    if current_node.children:
        for child in current_node.children:
            length += excel_dfs(child, current_lijst, column + length, sheet_data, constraint_data,
                                (is_needed and min_occur > 0) or first)
        if len(current_lijst) > 1:
            sheet_data[(len(current_lijst) - 1, column, length)] = current_node.name
            constraint_data[(len(current_lijst) - 1, column, length)] = (min_occur > 0, current_node.constraints)
    else:
        sheet_data[(0, column, 1)] = '-'.join(current_lijst[1:])
        sheet_data[(len(current_lijst) - 1, column, 1)] = current_node.name
        constraint_data[(len(current_lijst) - 1, column, 1)] = (min_occur > 0, current_node.constraints)
        constraint_data[(0, column, 1)] = (is_needed and min_occur > 0, current_node.constraints)

        length += 1

    current_lijst.remove(current_node.name)
    return length




def get_excel_format_data(xls_root):
    current_lijst = []
    column = 0
    sheet_data = {}
    constraint_data = {}
    excel_dfs(xls_root, current_lijst, column, sheet_data, constraint_data, first=True)

    max_n = max(x[0] for x in sheet_data.keys())
    for coords, top_field in [(x, y) for x, y in sheet_data.items() if x[0] == 0]:
        x, y, l = coords
        sheet_data[(max_n + 1, y, l)] = top_field
        constraint_data[(max_n + 1, y, l)] = constraint_data[coords]
    return sheet_data, constraint_data


def create_xls(filename, sheets, root):
    workbook = xlsxwriter.Workbook(filename)
    for sheet in sheets:
        worksheet = workbook.add_worksheet(sheet)
        xls_root = root.get_specific_child(sheet)
        sheet_data, constraint_data = get_excel_format_data(xls_root)

        merge_format = workbook.add_format(
            {
                "bold": 1,
                "border": 1,
                "align": "center",
                "valign": "vcenter",
            }
        )

        necessary_format = workbook.add_format(
            {"bold": 1,
             "border": 1,
             "align": "center",
             "valign": "vcenter",
             "fg_color": "#FABF8F", }
        )

        for coords, data in sheet_data.items():
            row, col, length = coords

            cell_format = merge_format
            if constraint_data[coords][0]:
                cell_format = necessary_format

            if length > 1:
                worksheet.merge_range(f'{get_nth_col_name(col)}{row + 1}:{get_nth_col_name(col + length - 1)}{row + 1}',
                                      data, cell_format)

            else:
                worksheet.write(f'{get_nth_col_name(col)}{row + 1}', data, cell_format)

    workbook.close()


root = create_dfs_schema(TYPE_LIJST[dov_schema_id])
create_xls('dev.xlsx', sheets, root)
