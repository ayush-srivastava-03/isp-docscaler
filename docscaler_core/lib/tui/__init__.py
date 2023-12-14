'''
Created on 28 Nov 2022

@author: mwolf
'''

from textual.app import App
from tui.screens import Start, DocScalerForm

class tui(App):
    CSS_PATH = "tui.css"
    TITLE = "DocScaler - Installation Report Generator"
    
    def on_mount(self) -> None:
        self.app.push_screen(Start())