import logging
import tkinter as tk
from pathlib import Path
from tkinter import ttk

import fitz
from PIL import Image, ImageTk

logging.getLogger('PIL.PngImagePlugin').setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

class PdfViewer:
    def __init__(self, **kwargs):
        self._pdf_file = None
        self.filter = kwargs.get('filter', Image.LANCZOS)
        self.resize_delay = kwargs.get('resize_delay', 5)
        
        self._canvas = None
        
        self.__resize_event_id = None
    
    def create_viewer(self, master) -> ttk.Frame:
        frame = ttk.Frame(master)

        vbar = ttk.Scrollbar(frame, orient='vertical')
        vbar.grid(row=0, column=1, sticky='ns')

        self._canvas = tk.Canvas(frame, yscrollcommand=vbar.set)
        
        vbar.configure(command=self._canvas.yview)
        
        self._canvas.grid(row=0, column=0, sticky='nswe')
        self._canvas.update()

        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1)

        self._canvas.grid(row=0, column=0)
        self._canvas.bind('<MouseWheel>', self.__wheel)
        self._canvas.bind('<Configure>', self._on_resize)

        return frame
    
    def display(self, filename: Path) -> None:
        """ Set file if valid and update display """
        if filename.suffix.lower() != '.pdf':
            return

        self._pdf_file = filename
        self._open_page(0)

    def __create_page_image(self, page: int):
        self._canvas.delete('all')

        with fitz.open(self._pdf_file) as pdf:
            # Get image data from the pdf page
            pix = pdf.get_page_pixmap(page)
            img = Image.frombytes('RGB', [pix.width, pix.height], pix.samples)

            # Resize image to fit canvas width
            width = self._canvas.winfo_width()
            w, h = img.size
            percent = width / w
            h = int(h*percent)
            img = img.resize((width, h), self.filter)
            
            # Draw iamge on the canvas
            imagetk = ImageTk.PhotoImage(img)
            img_id = self._canvas.create_image(0, 0, anchor='nw', image=imagetk)
            self._canvas.lower(img_id)
            
            # Keep a reference to the image to avoid garbage collection
            self._canvas.imagetk = imagetk

            # Set the scroll region for the canvas to match image dimensions
            self._canvas.configure(scrollregion=self._canvas.bbox("all"))
    
    def __wheel(self, event = None) -> None:
        self._canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
    def _open_page(self, page = 0) -> None:
        if not self._pdf_file:
            return

        self.__create_page_image(page)

    def _on_resize(self, event = None) -> None:
        if self.__resize_event_id is not None:
            self._canvas.after_cancel(self.__resize_event_id)
            self.__resize_event_id = None
        
        self.__resize_event_id = self._canvas.after(self.resize_delay, self._open_page)

if __name__ == "__main__":
    import ctypes
    from tkinter.filedialog import askopenfilename
    ctypes.windll.shcore.SetProcessDpiAwareness(1)

    app = tk.Tk()
    up_viewer = PdfViewer()
    view_frame = up_viewer.create_viewer(app)
    view_frame.pack(fill=tk.BOTH, expand=tk.TRUE)

    test_file = Path(askopenfilename())
    up_viewer.display(test_file)
    app.mainloop()
