import abc
from tkinter import font, ttk
from typing import Any, Dict, Tuple, TypeVar

class TreeviewAdapter(abc.ABC):
    """ Abstract class for containing objects to be displayed in a treeview """
    def __init__(self, item):
        self.item = item
        self.iid = None
        self.is_comments_allowed = True

    @abc.abstractmethod
    def text(self): return

    @abc.abstractmethod
    def values(self): return

    def tag(self, index) -> Tuple[str]:
        return ('odd',) if index % 2 else ('even',)

    def key(self) -> str:
        return self.generate_key(self.item)
    
    @staticmethod
    def generate_key(item) -> str:
        return f'<{item.__class__.__qualname__}({item.link})>'

class InvoiceAdapter(TreeviewAdapter):
    headings = ['File', 'Type', 'Status']

    def __init__(self, invoice):
        super().__init__(invoice)

    def text(self):
        return self.item.link
    
    def tag(self, index):
        if self.item.status == 'done':
            return ('done', )
        elif self.item.status == 'error':
            return ('error', )
        elif self.item.status == 'missing_wo':
            return ('missing_wo', )
        elif self.item.status == 'working':
            return ('working', )
        elif self.item.status == 'uploaded':
            return ('uploaded', )
        else:
            return super().tag(index)
    
    def values(self):
        return (
            self.item.link.name,
            self.item.invoice_type,
            self.item.status
        )
    
    def key(self) -> str:
        return self.item.link.name


Adapter = TypeVar('Adapter', bound=InvoiceAdapter)

class ItemTreeview(ttk.Treeview):
    def __init__(self, master, adapter, *args, **kwargs):
        super().__init__(master, columns=adapter.headings, show='headings', **kwargs)
        self.adapter_class = adapter

        self.font = 'helvetica 10'
        self.style = ttk.Style()
        self.style.configure('Treeview', 
                font=self.font,
                rowheight=font.Font(font=self.font).metrics('linespace') + 5)
        self.style.configure('Treeview.Heading', 
                font=self.font,
                rowheight=font.Font(font=self.font).metrics('linespace') + 20)
        self.style.configure('Scaling.Treeview',  
                rowheight=font.Font(font=self.font).metrics('linespace') + 5)

        self.style.map('Treeview', foreground=self.fixed_map('foreground'), background=self.fixed_map('background'))

        self.displayed_columns = []
        for h in self.adapter_class.headings:
            self.heading(h, text=h, command=lambda h=h: self.on_sort(h))
            self.column(h, stretch=True)

            self.displayed_columns.append(h)
        
        self['displaycolumns'] = self.displayed_columns

        self.tag_configure('even', background='lightsteelblue', foreground='blue4')
        self.tag_configure('odd', background='whitesmoke', foreground='blue4')

        self._content: Dict[str, Adapter] = {}
        self._item_content: Dict[str, Adapter] = {}
    
    def fixed_map(self, option):
        """
            Fix for setting text colour for Tkinter 8.6.9
            From: https://core.tcl.tk/tk/info/509cafafae
            
            Returns the style map for 'option' with any styles starting with
            ('!disabled', '!selected', ...) filtered out.

            style.map() returns an empty list for missing options, so this
            should be future-safe.
        """
        return [elm for elm in self.style.map('Treeview', query_opt=option) if elm[:2] != ('!disabled', '!selected')]

    @property
    def content(self):
        return self._content

    @content.setter
    def content(self, objects):
        self._content = {}

        for o in objects:
            adapter = self.create_adapter(o)
            self._content[adapter.key()] = adapter

        self.build_tree()
    
    @property
    def selected_text(self):
        return self.item(self.focus())['text']
    
    @property
    def selected(self):
        return self._item_content.get(self.focus(), None)
    
    def create_adapter(self, object) -> Adapter:
        return self.adapter_class(object)

    def focus_to_position(self, pos=-1):
        """ Move focus to item in position if possible """
        # Focus on view incase application is focused elsewhere
        self.focus_set()

        children = self.get_children()
        if -1 < pos < len(children):
            self.focus(children[pos])
            self.selection_set(children[pos])
        elif pos >= len(children) and len(children):
            self.focus(children[-1])
            self.selection_set(children[-1])
        else:
            self.focus_set()
            self.selection_set()

    def update_object(self, object: Any):
        object_adapter = self.create_adapter(object)
        key = object_adapter.key()

        if key in self.content:
            adapter = self.content[key]

            if object is None:
                self.delete(adapter.iid)
                del self._item_content[adapter.iid]
                del self.content[key]
            else:
                adapter.object = object
                index = self.index(adapter.iid)
                self.item(adapter.iid, values=adapter.values(), tag=adapter.tag(index))
        else:
            if object is not None:
                adapter = self.create_adapter(object)
                self.create_item(adapter, index=len(self.content))

                self._content[key] = adapter

                self.focus(adapter.iid)
                self.selection_set(adapter.iid)

    def delete_object(self, object: Any):
        key = self.adapter_class.generate_key(object)
        if key in self.content:
            adapter = self._content[key]
            
            self.delete(adapter.iid)

            del self._content[key]
            del self._item_content[adapter.iid]

    def build_tree(self):
        self.clear_tree()

        for i, adapter in enumerate(self.content.values()):
            self.create_item(adapter, i)

    def clear_tree(self):
        self._item_content = {}
        self.delete(*self.get_children())

    def create_item(self, adapter, index):
        adapter.iid = self.insert(
            parent='', 
            index='end', 
            text=adapter.text(), 
            values=adapter.values(), 
            tag=adapter.tag(index)
        )
        
        self._item_content[adapter.iid] = adapter

    def on_sort(self, heading: str = None, reverse: bool = True):
        # Create list with a tuple of value at selected column and itemid
        if heading is None:
            heading = self.adapter_class.headings[0]
            reverse = False
          
        l = [(self.set(iid, heading), iid) for iid in self.get_children()]

        # Try to sort as numbers
        try:
            l.sort(key=lambda t: float(str(t[0]).replace(' ','').replace(',','.')), reverse=reverse)
        except ValueError:
            l.sort(key=lambda t: str(t[0]), reverse=reverse)

        # Move items based on itemid
        for index, (_, iid) in enumerate(l):
            adapter = self._item_content[iid]
            self.item(iid, tags=adapter.tag(index))
            self.move(iid, '', index)

        # Reverse sorting function
        self.heading(heading, command=lambda h=heading: self.on_sort(h, not reverse))


class SearchableTree(ttk.Treeview):
    """ Treeview with search method for items """
    
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        self._detached = set()

        # Number for columns to search 
        self._num_search_values = 2

    def searcher(self, query: str):
        """ Checks if treeview contains query and attaches/detaches them. The detached items are
            stored in a set so they can be reattached later. 
        """
        children = list(self._detached) + list(self.get_children())
        self._detached = set()

        i_r = -1
        for item_id in children:
            values = self.item(item_id)['values'][:self._num_search_values]
            text = ', '.join(str(v).lower() for v in values)
            if query.lower() in text:
                i_r += 1
                self.reattach(item_id, '', i_r)
            else:
                self._detached.add(item_id)
                self.detach(item_id)
        
        self.event_generate('<<TreeviewSearched>>')

from tkinter import ttk

class AutohideScrollbar(ttk.Scrollbar):
    """ Scrollbar that automaticaly palces and hide with on mousewheel scroll """

    HIDE_DELAY = 800

    def __init__(self, *args, **kwargs):
        self.margin_top = kwargs.pop('margin_top') if 'margin_top' in kwargs else 0
        command_wrapper = kwargs.pop('command_wrapper') if 'command_wrapper' in kwargs else None
        super().__init__(*args, **kwargs)

        self.configure(orient=kwargs['orient'] if 'orient' in kwargs else 'vertical')
        self.configure(command=kwargs['command'] if 'command' in kwargs else self.master.yview)
        
        yscrollcommand = self.set if command_wrapper is None else lambda *args: command_wrapper(self.set, *args)
        self.master.configure(yscrollcommand=yscrollcommand)

        self.__isplaced = False
        self.__isactive = False
        self.__ismousedown = False
        self.__cancel_id = None 

        self.__init_bindings()

    
    def __init_bindings(self):
        """ Initialize bindings """
        self.master.bind('<Enter>', lambda _: self.bind_all('<MouseWheel>', self.display))
        self.master.bind('<Leave>', lambda _: self.unbind_all('<MouseWheel>'))

        self.bind('<Enter>', self._on_enter)
        self.bind('<Leave>', self._on_leave)

        self.bind('<Button-1>', self._on_mousedown)
        self.bind('<ButtonRelease-1>', self._on_mouserelease)

    def _on_enter(self, event):
        """ Called when mouse enters widget """
        self.cancel_hide()
        self.__isactive = True
    
    def _on_leave(self, event):
        """ Called when mouse leaves widget """
        if not self.__ismousedown:
            self.schedule_hide()
        self.__isactive = False
    
    def _on_mousedown(self, event):
        """ Called when mouse clicks widget """
        self.__ismousedown = True

    def _on_mouserelease(self, event):
        """ Called when mouse is released """
        self.__ismousedown = False
        self.schedule_hide()
    
    def schedule_hide(self, time: int = 0):
        """ Set widget to be hidden after a time """
        self.cancel_hide()
        self.__cancel_id = self.after(time if time else self.HIDE_DELAY, self.hide)

    def cancel_hide(self):
        """ Cancel scheduled hide """
        if self.__cancel_id is not None:
            self.after_cancel(self.__cancel_id)

    def display(self, event):
        """ Place in master and schedule hide """
        if not self.__isplaced:
            self.place(relx=1, x=-1, rely=0, y=self.margin_top + 1, relheight=1, height=-self.margin_top - 1, anchor='ne')
            self.__isplaced = True
        
        self.schedule_hide()
    
    def hide(self):
        """ Remove from master """
        if self.__isplaced and not self.__isactive:
            self.place_forget()
            self.__isplaced = False


class ScrollbarTreeview(ttk.Treeview):
    """ Treeview with a scrollbar that calls on_scroll() """
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        self.scrollbar = AutohideScrollbar(self, command_wrapper=self.__wrapper)

    def __wrapper(self, callback, *args):
        callback(*args)
        self.on_scroll()
    
    def on_scroll(self):
        pass

class InvoiceTree(ItemTreeview, SearchableTree, ScrollbarTreeview):
    def __init__(self, master, **kwargs):
        super().__init__(master=master, adapter=InvoiceAdapter)
        self._num_search_values = 3

        self.tag_configure('missing_wo', background='grey82', foreground='black')
        self.tag_configure('error', background='gold', foreground='yellow')
        self.tag_configure('done', background='lightgreen', foreground='grey23')
        self.tag_configure('working', background='purple', foreground='grey45')
        self.tag_configure('uploaded', background='lightgreen', foreground='grey45')

