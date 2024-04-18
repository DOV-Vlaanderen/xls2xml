import json
import math
import xlsxwriter
from dfs_schema import Node, Choice_Node, Sequence_Node

with open("../code_lijsten/xsd_test.json") as f:
    data = json.load(f)

sheets = ["grondwaterlocatie", 'filter', 'filtermeting', 'opdracht']

priority_columns = {'grondwaterlocatie': ['identificatie']}

TYPE_LIJST = {x["id"]: x for x in data["schemas"][0]["types"]}

dov_schema_id = [x["id"] for x in data["schemas"][0]["types"] if x["name"] == "DovSchemaType"][0]


class Excel_data:

    def __init__(self):
        self.col_range = None
        self.row_range = None
        self.data = None
        self.code_lijst = None
        self.data_type = None
        self.mandatory = False
        self.min_occur = 0

    def __repr__(self):
        return f"Excel_data[{self.data}]"


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


def excel_dfs(current_node, current_lijst, column, sheet_data, constraint_data, test, is_needed=True, first=False):
    current_lijst.append(current_node.name)
    length = 0
    data = Excel_data()

    if current_node.children:
        for child in sorted(current_node.children, key=lambda x: -x.min_amount):
            length += excel_dfs(child, current_lijst, column + length, sheet_data, constraint_data, test,
                                (is_needed and current_node.min_amount > 0) or first)
        if len(current_lijst) > 1:
            sheet_data[(len(current_lijst) - 1, column, length)] = current_node.name
            constraint_data[(len(current_lijst) - 1, column, length)] = (
                current_node.min_amount > 0, current_node.constraints)
    else:
        sheet_data[(0, column, 1)] = '-'.join(current_lijst[1:])
        sheet_data[(len(current_lijst) - 1, column, 1)] = current_node.name
        constraint_data[(len(current_lijst) - 1, column, 1)] = (current_node.min_amount > 0, current_node.constraints)
        constraint_data[(0, column, 1)] = (is_needed and current_node.min_amount > 0, current_node.constraints)
        length += 1

        header_data = Excel_data()
        test.append(header_data)
        header_data.min_occur = current_node.min_amount
        header_data.row_range = (0, 0)
        header_data.col_range = (column, column + length - 1)
        header_data.data = current_node.name
        header_data.mandatory = is_needed and current_node.min_amount > 0
        header_data.data_type = current_node.constraints

    data.min_occur = current_node.min_amount
    data.row_range = (len(current_lijst) - 1, len(current_lijst) - 1)
    data.col_range = (column, column + length - 1)
    data.data = current_node.name
    data.mandatory = current_node.min_amount > 0
    if not first:
        test.append(data)

    del current_lijst[-1]
    return length


def get_excel_format_data(xls_root):
    current_lijst = []
    column = 0
    sheet_data = {}
    constraint_data = {}
    test = []
    excel_dfs(xls_root, current_lijst, column, sheet_data, constraint_data, test, first=True)

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

        # merge_format = workbook.add_format(
        #     {
        #         "bold": 1,
        #         "border": 1,
        #         "align": "center",
        #         "valign": "vcenter",
        #     }
        # )
        #
        # necessary_format = workbook.add_format(
        #     {"bold": 1,
        #      "border": 1,
        #      "align": "center",
        #      "valign": "vcenter",
        #      "fg_color": "#FABF8F", }
        # )
        #
        # bottom_header_index = max(r for r, c, l in sheet_data)
        # for coords, data in sheet_data.items():
        #     row, col, length = coords
        #
        #     cell_format = merge_format
        #     if constraint_data[coords][0]:
        #         cell_format = necessary_format
        #
        #     if length > 1:
        #         worksheet.merge_range(f'{get_nth_col_name(col)}{row + 1}:{get_nth_col_name(col + length - 1)}{row + 1}',
        #                               data, cell_format)
        #
        #     else:
        #         worksheet.write(f'{get_nth_col_name(col)}{row + 1}', data, cell_format)
        #
        #     if row == bottom_header_index:
        #         col_constraints = constraint_data[coords][1]
        #         enums = [c['values'] for c in
        #                  [c['enumeration']['@value'] for c in col_constraints if 'enumeration' in c] if
        #                  c['allowOthers'] == False]
        #
        #         assert len(enums) <= 1, 'Undefined behaviour!'
        #         assert length == 1, 'Undefined behaviour!'
        #
        #         if enums:
        #             worksheet.data_validation(bottom_header_index + 1, col, 1000000, col, {
        #                 'validate': 'list',
        #                 'source': enums[0]
        #             })

    workbook.close()


root = create_dfs_schema(TYPE_LIJST[dov_schema_id])
create_xls('develop.xlsx', sheets, root)
