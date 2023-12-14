'''
Created on 22 Feb 2023

@author: mwolf
'''
from __future__ import annotations
from textual._types import MessageTarget
from textual.events import MouseEvent, Click
from rich.style import Style
from textual.widget import Widget

class ClickHandler(Widget):
    singleClickTimer = None
    event = None
    
    def checkClick(self, sender: Widget, event: MouseEvent):
        if isinstance(event, Click):
            self.sender = sender
            
            if self.singleClickTimer is not None:
                if not self.singleClickTimer._task.done():
                    self.event = DoubleClick(self.sender, 
                                               event.x, 
                                               event.y, 
                                               event.delta_x, 
                                               event.delta_y, 
                                               event.button, 
                                               event.shift,
                                               event.meta,
                                               event.ctrl,
                                               event.screen_x,
                                               event.screen_y,
                                               event.style)
                    self._emitMessage()
                    #raise Exception("SELF TUUUUT", self.event)
            else:
                self.event = SingleClick(self.sender, 
                                               event.x, 
                                               event.y, 
                                               event.delta_x, 
                                               event.delta_y, 
                                               event.button, 
                                               event.shift,
                                               event.meta,
                                               event.ctrl,
                                               event.screen_x,
                                               event.screen_y,
                                               event.style)
                
                self.singleClickTimer = self.set_timer(name="SingleClick", delay=0.25, callback=self._emitMessage)
                #raise Exception("SELF TUUUUT", self.singleClickTimer, self.event)
            
            
    async def _emitMessage(self):
        self.singleClickTimer.stop_no_wait()
        self.singleClickTimer = None
        await self.sender.post_message(self.event)

class SingleClick(MouseEvent):
    def __init__(
        self,
        sender: MessageTarget,
        x: int,
        y: int,
        delta_x: int,
        delta_y: int,
        button: int,
        shift: bool,
        meta: bool,
        ctrl: bool,
        screen_x: int | None = None,
        screen_y: int | None = None,
        style: Style | None = None,
    ) -> None:
        super().__init__(sender, x, y, delta_x, delta_y, button, shift, meta, ctrl, screen_x, screen_y, style)    

    def __str__(self)->str:
        return "SingleClick"
    
class DoubleClick(MouseEvent):
    def __init__(
        self,
        sender: MessageTarget,
        x: int,
        y: int,
        delta_x: int,
        delta_y: int,
        button: int,
        shift: bool,
        meta: bool,
        ctrl: bool,
        screen_x: int | None = None,
        screen_y: int | None = None,
        style: Style | None = None,
    ) -> None:
        super().__init__(sender, x, y, delta_x, delta_y, button, shift, meta, ctrl, screen_x, screen_y, style)
    
    def __str__(self)->str:
        return "DoubleClick"