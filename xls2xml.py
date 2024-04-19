import sys
import argparse
from src.read_excel import read_to_xml

if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='xls2xml',
                                     description="Function to parse data from xlsx-files to XML ready to be uploaded in DOV")

    parser.add_argument("-i", '--input_file',
                        help='Input xlsx file that will be parsed to XML, default: data/template.xlsx',
                        default='./data/template.xlsx')

    # Adding optional argument
    parser.add_argument("-o", "--output_file",
                        help="Output file to which the parsed XML-file is outputted, default: dist/dev.xml",
                        default='./dist/dev.xml')

    parser.add_argument("-s", "--sheets", nargs='+',
                        help="Sheet(s) from excel file that needs to be parsed, by default all sheets will be parsed")

    # Read arguments from command line
    args = parser.parse_args()

    if args.sheets:
        read_to_xml(args.input_file, args.output_file, sheets=args.sheets)
    else:
        read_to_xml(args.input_file, args.output_file)
