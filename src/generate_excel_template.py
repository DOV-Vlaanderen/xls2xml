import datetime
from collections import defaultdict
import xlsxwriter
from colorsys import hsv_to_rgb
import configparser
from src.dfs_schema import ChoiceNode, get_dfs_schema
from datetime import date
from pathlib import Path
import os

# Initialize configparser objects
header_convertor = configparser.ConfigParser()
codelijst_beschrijvingen = configparser.ConfigParser()

# Initialize defaultdict for priority columns
priority_columns = configparser.ConfigParser()
PROJECT_ROOT = None


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
        self.priority = None

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
        copy_data.priority = self.priority

        return copy_data


def fill_priority(current_node, previous_names, convertor):
    previous_names.append(current_node.name)
    if current_node.children:
        priorities = []
        for child in current_node.children:
            priorities.append(fill_priority(child, previous_names, convertor))
        current_node.priority = min(priorities)

    else:
        current_node.priority = convertor['-'.join(previous_names[1:]).lower()]
    del previous_names[-1]

    if isinstance(current_node, ChoiceNode):
        assert not (current_node.priority[0] < 4 and all(
            c.priority[0] >= 4 for c in current_node.children if c.min_amount > 0) and [c for c in current_node.children
                                                                                        if
                                                                                        c.min_amount > 0]), 'Removed a node that is necessary for its parent!'
    else:
        assert not (current_node.priority[0] < 4 and any(c.priority[0] >= 4 and c.min_amount > 0 for c in
                                                         current_node.children)), f'Removed node(s) {[c for c in current_node.children if c.priority[0] >= 4 and c.min_amount > 0]} that is necessary for its parent {previous_names, current_node}!'
    return current_node.priority


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

    for child in sorted(current_node.children, key=lambda x: (-x.min_amount, x.priority)):
        if child.priority[0] < 4:
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
        header_data.priority = current_node.priority
        if current_node.binding:
            header_data.data_type = current_node.binding

        if current_node.enum:
            header_data.code_lijst = current_node.enum

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


def make_tuple(val):
    return tuple(int(x) for x in val.split('.'))


def get_excel_format_data(xls_root):
    convertor = defaultdict(lambda: make_tuple(priority_columns['default']['default']),
                            {} if xls_root.name not in priority_columns else {k: make_tuple(v) for k, v in
                                                                              priority_columns[xls_root.name].items()})

    fill_priority(xls_root, [], convertor)
    current_lijst = []
    column = 0
    sheet_data = []
    excel_dfs(xls_root, current_lijst, column, sheet_data, 0, first=True)

    max_n = xls_root.get_max_depth() - 1
    header_row = []

    for cell_data in [s for s in sheet_data if s.row_range[0] == 0]:
        header_data = cell_data.copy()
        header_data.row_range = (max_n + 1, max_n + 1)
        if xls_root.name in header_convertor and cell_data.data in header_convertor[xls_root.name]:
            header_data.data = header_convertor[xls_root.name][cell_data.data]
        header_row.append(header_data)

    return sheet_data + header_row


def initialize_config(beschrijving_config, header_config, priority_config):
    global header_convertor
    global codelijst_beschrijvingen
    global priority_columns
    header_convertor = configparser.ConfigParser()
    codelijst_beschrijvingen = configparser.ConfigParser()
    priority_columns = configparser.ConfigParser()

    if beschrijving_config is not None:
        codelijst_beschrijvingen.read(beschrijving_config, encoding='utf-8')

    if header_config is not None:
        header_convertor.read(header_config, encoding='utf-8')

    if priority_config is not None:
        priority_columns.read(priority_config, encoding='utf-8')


def get_default_formats(workbook):
    standard_format = workbook.add_format({"bold": 1, "border": 1, "align": "left", "valign": "vcenter", })
    date_format = workbook.add_format({'num_format': 'dd/mm/yyyy'})
    decimal_format = workbook.add_format({'num_format': 'General'})
    integer_format = workbook.add_format({'num_format': '0'})
    time_format = workbook.add_format({'num_format': 'h:mm:ss'})
    formats = defaultdict(lambda: None)
    formats["java.sql.Date"] = date_format
    formats['java.math.BigDecimal'] = decimal_format
    formats['java.math.BigInteger'] = integer_format
    formats['java.sql.Time'] = time_format
    formats['java.lang.Double'] = decimal_format
    formats['java.lang.String'] = workbook.add_format({'num_format': '@'})
    formats["standard"] = standard_format

    return formats


def add_table_to_codelijst_sheet(workbook, data, cell_format, last_code_lijst_index):
    codelijst_worksheet = workbook.worksheets()[0]
    worksheet = workbook.worksheets()[-1]
    sheet = worksheet.name
    standard_format = workbook.add_format({"bold": 1, "border": 1, "align": "left", "valign": "vcenter", })
    bottom_header_index = data.row_range[0]

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


def get_cell_format(data, bottom_header_index, color_choice):
    formatting = {"bold": 1, "border": 1, "align": "left", "valign": "vcenter", }

    if data.row_range[0] in (0, bottom_header_index):  # Top or bottom row
        if data.mandatory or data.priority[0] < 2:
            rgb = hsv_to_rgb(27 / 360, 1 / (2 ** (data.choices * color_choice)), 1)
            _hex = rgb_to_hex(*rgb)
            formatting["fg_color"] = _hex

    elif data.min_occur > 0:
        formatting["fg_color"] = "#FABF8F"

    return formatting


def write_cell(data, worksheet, cell_format):
    if data.col_range[0] != data.col_range[1]:  # Merge_cell
        worksheet.merge_range(
            f'{get_nth_col_name(data.col_range[0])}{data.row_range[0] + 1}:{get_nth_col_name(data.col_range[1])}{data.row_range[1] + 1}',
            data.data, cell_format)

    else:
        worksheet.write(f'{get_nth_col_name(data.col_range[0])}{data.row_range[0] + 1}', data.data, cell_format)


def add_metadata_sheet(workbook, root, project_root):
    config = configparser.ConfigParser()
    config.read(os.path.join(project_root, 'config', 'config.ini'))
    worksheet = workbook.add_worksheet('metadata')

    worksheet.write('A1', 'Date generated')
    worksheet.write('B1', f'{datetime.datetime.now()}')
    row = 2
    for key, value in config['generation'].items():
        worksheet.write(f'A{row}', key)
        worksheet.write(f'B{row}', f'{value}')
        row += 1
    worksheet.write(f'A{row}', 'mode')
    worksheet.write(f'B{row}', root.source[0])
    row += 1
    worksheet.write(f'A{row}', 'source')
    worksheet.write(f'B{row}', root.source[1])

    worksheet.hide()


def add_sheet(workbook, sheet, xls_root, formats, last_code_lijst_index, color_choice):
    first_code_lijst_index = last_code_lijst_index
    codelijst_worksheet = workbook.worksheets()[0]
    worksheet = workbook.add_worksheet(sheet)
    sheet_data = get_excel_format_data(xls_root)
    bottom_header_index = max(d.row_range[1] for d in sheet_data)

    for data in sheet_data:
        cell_format = workbook.add_format(get_cell_format(data, bottom_header_index, color_choice))
        write_cell(data, worksheet, cell_format)

        if data.row_range[0] == bottom_header_index:
            worksheet.set_column(data.col_range[0], data.col_range[1], len(data.data) * 2,
                                 formats[data.data_type],
                                 {'hidden': data.priority[0] >= 3 and not data.mandatory})

            if data.data_type == 'java.sql.Date':
                worksheet.data_validation(bottom_header_index + 1, data.col_range[0], 1000000, data.col_range[0], {
                    'validate': 'date',
                    'criteria': '>',
                    'minimum': date(1500, 1, 1)
                })

            if data.data_type == 'java.lang.Boolean':
                worksheet.data_validation(bottom_header_index + 1, data.col_range[0], 1000000, data.col_range[0], {
                    'validate': 'list',
                    'source': ['true', 'false']
                })

            if data.code_lijst:
                add_table_to_codelijst_sheet(workbook, data, cell_format, last_code_lijst_index)
                last_code_lijst_index += 1

    for row in range(0, bottom_header_index):  # Hide top rows
        worksheet.set_row(row, None, None, {'hidden': True})

    # Format all tables from this sheet in the codelijst_worksheet.
    for col in range(0, 2 * last_code_lijst_index + 1):
        codelijst_worksheet.set_column(col, col, 10)

    codelijst_worksheet.merge_range(0, 2 * first_code_lijst_index, 0, 2 * last_code_lijst_index - 1, sheet,
                                    cell_format=formats['standard'])

    return last_code_lijst_index


def create_xls(filename, sheets, root, project_root,
               beschrijving_config=None,
               header_config=None,
               priority_config=None,
               color_choice=True):
    """
    Creates an Excel file based on the given schema.

    Args:
        filename (str): The name of the Excel file to be created.
        sheets (List[str]): A list of sheet names.
        root (Node): The root node of the schema.
    """

    if beschrijving_config is None:
        beschrijving_config = os.path.join(project_root, 'config', 'beschrijvingen.ini')

    if priority_config is None:
        priority_config = os.path.join(project_root, 'config', 'priority_config_full.ini')

    initialize_config(beschrijving_config, header_config, priority_config)

    workbook = xlsxwriter.Workbook(filename)
    last_code_lijst_index = 0

    formats = get_default_formats(workbook)
    workbook.add_worksheet('Codelijsten')

    for sheet in sheets:
        xls_root = root.get_specific_child(sheet)
        last_code_lijst_index = add_sheet(workbook, sheet, xls_root, formats, last_code_lijst_index, color_choice)

    add_metadata_sheet(workbook, root, project_root)

    workbook.worksheets()[1].activate()

    workbook.close()


def generate_standard_templates(project_root, mode='local'):
    configs = [
        ('productie', 'priority_config_beknopt.ini', 'header_convertor.ini'),
        ('oefen', 'priority_config_beknopt_oefen.ini', 'header_convertor_oefen.ini'),
        ('ontwikkel', 'priority_config_beknopt_oefen.ini', 'header_convertor_oefen.ini'),
    ]

    for omgeving, priorities_filename, header_filename in configs:
        priorities_filename = os.path.join(project_root, 'config', priorities_filename)
        header_filename = os.path.join(project_root, 'config', header_filename)
        root = get_dfs_schema(project_root, xsd_source=omgeving, mode=mode)

        # GRONDWATER
        sheets = ['grondwaterlocatie', 'filter', 'filtermeting', 'opdracht', 'monster', 'observatie']
        create_xls(f'{project_root}/templates/{omgeving}/{omgeving}_grondwater_template.xlsx', sheets, root,
                   project_root=project_root,
                   header_config=header_filename,
                   priority_config=priorities_filename,
                   color_choice=False)
        sheets += ['filterdebietmeter']
        create_xls(f'{project_root}/templates/{omgeving}/{omgeving}_grondwater_template_full.xlsx', sheets, root,
                   project_root=project_root)

        # BODEM
        sheets = ['bodemlocatie', 'bodemsite', 'bodemmonster', 'bodemobservatie',
                  'bodemkundigeopbouw', 'opdracht', 'monster', 'observatie']
        create_xls(f'{project_root}/templates/{omgeving}/{omgeving}_bodem_template.xlsx', sheets, root,
                   project_root=project_root,
                   header_config=header_filename,
                   priority_config=priorities_filename,
                   color_choice=False)
        sheets.append('bodemlocatieclassificatie')
        sheets.sort()
        create_xls(f'{project_root}/templates/{omgeving}/{omgeving}_bodem_template_full.xlsx', sheets, root,
                   project_root=project_root)

        # GEOLOGIE
        sheets = ['boring', 'interpretaties', 'grondmonster', 'opdracht', 'monster', 'observatie']
        create_xls(f'{project_root}/templates/{omgeving}/{omgeving}_geologie_template.xlsx', sheets, root,
                   project_root=project_root,
                   header_config=header_filename,
                   priority_config=priorities_filename,
                   color_choice=False)
        create_xls(f'{project_root}/templates/{omgeving}/{omgeving}_geologie_template_full.xlsx', sheets, root,
                   project_root=project_root)

        # OPDRACHT
        sheets = ['opdracht', 'monster', 'observatie']
        create_xls(f'{project_root}/templates/{omgeving}/{omgeving}_opdracht_template.xlsx', sheets, root,
                   project_root=project_root,
                   header_config=header_filename,
                   priority_config=priorities_filename,
                   color_choice=False
                   )
        create_xls(f'{project_root}/templates/{omgeving}/{omgeving}_opdracht_template_full.xlsx', sheets, root,
                   project_root=project_root)

        # FULL
        sheets = ['grondwaterlocatie', 'filter', 'filtermeting', 'filterdebietmeter', 'bodemlocatie',
                  'bodemsite',
                  'bodemmonster',
                  'bodemobservatie',
                  'bodemlocatieclassificatie',
                  'bodemkundigeopbouw',
                  'boring', 'interpretaties', 'grondmonster', 'opdracht', 'monster', 'observatie']
        create_xls(f'{project_root}/templates/{omgeving}/{omgeving}_template_full.xlsx', sheets, root,
                   project_root=project_root)


if __name__ == '__main__':
    project_root = Path(os.path.dirname(os.path.dirname(__file__)))
    generate_standard_templates(project_root=project_root)
