
from __future__ import annotations
from textual.widgets import ListView, ListItem
from textual.message import Message
from textual._types import MessageTarget
from textual import events
from textual.widgets._label import Label
from textual.widget import AwaitMount

class DraggableListItem(ListItem, can_focus=False):
    """
    A draggable list item.
    """
    mouse_down = False
    is_dragging = False
    x = 0
    y = 0

    class DragMessage(Message):
        """Sent for any drag-related events."""
        def __init__(self, sender: MessageTarget, mouse_event):
            self.mouse_event = mouse_event
            super().__init__(sender)

    class DragStart(DragMessage):
        """Sent when the mouse starts dragging."""

    class DragMove(DragMessage):
        """Sent when the mouse is dragging."""

    class DragStop(DragMessage):
        """Sent when the mouse stops dragging."""

    def __init__(self, label: Label, draggable = True):
        super().__init__(label)
        self.value = label
        self.text = self.value.renderable
        self.draggable = draggable
        
        if not self.draggable:
            self.value.styles.color = "white 60%"

    def on_mouse_down(self, event: events.MouseDown) -> None:
        """When a mouse left-button is pressed."""
        if event.button != 1:
            return
        self.mouse_down = True
        self.capture_mouse(capture=True)

    def on_mouse_up(self, event: events.MouseUp) -> None:
        """When a mouse left-button is released."""
        if event.button != 1:
            return
        self.mouse_down = False
        if self.is_dragging:
            self.post_message_no_wait(self.DragStop(self, event))
            self.is_dragging = False
        self.capture_mouse(capture=False)

    def on_mouse_move(self, event: events.MouseMove) -> None:
        """When the mouse moves."""
        if self.mouse_down and self.draggable:
            if not self.is_dragging:
                self.post_message_no_wait(self.DragStart(self, event))
                self.post_message_no_wait(self.DragMove(self, event))
                self.is_dragging = True
            else:
                self.post_message_no_wait(self.DragMove(self, event))

class DraggableListView(ListView):
    """Displays a sortable ListView."""

    DEFAULT_CSS = """

    DraggableListView {
        height: 100%;
        background: black 60%;
        border: tall black;
    }
    """
    def __init__(
        self, 
        *items: DraggableListItem, 
        name:str | None=None, 
        id:str | None=None, 
        classes:str | None=None) -> None:
        
        ListView.__init__(self, *items)
        
        for index, child in enumerate(self.children):
            child.value.update("{}. {}".format(index + 1, child.text))
        
        for index, child in enumerate(self.children):
            if child.draggable:
                self._index = index
                break
            
    def append(self, item:ListItem) -> AwaitMount:        
        await_mount = self.mount(item, before=len(self.children) - 3)
        
        for index, child in enumerate(self.children):
            child.value.update("{}. {}".format(index + 1, child.text))
        
        if len(self) == 1:
            self.index = 0
        return await_mount   
    
    def remove(self, item:ListItem):
        item.remove()
        
        for index, child in enumerate(self.children):
            child.value.update("{}. {}".format(index + 1, child.text))
            
        if len(self) == 1:
            self.index = 0
        
        
    def on_list_item__child_clicked(self, event:ListItem._ChildClicked)->None:
        if not event.sender.draggable:
            event.stop()

    def on_draggable_list_item_drag_start(self, message: DraggableListItem.DragStart) -> None:
        """When a user starts dragging a list item."""
        self.index = self.children.index(message.sender)

    def on_draggable_list_item_drag_move(self, message: DraggableListItem.DragMove) -> None:
        """While a user is dragging a list item."""
        index_sender = self.children.index(message.sender)
        new_index = self._clamp_index(index_sender + message.mouse_event.y)

        if new_index > index_sender:
            self.move_child(index_sender, after=new_index)
        elif new_index < index_sender:
            self.move_child(index_sender, before=new_index)
            
        for index, child in enumerate(self.children):
            child.value.update("{}. {}".format(index + 1, child.text))
        
        self.index = new_index

        # Request a refresh.
        self.refresh()

    def on_draggable_list_item_drag_stop(self, message: DraggableListItem.DragStop) -> None:
        """When a user stops dragging a list item."""
        pass
