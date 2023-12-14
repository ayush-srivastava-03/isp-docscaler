from __future__ import annotations

from textual.widget import Widget, events
from textual.containers import Vertical, Container
from textual.widgets import Label, ListView, ListItem, Input, DirectoryTree
from textual.events import Key
from textual.geometry import Offset

from rich.highlighter import Highlighter

import os
from rich.text import Text
from pathlib import Path
from textual.widgets._directory_tree import DirEntry
from textual.widgets._tree import TreeNode

class DropDownList(Widget):
    DEFAULT_CSS = """
    DropDownList {
      layer: dialog;
      background: #1F2323;
      padding: -1 -1;
      display: none;
    }
    
    DropDownList ListItem {
      background: transparent;
      padding: 0 2;
    }
    
    DropDownList DirectoryTree > .tree--guides {
        color: white;
        text-style: bold;
    }

    DropDownList DirectoryTree {
        background: #4D4F53;
        border: solid #1F2323;
        scrollbar-color: #A71930;
        padding: 0 1;
    }
    """

    def __init__(
        self,
        dropDown: DropDown,
        items: list,
        *children: Widget,
        fileTree: bool | None = False,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self.dropDown = dropDown
        self.items = items
        self.items_filtered = items
        self.fileTree = fileTree
        self.selectedFile = None

    def compose(self):
        widgets = []
        list_items = []
        
        if self.fileTree:
            self.view = DirectoryTree(path=self.items)
        else:  
            for item in self.items:
                list_items.append(ListItem(Label(item["text"])))
            self.view = ListView(*list_items)
        
        widgets.append(self.view)

        yield Container(*widgets)

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:  
        self.selectedFile = os.path.basename(event.path)
        self.on_key(Key(self, "enter", None))
        
    def on_list_view_selected(self, event: ListView.Selected) -> None:
        self.selectedItem = self.items_filtered[self.view.index]["text"]
        self.on_key(Key(self, "enter", None))

    def on_key(self, event: events.Key) -> None:
        if event.key == "enter":
            if not isinstance(self.view, DirectoryTree):
                if self.view.index is not None:
                    self.__selectItem(self.items_filtered[self.view.index]["text"])
                    self.dropDown.value = str(self.items_filtered[self.view.index]["value"])
            else:
                dir_entry = self.view.get_node_at_line(self.view.cursor_line).data
                if dir_entry is None or dir_entry.is_dir:
                    return
                else:
                    self.dropDown.value = dir_entry.path
                    self.__selectItem(Path(dir_entry.path).name)

        if event.key == "tab" or event.key == "shift+tab":
            event.prevent_default()

    def __selectItem(self, item: str) -> None:
        self.dropDown.text = item
        self.display = False
        self.dropDown.focus()
        
    def on_mouse_scroll_down(self, event) -> None:
        event.stop()
        event.prevent_default()
    
    def on_mouse_scroll_up(self, event) -> None:
        event.stop()
        event.prevent_default()
        
    def key_escape(self, event: events.Key) -> None:
        self.view.focus(False)
        self.display = False
        self.view.active = False
        event.stop()
        event.prevent_default()  
    
    def on_descendant_blur(self, event: events.Blur) -> None:
        self.display = False
        

class DropDown(Input, can_focus=True):
    """A dropDown widget with a drop-down."""
    def __init__(
            self,
            items: list,
            listMount: str|Widget,
            fileTree: bool | None = False,
            value: str | None = None,
            placeholder: str = "",
            highlighter: Highlighter | None = None,
            name: str | None = None,
            id: str | None = None,
            classes: str | None = None
    ) -> None:
        super().__init__(
            placeholder=placeholder,
            name=name,
            id=id,
            classes=classes,
            value=str(value)
        )
            
        self.select_classes = classes
        self.items = items
        
        if isinstance(listMount, Widget):
            self.listMount = listMount.id
        else:
            self.listMount = listMount
        
        self.highlighter = highlighter
        self.fileTree = fileTree

        # DropDownList widget
        self.dropdown_list = None

        # The selected text
        self.text = ""

        # there is a value, find the text to display
        if self.value and not self.fileTree:
            for item in self.items:
                if str(item["value"]) == self.value:
                    self.text = item["text"]
                    break

    def render(self) -> str:
        chevron_down = "\u25bc"
        chevron_up = "\u25b2"
        width = self.content_size.width
        text_space = width - 2
        
        if self.dropdown_list.display:
            chevron = chevron_up
        else:
            chevron = chevron_down

        if not self.text:
            text = Text("{text:{text_space}} {chevron}".format(text=self.placeholder,text_space=text_space, chevron=chevron), justify="left")
            text.stylize(self.get_component_rich_style("input--placeholder"),0, text_space)
            
            return text
            
        else:
            text = self.text
            
            if len(text) > text_space:
                text = text[0:text_space]
            
            text = f"{text:{text_space}} {chevron}"

            return text

    def on_mount(self):  
        if self.dropdown_list is None:
            self.dropdown_list = DropDownList(
                dropDown=self,
                items=self.items,
                fileTree=self.fileTree,
                classes=self.select_classes
            )
            
            default_height = 5
            if self.fileTree:
                default_height = 12
                
            if self.dropdown_list.styles.height is None:
                self.dropdown_list.styles.height = default_height
            if self.dropdown_list.styles.min_height is None:
                self.dropdown_list.styles.min_height = default_height
                
            if len(self.items) < 5 and isinstance(self.items, list):
                height = max(1, len(self.items))
                self.dropdown_list.styles.height = height
                self.dropdown_list.styles.min_height = height
                        
            self.screen.get_widget_by_id(self.listMount).mount(self.dropdown_list)

    def on_click(self) -> None:
        self.on_key(Key(self, "enter", None))      

    def on_key(self, event: events.Key) -> None:
        if event.key == "enter":
            self.hide_select_lists()
            self.dropdown_list.styles.width = self.outer_size.width
            
            self.dropdown_list.offset = self.screen.get_widget_by_id(self.listMount).scroll_offset + Offset(self.region.x, self.region.y + 2) #+ \
        
            if isinstance(self.dropdown_list.view, DirectoryTree):
                self.dropdown_list.view.clear()
                self.dropdown_list.view.root = self.dropdown_list.view._add_node(parent=None, label=self.items, data=DirEntry(self.items, True))
                self.dropdown_list.view.load_directory(self.dropdown_list.view.root)
        
            self.dropdown_list.display = True
        
            
            self.dropdown_list.view.focus(scroll_visible=False)
    
    def hide_select_lists(self):
        #Close any open DropDownList widget before opening a new one.
        for dropdownList in self.screen.get_widget_by_id(self.listMount).children:
            if isinstance(dropdownList, DropDownList):
                dropdownList.display = False
