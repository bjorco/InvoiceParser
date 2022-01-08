import ctypes
import re
import tkinter as tk
import tkinter.filedialog as fd
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Optional

from PyPDF2 import PdfFileReader
import dateutil.parser as date_parser

@dataclass(repr=True)
class Invoice:
    link: Path
    number: int
    workorder: int
    timestamp: datetime
    amount: Decimal
    amount_vat: Optional[Decimal] = None
    status: str = 'success'

def extract_text(filename: str):
    with open(filename, 'rb') as f:
        pfr = PdfFileReader(f)
        page = pfr.getPage(0)
        return page.extractText()

def parse_invoice(filename) -> Invoice:
    text = extract_text(filename)

    inv_no = int(re.search('Invoice Number:(\d+)', text).group(1))
    raw_dt = re.search(r'Invoice Date:(\w{3} \d{2}, \d{4})', text).group(1)
    inv_dt = date_parser.parse(raw_dt)
    inv_amt = Decimal(re.search('Invoice Total:EUR ((\d{1,3}(\,\d{3})*|(\d+))(\.\d{2}))', text).group(1).replace(',',''))
    wo_match = re.search('Booking Number:(\d+)[/](\d+)', text)
    wo1 = wo_match.group(1)
    wo2 = wo_match.group(2)
    if wo1[0] == '9':
        inv_wo = wo1
    else:
        inv_wo = wo2
    
    return Invoice(filename, inv_no, inv_wo, inv_dt, inv_amt)

def main():
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
    window = tk.Tk()
    window.withdraw()

    pdf_file = fd.askopenfilename(
        title='Invoice', 
        filetypes=[('PDF Files', '.pdf')]
    )

    print(parse_invoice(pdf_file))


if __name__ == '__main__':
    main()
