'''
Created on 16 Dec 2022

@author: mwolf
'''
from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.screen import Screen
from textual.widgets import Header, Static, Input, Button
from textual.widgets._header import HeaderTitle, HeaderClock, HeaderClockSpace
from textual.coordinate import Coordinate
from textual.widgets._label import Label

from tui.widgets.DropDown import DropDown
from tui.widgets.EditableDataTable import EditableDataTable, CellList, CellCheckBox
from tui.widgets.DraggableListView import DraggableListView, DraggableListItem

from config import ConfigWriter
from pathlib import Path
from textual.widgets._list_view import ListView

class Body(Container):
    pass

class Column(Container):
    pass

class Section(Container):
    pass

class SectionTitle(Static):
    pass

class Form(Container):
    pass

class EmptyForm(Container):
    pass

class ProjectForm(Container):
    pass

class TemplateSelect(Container):
    pass

class HeaderLarge(Header):
    DEFAULT_CSS = """
    HeaderLarge {
        dock: top;
        width: 100%;
        background: $secondary-background;
        color: $text;
        height: 1;
    }
    """
    def compose(self):
        yield HeaderTitle()
        yield HeaderClock() if self.show_clock else HeaderClockSpace()
        
class Start(Screen):
    DEFAULT_CSS=""" 
    
    Start {
        layout: grid;
        grid-size: 1;
        grid-rows: 22;
        grid-columns: 40%;
        background: #E9EDF4;
        align: center middle;
        overflow-y: hidden;
    }
    
    #start_label {
        width: 20%;
    }

    #start_content {
        margin: 1 0;
        padding: 1 2;
        background: #91969E;
        border: wide #1F2323;
    }
    
    .input {
        width: 70%;
    }
    
    .column {
        padding: 1 1;
    }
    """
    
    directory = "./"
    
    def compose(self) -> ComposeResult:
        yield HeaderLarge(show_clock=False)
        yield Container(
            SectionTitle("New Report"),
            Horizontal(
                Vertical(
                    Static("Enter the path (directory name) for the new report. It will be created if it does not exist. All files will end up in this directory.", classes="text")
                ,classes="column")
            ),
            Horizontal(
                    #Static("", classes="text label", id="start_label"),
                    Input(value=str(Path.cwd()) + "/reports/", placeholder="<directoy name>", classes="input", id="directory")
                   
            ),
            Horizontal(
                Vertical(
                    Button.success("Start", id="start_button")
                ,classes="column")
            ),
            id="start_content"
        )
        
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "start_button":
            #TODO:
            # create directory (and parent) if it does not exist
            # check directory access
            # check if files are in the directory, if yes use this as base if not use the home directory
                        
            #create dir if it does not exist.
            
            path = self.get_widget_by_id("directory").value
            Path(path).mkdir(parents=True, exist_ok=True)
            
            if not path.endswith("/"):
                path = path + "/"
            
            #set this directory as base
            self.app.push_screen(DocScalerForm(path))
 
class DocScalerForm(Screen):
    
    DEFAULT_CSS="""
    DocScalerForm {
        background: transparent;
    }
    """
    
    def __init__(self, reportPath:str):
        Screen.__init__(self)
        self.reportPath = reportPath
    
    def compose(self) -> ComposeResult:
        yield HeaderLarge(show_clock=True)
        yield Container(
            Body(
                Column(
                    Section(
                        SectionTitle("General"),
                        Form(
                            Static("Date:", classes="text label"),
                            Static("Now", classes="labelDate", id="date"), #yield Input(value="Now", classes="input")
                            Static("Document Name:", classes="text label"),
                            Input(placeholder="<e.g. InstallationReport-<company>.pdf>", classes="input", id="document_name"),
                            Static("Title 1: ", classes="text label"),
                            Input(placeholder="<e.g. Project XYZ>", classes="input", id="title1"),
                            Static("Title 2: ", classes="text label"),
                            Input(placeholder="<e.g. 3x ExaScaler Filesystem based on>", classes="input", id="title2"),
                            Static("Title 3: ", classes="text label"),
                            Input(placeholder="<e.g. 2x ES400NVXE and 10x ES7990XE>", classes="input", id="title3")
                        )
                    )
                ),
                Column(
                    Section(
                        SectionTitle("Customer"),
                        Form(
                            Static("Company: ", classes="text label"),
                            Input(placeholder="<Company>", classes="input", id="customer_company"),
                            Static("Logo: ", classes="text label"),
                            DropDown(placeholder = "<Customer Logo>", classes="dropdown", items=self.reportPath, fileTree=True, id="customer_logo", listMount="test"),
                            Static("Name: ", classes="text label"),
                            Input(placeholder="<Customer Name>", classes="input", id="customer_name"),
                            Static("Phone: ", classes="text label"),
                            Input(placeholder="<Customer Phone>", classes="input", id="customer_phone"),
                            Static("Email: ", classes="text label"),
                            Input(placeholder="<Customer Email>", classes="input", id="customer_email"),
                            Static(),Static(),
                            Static("Address 1: ", classes="text label"),
                            Input(placeholder="<e.g. full company name>", classes="input", id="customer_address1"),
                            Static("Address 2: ", classes="text label"),
                            Input(placeholder="<e.g. street>", classes="input", id="customer_address2"),
                            Static("Address 3: ", classes="text label"),
                            Input(placeholder="<e.g. postal code and city>", classes="input", id="customer_address3"),
                            Static("Address 4: ", classes="text label"),
                            Input(placeholder="<e.g. country>", classes="input", id="customer_address4"),
                        )
                    )
                ),
                Column(
                    Section(
                        SectionTitle("DDN Team"),
                        EmptyForm(
                            EditableDataTable(CellList("lib/tui/team.csv", 0, None, False), CellCheckBox(4, None), listMount="test", id="ddn_team")
                        )
                    )
                ),
                Column(
                    Section(
                        SectionTitle("Rack Layout and Network Diagram"),
                        Form(
                            Static("Rack Layout: ", classes="text label"),
                            DropDown(placeholder="<rack layput picture>", items=self.reportPath, fileTree=True, classes="dropdown", id="rack_layout", listMount="test"),
                            Static("Network Diagram: ", classes="text label"),
                            DropDown(placeholder="<network diagram picture>", items=self.reportPath, fileTree=True, classes="dropdown", id="network_diagram", listMount="test")
                        )
                    )
                ),
                Column(
                    Section(
                        SectionTitle("Project(s)"),
                        ProjectContainer(path=self.reportPath, id="ProjectContainer")
                    ),
                    id = "ProjectSection"
                ),
                Column(
                    Section(
                        SectionTitle("Templates"),
                        TemplateConfig(id="TemplateConfig")
                    )
                ),
                Column(
                    Button.success("Save", classes="saveButton", id="save")
                )
                
            , id="test")
        )
        
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.sender.id == "save":
            configWriter = ConfigWriter()
            
            #general
            configWriter.setDate(self.screen.get_widget_by_id("date").renderable)
            configWriter.setDocumentName(self.get_widget_by_id("document_name").value)
            configWriter.setTitle(self.get_widget_by_id("title1").value, 
                                  self.get_widget_by_id("title2").value, 
                                  self.get_widget_by_id("title3").value)
            
            #customer
            configWriter.setCustomerCompany(self.get_widget_by_id("customer_company").value)
            configWriter.setCustomerLogo(self.get_widget_by_id("customer_logo").text)
            configWriter.setCustomerName(self.get_widget_by_id("customer_name").value)
            configWriter.setCustomerPhone(self.get_widget_by_id("customer_phone").value)
            configWriter.setCustomerEmail(self.get_widget_by_id("customer_email").value)
            configWriter.setCustomerAddress(self.get_widget_by_id("customer_address1").value,
                                            self.get_widget_by_id("customer_address2").value,
                                            self.get_widget_by_id("customer_address3").value,
                                            self.get_widget_by_id("customer_address4").value)
            
            #team
            team_list = []
            data_table = self.get_widget_by_id("ddn_team")
            for row in range(data_table.row_count):
                if row >= 0:
                    team_mate = []
                    for column in range(len(data_table.columns)):
                        if data_table.current_cell_checkbox == (row,column):
                            team_mate.append("yes")
                        else:
                            team_mate.append(data_table.get_cell_at(Coordinate(row,column)))
                team_list.append(team_mate)
            
            configWriter.setDDNTeam(team_list)
            
            #network
            configWriter.setRackLayout(self.get_widget_by_id("rack_layout").text)
            configWriter.setNetworkDiagram(self.get_widget_by_id("network_diagram").text)
            
            #project
            project_list = []
            projects = self.get_widget_by_id("ProjectContainer").projects

            for projectId in range(projects + 1):
                
                projectName = self.get_widget_by_id("project_{}".format(projectId)).value
                if projectName:
                    sss_logs = self.get_widget_by_id("project_{}".format(projectId)).parent.sss_logs
                    
                    sss_log_parts = []
                    for sss_log in range(sss_logs + 1):
                        nodes = self.get_widget_by_id("sss{}_nodes_{}".format(sss_log, projectId)).value
                        log = self.get_widget_by_id("sss{}_log_{}".format(sss_log, projectId)).text
                        
                        if log:
                            if nodes:
                                sss_log_parts.append({nodes:log})
                            else:
                                sss_log_parts.append(log)
                    
                    filesystem = self.get_widget_by_id("fs_fs_{}".format(projectId)).text.lower()
                    showall = self.get_widget_by_id("fs_log_{}".format(projectId)).text
                    
                    if sss_log_parts and showall:
                        project_list.append({projectName:{"sfa":sss_log_parts, filesystem:showall}})
                        
                    if sss_log_parts and not showall:
                        project_list.append({projectName:{"sfa":sss_log_parts}})
                        
                    if not sss_log_parts and showall:
                        project_list.append({projectName:{filesystem:showall}})
                    
            configWriter.setProjects(project_list)
            
            #templates
            templates = []
            children = self.get_widget_by_id("TemplateConfig").listview.children
            for template in children:
                templates.append(template.value.name)
            
            configWriter.setTemplates(templates)
            
            configFile = Path(self.reportPath).parts[len(Path(self.reportPath).parts) - 1] + ".config"
            configWriter.writeConfig(self.reportPath, configFile)
            
            self.app.exit(message="\nPlease review the overview and summary template!\nTo create the report run:\n\n./docscaler.py -c {0}\n".format(self.reportPath + configFile))
        
    def on_mount(self) -> None:
        table = self.query_one(EditableDataTable)
        table.add_column("Name", width=23)
        table.add_column("Role", width=30)
        table.add_column("Phone", width=17)
        table.add_column("Email", width=23)
        table.add_column("Creator", width=7)
        table.zebra_stripes = True
        
        for row in range(4):
            table.add_row(*[f"" for col in range(5)], height=1)     

class ProjectContainer(EmptyForm):
    projects = 0
    
    DEFAULT_CSS="""
    ProjectContainer {
        height: auto;
    }
    
    ProjectContainer > Column > Horizontal{
        height: 3;
        align: center middle;
    }
    
    """
    
    def __init__(
        self, *
        children:Widget, 
        name:str | None=None, 
        id:str | None=None, 
        classes:str | None=None,
        path:str | None="./") -> None:
        
        EmptyForm.__init__(self, *children, id=id)
        
        self.path = path
    
    def compose(self) -> ComposeResult:       
        yield ProjectConfig(self.path, index=self.projects)
        yield Column(Horizontal(
            Button.success("+", id="addProjectButton"),
            Button.error("-", id="removeProjectButton", disabled = True)),
            id="addProject"
        )
        
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.sender.id == "addProjectButton":
            self.projects += 1
            self.get_widget_by_id("removeProjectButton").disabled = False
                
            await self.mount(ProjectConfig(self.path, self.projects), before=self.get_widget_by_id("addProject"))
            
            return
            
        if event.sender.id == "removeProjectButton":
            if self.projects > 0:
                await self.get_widget_by_id("projectConfig_{}".format(self.projects)).remove()
                self.refresh(layout=True)
                self.projects -= 1
                
                if self.projects == 0:
                    self.get_widget_by_id("removeProjectButton").disabled = True
            
            return
                    
                

        
class ProjectConfig(ProjectForm):
    DEFAULT_CSS="""  
    ProjectConfig{
        background: #91969E 50%;
    }
    
    ProjectConfig > Horizontal {
        height: 100%;
        layout: grid;
        grid-size: 2;
        grid-columns: 29 1fr;
    }
    """
    
    def __init__(self, path, index) -> None:
        super().__init__(id="projectConfig_{}".format(index))
        self.path = path
        self.index = index
        self.sss_logs = 0
        self.sss_log_ids = []
    
    def compose(self) -> ComposeResult:
        yield Static("Project: ", classes="text label")
        yield Input(placeholder="<project name, e.g. the FS name>", classes="input", id="project_{}".format(self.index))
        yield Static()
        yield Static("SFA: ", classes="text label")
        #Dynamic
        yield Horizontal(Input(placeholder="<e.g node[1-10]>", classes="input", id="sss{}_nodes_{}".format(self.sss_logs, self.index)),
                         DropDown(placeholder="<SSS log files>", classes="dropdown", id="sss{}_log_{}".format(self.sss_logs, self.index), items=self.path, fileTree=True, listMount="test"))
        yield Button.success("+", id="sss{}_add_log".format(self.sss_logs))
        #FS
        yield DropDown([{"value": 1, "text": "Lustre"}, {"value": 2, "text": "GPFS"}], classes="input", id="fs_fs_{}".format(self.index), placeholder="Filesystem", value="1", listMount="test")
        yield DropDown(placeholder="<FS log file>", classes="input", id="fs_log_{}".format(self.index), items=self.path, fileTree=True, listMount="test")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        
        if event.sender.label.plain == "-":
            index = event.sender.id.split("_")[0]
            for child in self.walk_children():
                if child.id is not None:
                    if child.id.split("_")[0] == index:
                        child.remove()
            
            self.sss_log_ids.remove("{}_buttons".format(index))
            
            self.refresh(layout=True)
            self.screen.get_widget_by_id("ProjectContainer").refresh(layout=True)
            self.screen.get_widget_by_id("ProjectSection").refresh(layout=True)
            
            if len(self.sss_log_ids) == 0:
                self.get_widget_by_id("sss0_add_log").visible = True
                
            self.sss_logs -= 1
            
        else:   
            self.sss_logs += 1
            button_id = "sss{}_buttons".format(self.sss_logs)
            self.sss_log_ids.append(button_id)
            
            if len(self.sss_log_ids) == 1:
                event.sender.visible = False
                after = event.sender
            elif len(self.sss_log_ids) > 1:
                after = self.get_widget_by_id("{}_buttons".format(event.sender.id.split("_")[0]))
                
            await self.mount(Static(id="sss{}_space_{}".format(self.sss_logs, self.index)),
                             Horizontal(Input(placeholder="<e.g. node[1-10]>", classes="input", id="sss{}_nodes_{}".format(self.sss_logs, self.index)),
                                        DropDown(placeholder="<SSS log files>", classes="dropdown", id="sss{}_log_{}".format(self.sss_logs, self.index), items=self.path, fileTree=True, listMount="test"), 
                                        id="sss{}_horizontal_{}".format(self.sss_logs, self.index)),
                                 Container(
                                 Button.error("-", id="sss{}_remove_log".format(self.sss_logs), classes="sss_minus"),
                                 Button.success("+", id="sss{}_add_log".format(self.sss_logs), classes="sss_plus"),
                                 classes = "sss_buttons",
                                 id = button_id
                            ), after = after)
            
        
class TemplateConfig(EmptyForm):
    DEFAULT_CSS= """
    TemplateConfig > Horizontal {
        height: 20;
        layout: grid;
        grid-size: 2;
        grid-columns: 50% 50%;
    }
    
    TemplateConfig > Horizontal > Vertical {
        height: 100%;
    }
    
    TemplateConfig > Horizontal > Vertical > Horizontal{
        height: 4;
        layout: grid;
        grid-size: 2;
        grid-columns: 83% 17%;
    }
    
    TemplateConfig DraggableListView {
        height: 100%;
        background: black 60%;
    }
    
    TemplateConfig ListItem {
      background: transparent;
      padding: 0 2;
    }
    """

    def compose(self) -> ComposeResult:
        
        self.listview = DraggableListView(DraggableListItem(Label("Contact", name="contact"), False), 
                            DraggableListItem(Label("Overview", name="overview"), False),
                            DraggableListItem(Label("Summary", name="summary"), False),
                            DraggableListItem(Label("Rack and Network", name="rack_network"), False),
                            DraggableListItem(Label("Project", name="project"), False),
                            DraggableListItem(Label("Maintenance", name="maintenance"), False),
                            DraggableListItem(Label("Support", name="support"), False),
                            DraggableListItem(Label("Appendix", name="appendix"), False)
                    )
        
        yield Horizontal(self.listview,
                            Vertical(
                                Horizontal(
                                    Input(placeholder="<template name>", classes="input", id="new_template"),
                                    Button.success("Add", id="add")
                                ),
                                Horizontal(
                                    Input(placeholder="<click on the template>", id="delete_template"),
                                    Button.error("Delete", id="delete")
                                )
                            )
                        )

    def on_list_view_selected(self, event: ListView.Selected)->None:
        self.screen.get_widget_by_id("delete_template").value = str(event.item.text)
        
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.sender.id == "delete":
            if str(self.listview.highlighted_child.text) == self.screen.get_widget_by_id("delete_template").value:
                self.listview.remove(self.listview.highlighted_child)
                self.screen.get_widget_by_id("delete_template").value = ""
        
        if event.sender.id == "add":
            template = self.screen.get_widget_by_id("new_template").value
            if template != "":
                self.listview.append(DraggableListItem(Label(template, name=template.lower()), True))
                self.screen.get_widget_by_id("new_template").value = ""
        
        
    