import tkinter as tk
from tkinter import ttk
from tkinter import filedialog as fd
from tkinter.messagebox import showinfo
from src.read_excel import read_to_xml
from src.generate_excel_template import generate_standard_templates
from src.dfs_schema import get_project_root, get_XML_schema
import traceback
import time


"""
Command:
pyinstaller -F -w -n xls2xml --distpath app gui.py
"""
def generate_templates():
    try:
        generate_standard_templates(project_root=get_project_root(), mode='online')
    except:
        showinfo('Outdated version',
                 "Your version of xls2xml is outdated and therefore you can't generate the most recent templates.")


def select_file():
    filetypes = (('Alle Excel bestanden', '*.xl*'), ('Alle bestanden', '*.*'))

    filename = fd.askopenfilename(title='Input excel file', initialdir='./', filetypes=filetypes)

    input_entry.delete(0, tk.END)
    input_entry.insert(0, filename)


# Choose output file

def save_as_file():
    filename = fd.asksaveasfilename(defaultextension='.xml', initialdir='./dist', title='Output_file',
                                    filetypes=(('XML bestanden', "*.xml"),))

    output_entry.delete(0, tk.END)
    output_entry.insert(0, filename)


def run_xls2xml():
    if omgeving.get() not in SCHEMAS:
        SCHEMAS[omgeving.get()] = get_XML_schema(omgeving.get())

    information_label.config(text='Converting your xlsx to XML...')
    root.update()
    try:
        read_to_xml(input_entry.get(), output_entry.get(), xsd_source=omgeving.get(), project_root=get_project_root(),
                    xml_schema=SCHEMAS[omgeving.get()])
        showinfo('Conversion complete!',
                 f'The conversion was completed succesfully!\nYour XML file can be found at:\n {output_entry.get()}')
    except:
        showinfo('Conversion failed!',
                 'The conversion to xml has failed with the following error:\n' + traceback.format_exc())
    finally:
        information_label.config(text=' ')


if __name__ == '__main__':
    SCHEMAS = {}

    # create the root window
    root = tk.Tk()
    root.title('xls2xml')
    root.resizable(True, True)
    root.geometry('800x300')

    input_filename = tk.StringVar()
    output_filename = tk.StringVar()
    omgeving = tk.StringVar()
    omgeving.set('productie')

    # open button
    input_entry = ttk.Entry(root, width=100)
    input_button = ttk.Button(root, width=20, text='Select input file', command=select_file)
    output_entry = ttk.Entry(root, width=100)
    output_button = ttk.Button(root, width=20, text='Select output file', command=save_as_file)

    omgeving_label = ttk.Label(root, text='Omgeving:')
    omgeving_menu = tk.OptionMenu(root, omgeving, *('productie', 'oefen', 'ontwikkel'))

    menubar = tk.Menu(root)
    filemenu = tk.Menu(menubar, tearoff=0)

    filemenu.add_command(label="Generate templates", command=generate_templates)

    menubar.add_cascade(label="File", menu=filemenu)

    run_button = ttk.Button(root, width=20, text='Run', command=run_xls2xml)
    information_label = ttk.Label(root, text=' ')

    input_entry.grid(row=1, column=0, pady=10, padx=10, sticky='NESW', columnspan=2)
    input_button.grid(row=1, column=2, pady=10, padx=10, sticky='NESW', )
    output_entry.grid(row=2, column=0, pady=10, padx=10, sticky='NESW', columnspan=2)
    output_button.grid(row=2, column=2, pady=10, padx=10, sticky='NESW')
    omgeving_label.grid(row=3, column=0, pady=10, padx=10, sticky='NESW', columnspan=1)
    omgeving_menu.grid(row=3, column=1, pady=10, padx=10, sticky='NESW')
    run_button.grid(row=4, columnspan=3, pady=30)
    information_label.grid(row=5, columnspan=3, pady=10)
    # run the application
    root.config(menu=menubar)
    root.mainloop()
