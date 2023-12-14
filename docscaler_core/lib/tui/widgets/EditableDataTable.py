from __future__ import annotations

from textual.widget import events, Widget
from textual.widgets import Input

from textual.widgets._data_table import DataTable, Coordinate
from textual.events import Key, Click, MouseEvent
from textual.widgets._list_item import ListItem
from textual.widgets._label import Label
from textual.widgets._list_view import ListView
from textual.containers import Vertical
from textual.geometry import Offset
from rich.padding import Padding
from rich.style import Style
from rich.text import Text
from textual.message import Message

import csv
from tui.widgets.handler import ClickHandler
from rich.segment import SegmentLines

class TableInput(Input):
    """Input for a table cell."""

    DEFAULT_CSS = """
    TableInput {
        layer: dialog;
        border: none;
        background: #E9EDF4;
        display: none;
        height: auto;
    }
    
    TableInput:focus {
        border: none;
    }
    
    TableInput > .input--cursor {
        background: #E9EDF4;
        color: #1F2323;
        text-style: reverse;
    }
    
    """

    def __init__(
        self,
        editableDataTable: EditableDataTable,
        value: str | None = None,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(
            value=value,
            placeholder="",
            name=name,
            id=id,
            classes=classes
        )

        self.editableDataTable  = editableDataTable
       
    def key_enter(self, event: events.Key) -> None:
        self.editableDataTable._data[self.editableDataTable._row_locations.get_key(self.editableDataTable.cursor_row)][self.editableDataTable._column_locations.get_key(self.editableDataTable.cursor_column)] = self.value
        self.editableDataTable.focus(False)
        self.display = False
        
        event.stop()
        event.prevent_default()
        
    def key_tab(self, event: events.Key) -> None:
        self.editableDataTable._data[self.editableDataTable._row_locations.get_key(self.editableDataTable.cursor_row)][self.editableDataTable._column_locations.get_key(self.editableDataTable.cursor_column)] = self.value        
        self.editableDataTable.focus(True)
        self.display = False
        
        if len(self.editableDataTable.columns) == self.editableDataTable.cursor_column + 1:
            if len(self.editableDataTable.rows) == self.editableDataTable.cursor_row + 1:
                self.editableDataTable.cursor_coordinate = Coordinate(0, 0)
            else:
                self.editableDataTable.cursor_coordinate = Coordinate(self.editableDataTable.cursor_row + 1, 0)
        else:
            self.editableDataTable.cursor_coordinate = Coordinate(self.editableDataTable.cursor_row, self.editableDataTable.cursor_column + 1)

        event.stop()
        event.prevent_default() 
        self.editableDataTable.key_enter(Key(self, "enter", None))
        
    def key_shift_tab(self, event: events.Key) -> None:
        self.editableDataTable._data[self.editableDataTable._row_locations.get_key(self.editableDataTable.cursor_row)][self.editableDataTable._column_locations.get_key(self.editableDataTable.cursor_column)] = self.value        
        self.editableDataTable.focus(True)
        self.display = False
        
        if len(self.editableDataTable.columns) == self.editableDataTable.cursor_column + 1:
            if len(self.editableDataTable.rows) == self.editableDataTable.cursor_row + 1:
                self.editableDataTable.cursor_coordinate = Coordinate(0, 0)
            else:
                self.editableDataTable.cursor_coordinate = Coordinate(self.editableDataTable.cursor_row + 1, 0)
        else:
            self.editableDataTable.cursor_coordinate = Coordinate(self.editableDataTable.cursor_row, self.editableDataTable.cursor_column + 1)

        event.stop()
        event.prevent_default() 
        self.editableDataTable.key_enter(Key(self, "enter", None))

    def key_escape(self, event: events.Key) -> None:
        self.editableDataTable.focus(False)
        self.display = False
        
        event.stop()
        event.prevent_default()

class TableListView(ListView):
    DEFAULT_CSS="""
    TableListView{
        scrollbar-color: #A71930;
    }
    """
    
    
    clickHandler = ClickHandler()
    
    def __init__(
        self,
        *children: ListItem,
        table_list: TableList,
        initial_index: int | None = 0,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(
            *children, initial_index=initial_index, name=name, id=id, classes=classes
        )
        self.table_list = table_list

    def on_blur(self) -> None:
        self.table_list.display = False

    def on_click(self, event: events.MouseEvent) -> None:
        self.clickHandler.checkClick(self, event)
            
    def key_enter(self, event: events.Key) -> None:
        self.table_list.selectItem(self.index)
        self.table_list.data_table.focus(False)
        self.table_list.display = False
        self.table_list.active = False
        event.stop()
        event.prevent_default()
        
    def key_escape(self, event: events.Key) -> None:
        self.table_list.data_table.focus(False)
        self.table_list.display = False
        self.table_list.active = False
        event.stop()
        event.prevent_default()   
        
    def on_single_click(self, event: MouseEvent):
        self.table_list.selectItem(self.index)
        self.table_list.data_table.focus(False)
        self.table_list.display = False
        self.table_list.active = False
        event.stop()
        event.prevent_default()

class TableList(Widget):
    DEFAULT_CSS = """
    TableList {
        layer: dialog;
        background: black 60%;
        border: solid black;
        display: none;
    }
    
    TableList ListItem {
        background: transparent;
        padding: 0 0;
    }
    
    TableList ListItem > Widget :hover {
        background: black 30%;
    }
    
    TableList ListView:focus > ListItem.--highlight {
        background: black;
    }
    """

    def __init__(
        self,
        data_table: EditableDataTable,
        items: list,
        *children: Widget,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)
        
        self.data_table = data_table
        self.view = TableListView(*items, table_list=self)
        self.listWidth = 0
        self.active = False
        
    def compose(self):
        yield Vertical(self.view)
        
    #TODO: change to flexible padding values
    def setListItems(self, items: CellList):
        self.view.clear()
        self.listWidth = 0
        
        self.items = items
        for item in self.items.listData():
            listItem = ListItem(Label(item["text"]))
            if len(item["text"]) + 6 > self.listWidth:
                self.listWidth = len(item["text"]) + 6
            self.view.append(listItem)
            
    def selectItem(self, index:int) -> None:
        if index is not None:
            for idx, cell in enumerate(self.items.cellData(index)):
                self.data_table._data[self.data_table._row_locations.get_key(self.data_table.cursor_row)][self.data_table._column_locations.get_key(idx)] = cell
                
    def on_mouse_scroll_down(self, event) -> None:
        event.stop()
        event.prevent_default()
    
    def on_mouse_scroll_up(self, event) -> None:
        event.stop()
        event.prevent_default()

class CellItem():
    def __init__(self, column:int, row:int):
        self._column = column
        self._row = row

    def column(self, column:int):
        if self._column == None:
            return True
        else:
            if self._column == column:
                return True
            
        return False
    
    def row(self, row:int):
        if self._row == None:
            return True
        else:
            if self._row == row:
                return True
            
        return False

class CellEdit(CellItem):
    def __init__(self, column:int, row:int, enableEdit:bool = True):
        super().__init__(column, row)
        
        self._enableEdit = enableEdit
    
    def editEnabled(self):
        return self._enableEdit

class CellCheckBox(CellItem):
    def __init__(self, column:int, row:int, enabled:bool = False):
        super().__init__(column, row)
        
        self._enabled = enabled
    
    def enabled(self):
        return self._enabled
    
    def setEnabled(self):
        if self._enabled:
            self._enabled = False
        else:
            self._enabled = True

class CellList(CellItem):
    def __init__(self, csv_file:str, column:int, row:int, enableEdit:bool = False, placeholder:str = "Select..."):
        super().__init__(column, row)
        
        self._raw_data = csv_file
        self._enableEdit = enableEdit
        self._placeholder = placeholder
        
        self._listData = []
        self._cellData = []
        
        with open(csv_file) as csvfile:
            rows = sorted(csv.reader(csvfile, delimiter=","))
            
            for index, cellData in enumerate(rows):
                if cellData[0] != "name":
                    self._cellData.append(cellData)
                    self._listData.append({"value": index, "text": cellData[0]})
    
    def editEnabled(self):
        return self._enableEdit
    
    def listData(self):
        return self._listData
    
    def cellData(self, index:int):
        return self._cellData[index]
    
    def placeholder(self):
        return self._placeholder
        

class EditableDataTable(DataTable): 
    DEFAULT_CSS = """
    EditableDataTable {
        height: 1;
        width: 100%;
    }
    """
    
    clickHandler = ClickHandler()
    
    current_cell_edit = None
    current_cell_checkbox = None
    
    def __init__(self, *items: CellItem, listMount: str|Widget, id:str = None):
        super().__init__(id=id)
        self.items = items
        
        if isinstance(listMount, Widget):
            self.listMount = listMount.id
        else:
            self.listMount = listMount
    
    def handleCellItem(self, row:int, column:int) -> None:
        cell_region = self._get_cell_region(self.cursor_coordinate)
        
        item = self.getCellItem(row, column)
                
        if isinstance(item, CellEdit):
            if not item.editEnabled():
                return 
        
        if isinstance(item, CellList):
            if self.tableList.active:
                self.tableList.display = False
                self.tableList.active = False
                return
            else:
                self.tableList.setListItems(item)
                self.tableList.styles.width = self.tableList.listWidth #cell_region.width
                self.tableList.offset = self.screen.get_widget_by_id(self.listMount).scroll_offset + cell_region.offset + Offset(self.region.x, self.region.y)
                self.tableList.display = True
                self.tableList.active = True
                self.tableList.view.focus(scroll_visible=False)
                return
        
        if isinstance(item, CellCheckBox):
            if isinstance(self.getCellItem(self.cursor_row, self.cursor_column), CellCheckBox):
                if self.current_cell_checkbox == None:
                    self.current_cell_checkbox = (self.cursor_row, self.cursor_column)
                else:
                    if self.current_cell_checkbox[0] == self.cursor_row and self.current_cell_checkbox[1] == self.cursor_column:
                        self.current_cell_checkbox = None
                    else:
                        self.current_cell_checkbox = (self.cursor_row, self.cursor_column)
                
                
                self.refresh_column(self.cursor_column)
                #self.refresh()
            return
        
        self.current_cell_edit = (self.cursor_row, self.cursor_column)
        self.tableInput.styles.width = cell_region.width
        self.tableInput.offset = cell_region.offset
        self.tableInput.value = self._data[self._row_locations.get_key(self.cursor_row)][self._column_locations.get_key(self.cursor_column)]
        self.tableInput.display = True
        self.tableInput.focus()
        
    def getCellItem(self, row:int, column:int) -> CellItem:
        for item in self.items:
            if item.row(row) and item.column(column):
                return item

    def _render_cell(
        self,
        row_index: int,
        column_index: int,
        style: Style,
        width: int,
        cursor: bool = False,
        hover: bool = False,
    ) -> SegmentLines:
        """Render the given cell.

        Args:
            row_index: Index of the row.
            column_index: Index of the column.
            style: Style to apply.
            width: Width of the cell.
            cursor: Is this cell affected by cursor highlighting?
            hover: Is this cell affected by hover cursor highlighting?

        Returns:
            A list of segments per line.
        """
        is_header_row = row_index == -1

        # The header row *and* fixed columns both have a different style (blue bg)
        is_fixed_style = is_header_row or column_index < self.fixed_columns
        show_cursor = self.show_cursor

        if hover and show_cursor and self._show_hover_cursor:
            style += self.get_component_styles("datatable--highlight").rich_style
            if is_fixed_style:
                # Apply subtle variation in style for the fixed (blue background by
                # default) rows and columns affected by the cursor, to ensure we can
                # still differentiate between the labels and the data.
                style += self.get_component_styles(
                    "datatable--highlight-fixed"
                ).rich_style

        if cursor and show_cursor:
            style += self.get_component_styles("datatable--cursor").rich_style
            if is_fixed_style:
                style += self.get_component_styles("datatable--cursor-fixed").rich_style

        if is_header_row:
            row_key = self._header_row_key
        else:
            row_key = self._row_locations.get_key(row_index)

        column_key = self._column_locations.get_key(column_index)
        cell_cache_key = (row_key, column_key, style, cursor, hover, self._update_count)
        if cell_cache_key not in self._cell_render_cache:
            style += Style.from_meta({"row": row_index, "column": column_index})
            height = self.header_height if is_header_row else self.rows[row_key].height
            cell = self._get_row_renderables(row_index)[column_index]
            
            if isinstance(self.getCellItem(row_index, column_index), CellList) and row_index >= 0:
                chevron_down = "\u25bc"
                chevron_up = "\u25b2"
                
                text = cell.plain
                if len(text) == 0:
                    text = self.getCellItem(row_index, column_index).placeholder()
                
                text_space = width - 4
                
                if self.tableList.display and self.cursor_row == row_index and self.cursor_column == column_index:
                    chevron = chevron_up
                else:
                    chevron = chevron_down
                    
                if len(text) > width:
                    text = text[:width]
                    text_space = 0
                
                cell = Text(f"{text:{text_space}} {chevron}")
            
            if isinstance(self.getCellItem(row_index, column_index), CellCheckBox) and row_index >= 0:
                ballot_box_clear = "\u2610"
                ballot_box_set = "\u2611"
            
                if self.current_cell_checkbox != None:
                    if self.current_cell_checkbox[0] == row_index and self.current_cell_checkbox[1] == column_index:
                        ballot_box = ballot_box_set
                    else:
                        ballot_box = ballot_box_clear
                else:
                    ballot_box = ballot_box_clear

                cell = Text(f"{ballot_box:^{width-2}}")
            
            
            lines = self.app.console.render_lines(
                Padding(cell, (0, 1)),
                self.app.console.options.update_dimensions(width, height),
                style=style,
            )
            self._cell_render_cache[cell_cache_key] = lines
        return self._cell_render_cache[cell_cache_key]   
    
    def on_mount(self):
        self.tableInput = TableInput(self, None)
        self.tableInput.styles.height = 1
        self.tableInput.styles.min_height = 1
        
        self.mount(self.tableInput)
        
        self.tableList = TableList(self, items=[])
        self.tableList.styles.height = 6
        self.tableList.styles.min_height = 6
        self.screen.get_widget_by_id(self.listMount).mount(self.tableList)
        
    def on_click(self, event: Click) -> None:
        self.clickHandler.checkClick(self, event)

    def on_single_click(self, event: Message) -> None:
        self.key_enter(Key(self, "enter", None))

    def on_double_click(self, message: Message) -> None:
        pass

    def key_enter(self, event: events.Key) -> None:
        self.handleCellItem(self.cursor_row, self.cursor_column)
        event.stop()
        event.prevent_default()

    def action_cursor_down(self):
        if not self.tableInput.has_focus:
            DataTable.action_cursor_down(self)
        
    def action_cursor_up(self):
        if not self.tableInput.has_focus:
            DataTable.action_cursor_up(self)

    def action_cursor_right(self):
        if not self.tableInput.has_focus:
            DataTable.action_cursor_right(self)

    def action_cursor_left(self):
        if not self.tableInput.has_focus:
            DataTable.action_cursor_left(self)
            
