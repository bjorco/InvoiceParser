import pyautogui as pag
from contextlib import contextmanager

@contextmanager
def tab_switch():
    pag.hotkey('alt', 'tab')
    yield
    pag.hotkey('alt', 'tab')

def enter_invoice(invoice):
    with tab_switch():
        pag.write(f'{invoice.timestamp:%d%m%y}')
        pag.press('tab')
        pag.write(str(invoice.number))
        pag.press('down', 2)
        pag.write(str(invoice.amount).replace('.',','))
        pag.press('down', 3)
        pag.press('tab')
        pag.write(invoice.workorder)

def upload_file(invoice):
    with tab_switch():
        pag.keyDown('shift')
        pag.press('tab', 7)
        pag.keyUp('shift')