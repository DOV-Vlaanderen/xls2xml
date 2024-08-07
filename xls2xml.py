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

    parser.add_argument("-m", "--mode",
                        help="Run in local or online mode, options are 'local' and 'online', default: local",
                        default='local')

    parser.add_argument("-omg", "--omgeving",
                        help="Determines which xsd-schema is used, options are 'ontwikkel','oefen' and 'productie', default: productie ",
                        default='productie')

    parser.add_argument("-s", "--sheets", nargs='+',
                        help="Sheet(s) from excel file that needs to be parsed, by default all sheets will be parsed")

    # Read arguments from command line
    args = parser.parse_args()

    assert args.omgeving in ('ontwikkel', 'oefen', 'productie')
    assert args.mode in ('local', 'online')

    arg_convertor = {('ontwikkel', 'local'): 'xsd_schema_ontwikkel.json', ('oefen', 'local'): 'xsd_schema_oefen.json',
                     ('productie', 'local'): 'xsd_schema.json',
                     ('ontwikkel', 'online'): 'https://ontwikkel.dov.vlaanderen.be/xdov/schema/latest/xsd/kern/dov.xsd',
                     ('oefen', 'online'): 'https://oefen.dov.vlaanderen.be/xdov/schema/latest/xsd/kern/dov.xsd',
                     ('productie', 'online'): 'https://www.dov.vlaanderen.be/xdov/schema/latest/xsd/kern/dov.xsd'
                     }

    source = arg_convertor[(args.omgeving, args.mode)]

    # Call the read_to_xml function with provided arguments
    if args.sheets:
        read_to_xml(args.input_file, args.output_file, sheets=args.sheets, mode=args.mode, xsd_source=source)
    else:
        read_to_xml(args.input_file, args.output_file, mode=args.mode, xsd_source=source)
