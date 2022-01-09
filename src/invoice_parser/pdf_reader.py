import re
import tkinter as tk
import tkinter.filedialog as fd
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import List, Optional

import dateutil.parser as date_parser
from PyPDF2 import PdfFileReader

supported_invoice_types = {
    'North Sea Co': 'ncl'
}

@dataclass(repr=True)
class Invoice:
    link: Path
    invoice_type: str
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

    inv_type = _determine_invoice_type(text)

    if inv_type == 'Unknown':
        return Invoice(filename, inv_type, 0, 0, None, None, status='error')

    inv_no = int(re.search('Invoice Number:(\d+)', text).group(1))
    raw_dt = re.search(r'Invoice Date:(\w{3} \d{2}, \d{4})', text).group(1)
    inv_dt = date_parser.parse(raw_dt)
    inv_amt = Decimal(re.search('Invoice Total:EUR ((\d{1,3}(\,\d{3})*|(\d+))(\.\d{2}))', text).group(1).replace(',',''))
    inv_wo = _determine_work_order(text)
    inv_status = 'success'
    if inv_wo is None:
        inv_status = 'missing_wo'
    
    return Invoice(filename, inv_type, inv_no, inv_wo, inv_dt, inv_amt, status=inv_status)

def parse_folder(folder) -> List[Invoice]:
    invoices = []
    for p in Path(folder).glob('*.pdf'):
        inv = parse_invoice(p)
        invoices.append(inv)

    return invoices

def _determine_work_order(text: str) -> Optional[str]:
    if match := re.search('Booking Number:(\d+)[/](\d+)', text):
        wo1 = match.group(1)

        if wo1[0] == '9':
            return wo1
        else:
            return match.group(2)

def _determine_invoice_type(text: str) -> str:
    start = text[:12]
    if start in supported_invoice_types:
        return supported_invoice_types[start]
    else:
        return 'Unknown'

def main():
    window = tk.Tk()
    window.withdraw()

    pdf_file = fd.askopenfilename(
        title='Invoice', 
        filetypes=[('PDF Files', '.pdf')]
    )

    print(parse_invoice(pdf_file))


if __name__ == '__main__':
    main()
