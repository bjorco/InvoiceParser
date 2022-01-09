import ctypes
import tkinter as tk
import tkinter.filedialog as fd
from pathlib import Path
from tkinter import ttk
from typing import Optional

import controller
import pdf_reader
from item_treeview import InvoiceTree
from pdf_viewer import PdfViewer


class Event:
    ON_SEARCH = '<<ON_SEARCH>>'
    ON_SELECTED = '<<ON_SELECTED>>'
    ON_UPDATE_INVOICES = '<<ON_UPDATE_INVOICES>>'
    ON_REGISTER_INVOICE = '<<ON_REGISTER_INVOICE>>'
    ON_REGISTER_ERROR = '<<ON_REGISTER_ERROR>>'
    ON_REGISTER_MISSING = '<<ON_REGISTER_MISSING>>'
    ON_UPLOAD_INVOICE = '<<ON_UPLOAD_INVOICE>>'

class InvoiceOverview(ttk.Frame):
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.var_search_query = tk.StringVar()

        f_buttons = ttk.Frame(self)
        f_buttons.pack(side='top', fill='x')

        ttk.Entry(f_buttons, textvariable=self.var_search_query).pack(side='left')
        ttk.Button(f_buttons, text='Søk', command=self.on_search).pack(side='left')
        ttk.Button(f_buttons, text='Oppdater', command=self.on_update_invoices).pack(side='left')

        self.invoice_tree = InvoiceTree(self)
        self.invoice_tree.pack(side='top', fill='both', expand=True)

        self.invoice_tree.bind('<<TreeviewSelect>>', self.on_selected)
        self.invoice_tree.bind('<F8>', self.on_register_invoice)
        self.invoice_tree.bind('<F3>', self.on_register_error)
        self.invoice_tree.bind('<F4>', self.on_register_missing)
        self.invoice_tree.bind('<F5>', self.on_upload_invoice)
    
    @property
    def selected_invoice(self) -> Optional[pdf_reader.Invoice]:
        if adapter := self.invoice_tree.selected:
            return adapter.item
    
    def update_invoice(self, invoice) -> None:
        self.invoice_tree.update_object(invoice)

    def on_selected(self, event = None) -> None:
        self.event_generate(Event.ON_SELECTED)

    def on_search(self, event = None) -> None:
        self.invoice_tree.searcher(self.var_search_query.get())
        self.event_generate(Event.ON_SEARCH)
    
    def on_update_invoices(self, event = None) -> None:
        self.event_generate(Event.ON_UPDATE_INVOICES)

    def on_register_invoice(self, event = None) -> None:
        self.event_generate(Event.ON_REGISTER_INVOICE)
    
    def on_register_error(self, event = None) -> None:
        self.event_generate(Event.ON_REGISTER_ERROR)
    
    def on_register_missing(self, event = None) -> None:
        self.event_generate(Event.ON_REGISTER_MISSING)

    def on_upload_invoice(self, event = None) -> None:
        self.event_generate(Event.ON_UPLOAD_INVOICE)

class Application:
    def __init__(self, window):
        self.window = window

        self.invoices = []
        self.source = None
        self.pdf_viewer = PdfViewer()
        
        panes = ttk.Panedwindow(self.window, orient='horizontal')
        panes.pack(fill='both', expand=True)

        self.invoice_overview = InvoiceOverview(panes)
        self.viewer_frame = self.pdf_viewer.create_viewer(panes)

        panes.add(self.invoice_overview)
        panes.add(self.viewer_frame, weight=1)
        self.register_events()

    def register_events(self) -> None:
        self.invoice_overview.bind(Event.ON_REGISTER_INVOICE, self.on_register_invoice)
        self.invoice_overview.bind(Event.ON_REGISTER_ERROR, self.on_register_error)
        self.invoice_overview.bind(Event.ON_REGISTER_MISSING, self.on_register_missing)
        self.invoice_overview.bind(Event.ON_UPLOAD_INVOICE, self.on_upload_invoice)
        self.invoice_overview.bind(Event.ON_UPDATE_INVOICES, self.on_update_invoices)
        self.invoice_overview.bind(Event.ON_SELECTED, self.on_selected)

    def on_selected(self, event = None) -> None:
        if f := self.invoice_overview.selected_invoice:
            self.pdf_viewer.display(f.link)

    def on_register_invoice(self, event = None) -> None:
        if invoice := self.invoice_overview.selected_invoice:
            invoice.status = 'working'
            self.invoice_overview.update_invoice(invoice)

            controller.enter_invoice(invoice)

            invoice.status = 'done'
            self.invoice_overview.update_invoice(invoice)
    
    def on_upload_invoice(self, event = None) -> None:
        if invoice := self.invoice_overview.selected_invoice:
            uploaded_file = self.source / 'uploaded' / invoice.link.name
            invoice.link.rename(uploaded_file)
            invoice.link = uploaded_file
            invoice.status = 'uploaded'
            self.invoice_overview.update_invoice(invoice)
    
    def on_register_missing(self, event = None) -> None:
        if invoice := self.invoice_overview.selected_invoice:
            missing_file = self.source / 'wo' / invoice.link.name
            invoice.link.rename(missing_file)
            invoice.link = missing_file
            invoice.status = 'missing_wo'
            self.invoice_overview.update_invoice(invoice)
    
    def on_register_error(self, event = None) -> None:
        if invoice := self.invoice_overview.selected_invoice:
            error_file = self.source / 'err' / invoice.link.name
            invoice.link.rename(error_file)
            invoice.link = error_file
            invoice.status = 'error'
            self.invoice_overview.update_invoice(invoice)

    def on_update_invoices(self, event = None) -> None:
        if folder := fd.askdirectory(title='Velg arbeid mappe'):
            self.source = Path(folder)
            
            wo = self.source / 'wo'
            wo.mkdir(exist_ok=True)

            err = self.source / 'err'
            err.mkdir(exist_ok=True)

            up = self.source / 'uploaded'
            up.mkdir(exist_ok=True)

            self.invoices = pdf_reader.parse_folder(self.source)
            self.invoice_overview.invoice_tree.content = self.invoices


def main():
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
    window = tk.Tk()
    
    app = Application(window)
    
    window.mainloop()

if __name__ == '__main__':
    main()
