from collections import defaultdict
import xlsxwriter
from colorsys import hsv_to_rgb
import configparser
from src.dfs_schema import ChoiceNode, get_dfs_schema
from datetime import date

# Initialize configparser objects
header_convertor = configparser.ConfigParser()
codelijst_beschrijvingen = configparser.ConfigParser()

# Initialize defaultdict for priority columns
priority_columns = defaultdict(list)


class ExcelData:
    """
    Represents data for Excel cell.
    """

    def __init__(self):
        self.col_range = None
        self.row_range = None
        self.data = None
        self.code_lijst = None
        self.data_type = None
        self.mandatory = False
        self.min_occur = 0
        self.choices = 0

    def __repr__(self):
        return f"ExcelData[{self.data}]"

    def copy(self):
        """
        Creates a copy of the ExcelData instance.

        Returns:
            ExcelData: Copy of the instance.
        """

        copy_data = ExcelData()
        copy_data.col_range = self.col_range
        copy_data.row_range = self.row_range
        copy_data.data = self.data
        copy_data.code_lijst = self.code_lijst
        copy_data.data_type = self.data_type
        copy_data.mandatory = self.mandatory
        copy_data.min_occur = self.min_occur
        copy_data.choices = self.choices

        return copy_data


def rgb_to_hex(r, g, b):
    """
    Converts RGB values to hexadecimal color code.

    Args:
        r (float): Red value (0-1).
        g (float): Green value (0-1).
        b (float): Blue value (0-1).

    Returns:
        str: Hexadecimal color code.
    """
    return '#{:02x}{:02x}{:02x}'.format(int(255 * r), int(255 * g), int(255 * b))


def get_nth_col_name(n):
    """
    Converts column number to Excel column name.

    Args:
        n (int): Column number.

    Returns:
        str: Excel column name.
    """

    alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    l = len(alphabet)
    name = [alphabet[n % l]]
    n = (n // l)
    while n > 0:
        n -= 1
        name.append(alphabet[n % l])
        n = (n // l)
    return ''.join(reversed(name))


def excel_dfs(current_node, current_lijst, column, sheet_data, choices_made, is_needed=True, first=False):
    current_lijst.append(current_node.name)
    """
    Performs depth-first traversal of schema and constructs Excel sheet data.

    Args:
        current_node (Node): Current node in the schema.
        current_lijst (List[str]): Current list of elements.
        column (int): Current column number.
        sheet_data (List[ExcelData]): List to store ExcelData instances.
        choices_made (int): Number of choices made.
        is_needed (bool, optional): Indicates if the data is needed. Defaults to True.
        first (bool, optional): Indicates if it's the first node. Defaults to False.

    Returns:
        int: Length of the data.
    """

    length = 0
    data = ExcelData()

    for child in sorted(current_node.children, key=lambda x: -x.min_amount):
        length += excel_dfs(child, current_lijst, column + length, sheet_data,
                            choices_made + int(isinstance(current_node, ChoiceNode)),
                            (is_needed and current_node.min_amount > 0) or first)
    if not current_node.children:
        length += 1
        header_data = ExcelData()
        sheet_data.append(header_data)
        header_data.min_occur = current_node.min_amount
        header_data.row_range = (0, 0)
        header_data.col_range = (column, column + length - 1)
        header_data.data = '-'.join(current_lijst[1:])
        header_data.choices = choices_made
        header_data.mandatory = is_needed and current_node.min_amount > 0
        data_types = [x for x in current_node.constraints if 'binding' in x]
        if data_types:
            header_data.data_type = data_types[0]['binding']
        constraints = [x['enumeration']['@value']['values'] for x in current_node.constraints if
                       'enumeration' in x and not x['enumeration']['@value']['allowOthers']]
        if constraints:
            assert len(constraints) <= 1, 'Unintended behaviour!'
            header_data.code_lijst = constraints[0]

    data.min_occur = current_node.min_amount
    data.row_range = (len(current_lijst) - 1, len(current_lijst) - 1)
    data.col_range = (column, column + length - 1)
    data.data = current_node.name
    data.mandatory = current_node.min_amount > 0
    data.choices = choices_made
    if not first:
        sheet_data.append(data)

    del current_lijst[-1]
    return length


def get_excel_format_data(xls_root):
    current_lijst = []
    column = 0
    sheet_data = []
    excel_dfs(xls_root, current_lijst, column, sheet_data, 0, first=True)

    max_n = max(x.row_range[1] for x in sheet_data)
    header_row = []

    for cell_data in [s for s in sheet_data if s.row_range[0] == 0]:
        header_data = cell_data.copy()
        header_data.row_range = (max_n + 1, max_n + 1)
        if xls_root.name in header_convertor and cell_data.data in header_convertor[xls_root.name]:
            header_data.data = header_convertor[xls_root.name][cell_data.data]
        header_row.append(header_data)

    return sheet_data + header_row


def initialize_config(beschrijving_config, header_config, priority_config):
    if beschrijving_config is not None:
        codelijst_beschrijvingen.read(beschrijving_config)

    if header_config is not None:
        header_convertor.read(header_config)

    if priority_config is not None:
        with open(priority_config) as f:
            for line in f.readlines():
                line = line.strip(',\n').split(',')
                priority_columns[line[0]] = line[1:]


def create_xls(filename, sheets, root, hide_non_priority=True, beschrijving_config='./config/header_convertor.ini',
               header_config='./config/header_convertor.ini', priority_config='./config/priority_columns.csv'):
    """
    Creates an Excel file based on the given schema.

    Args:
        filename (str): The name of the Excel file to be created.
        sheets (List[str]): A list of sheet names.
        root (Node): The root node of the schema.
    """

    initialize_config(beschrijving_config, header_config, priority_config)

    workbook = xlsxwriter.Workbook(filename)

    last_code_lijst_index = 0

    standard_format = workbook.add_format({"bold": 1, "border": 1, "align": "left", "valign": "vcenter", })
    date_format = workbook.add_format({'num_format': 'dd/mm/yyyy'})

    codelijst_worksheet = workbook.add_worksheet('Codelijsten')

    worksheets = []
    for sheet in sheets:
        first_code_lijst_index = last_code_lijst_index
        worksheet = workbook.add_worksheet(sheet)
        worksheets.append(worksheet)
        xls_root = root.get_specific_child(sheet)
        sheet_data = get_excel_format_data(xls_root)
        bottom_header_index = max(d.row_range[1] for d in sheet_data)

        for data in sheet_data:
            formatting = {"bold": 1, "border": 1, "align": "left", "valign": "vcenter", }

            if data.row_range[0] in (0, bottom_header_index):
                if data.mandatory:
                    rgb = hsv_to_rgb(27 / 360, 1 / (2 ** data.choices), 1)
                    _hex = rgb_to_hex(*rgb)
                    formatting["fg_color"] = _hex

                if data.row_range[0] == 0:
                    worksheet.set_column(data.col_range[0], data.col_range[1], len(data.data) * 2,
                                         date_format if data.data_type == "java.sql.Date" else None,
                                         {'hidden': (data.data not in priority_columns[
                                             sheet] and not data.mandatory) and hide_non_priority})





            elif data.min_occur > 0:
                formatting["fg_color"] = "#FABF8F"
            cell_format = workbook.add_format(formatting)

            if data.col_range[0] != data.col_range[1]:
                worksheet.merge_range(
                    f'{get_nth_col_name(data.col_range[0])}{data.row_range[0] + 1}:{get_nth_col_name(data.col_range[1])}{data.row_range[0] + 1}',
                    data.data, cell_format)

            else:
                worksheet.write(f'{get_nth_col_name(data.col_range[0])}{data.row_range[0] + 1}', data.data, cell_format)

            if data.row_range[0] == bottom_header_index:
                if data.data_type == 'java.sql.Date':
                    worksheet.data_validation(bottom_header_index + 1, data.col_range[0], 1000000, data.col_range[0], {
                        'validate': 'date',
                        'criteria': '>',
                        'minimum': date(1900, 1, 1)
                    })

                if data.code_lijst:

                    # Toevoegen van codelijst aan Codelijsten sheet

                    codelijst_worksheet.merge_range(1, 2 * last_code_lijst_index, 1, 2 * last_code_lijst_index + 1,
                                                    data.data, cell_format=standard_format)

                    for i, code in enumerate(data.code_lijst):
                        codelijst_worksheet.write(i + 3, 2 * last_code_lijst_index, code)
                        beschrijving = '/'
                        if f'{sheet}-{data.data}' in codelijst_beschrijvingen and code in codelijst_beschrijvingen[
                            f'{sheet}-{data.data}']:
                            beschrijving = codelijst_beschrijvingen[f'{sheet}-{data.data}'][code]
                        codelijst_worksheet.write(i + 3, 2 * last_code_lijst_index + 1, beschrijving)

                    codelijst_worksheet.add_table(2, 2 * last_code_lijst_index, 2 + len(data.code_lijst),
                                                  2 * last_code_lijst_index + 1,
                                                  {'banded_columns': True, 'banded_rows': False, 'autofilter': False,
                                                   'columns': [{'header': 'Code'},
                                                               {'header': 'Beschrijving'}]
                                                   })

                    # Gegevensvalidatie toevoegen
                    worksheet.data_validation(bottom_header_index + 1, data.col_range[0], 1000000, data.col_range[0], {
                        'validate': 'list',
                        'source': f"='Codelijsten'!${get_nth_col_name(2 * last_code_lijst_index)}${4}:${get_nth_col_name(2 * last_code_lijst_index)}${4 - 1 + len(data.code_lijst)}"
                    })

                    # link toevoegen

                    worksheet.write_url(data.row_range[0], data.col_range[0],
                                        f"internal:'Codelijsten'!${get_nth_col_name(2 * last_code_lijst_index)}${2}",
                                        string=data.data, cell_format=cell_format)

                    last_code_lijst_index += 1

        for row in range(0, bottom_header_index):
            worksheet.set_row(row, None, None, {'hidden': True})
        for col in range(0, 2 * last_code_lijst_index + 1):
            codelijst_worksheet.set_column(col, col, 10)

        codelijst_worksheet.merge_range(0, 2 * first_code_lijst_index, 0, 2 * last_code_lijst_index - 1, sheet,
                                        cell_format=standard_format)

    worksheets[0].activate()
    workbook.close()


if __name__ == '__main__':
    root = get_dfs_schema()

    sheets = ['grondwaterlocatie', 'filter', 'filtermeting', 'filterdebietmeter', 'opdracht']
    create_xls('../data/grondwater_template.xlsx', sheets, root, hide_non_priority=True,
               header_config='./config/grondwater/header_convertor.ini')
    create_xls('../data/grondwater_template_full.xlsx', sheets, root, hide_non_priority=False, header_config=None)

    sheets = ['bodemlocatie', 'bodemsite', 'bodemmonster', 'bodemobservatie', 'bodemlocatieclassificatie',
              'bodemkundigeopbouw', 'opdracht']
    create_xls('../data/bodem_template.xlsx', sheets, root, hide_non_priority=True,
               header_config='./config/bodem/header_convertor.ini')
    create_xls('../data/bodem_template_full.xlsx', sheets, root, hide_non_priority=False, header_config=None)

    sheets = ['boring', 'interpretaties', 'grondmonster', 'opdracht']
    create_xls('../data/geologie_template.xlsx', sheets, root, hide_non_priority=True,
               header_config='./config/geologie/header_convertor.ini')
    create_xls('../data/geologie_template_full.xlsx', sheets, root, hide_non_priority=False, header_config=None)

    sheets = ['grondwaterlocatie', 'filter', 'filtermeting', 'filterdebietmeter', 'bodemlocatie',
              'bodemsite',
              'bodemmonster',
              'bodemobservatie',
              'bodemlocatieclassificatie',
              'bodemkundigeopbouw',
              'boring', 'interpretaties', 'grondmonster', 'opdracht']
    create_xls('../data/template.xlsx', sheets, root, hide_non_priority=False,
               header_config='./config/header_convertor.ini')
