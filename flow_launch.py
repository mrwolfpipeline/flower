import json
import sys

from PySide2 import QtCore

from auto_load_ui import autoloadUi  # Import the autoloadUi function
from flow_launch_stylesheet import radio_button_style
import util_flow
import util_globals as FL

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

from ui_checkable_combobox import checkablecombobox

import table_populator
import table_controller

settings_json = 'settings.json'

#TODO: Add default version for each project application into SG then read from there

class SplashScreen(QSplashScreen):
    def __init__(self):
        super().__init__(QPixmap('ui/images/application_icon.png'))
        self.setWindowFlags(Qt.SplashScreen | Qt.WindowStaysOnTopHint)
        self.setMask(self.pixmap().mask())

        # Add progress bar
        self.progressBar = QProgressBar(self)
        self.progressBar.setMaximum(100)
        self.progressBar.setGeometry(30, self.pixmap().height() - 40, self.pixmap().width() - 60, 20)
        self.progressBar.setValue(0)

    def set_progress(self, value):
        self.progressBar.setValue(value)

class FlowLaunch(QWidget):
    def __init__(self):
        super().__init__()

        # Load the UI file using autoloadUi
        self.ui = autoloadUi(self, customWidgets=[checkablecombobox])

        # Authenticate User
        FL.sg = util_flow.get_sg_connection()
        self.user_object = FL.sg_user_object
        self.user_name = str(self.user_object)
        self.user_details = util_flow.get_user_details(self.user_name)
        self.user_tasks = None
        self.task_field_dict = {}

        self.selected_project = None
        self.prev_selected_display_fields = None
        self.entity_map = util_flow.get_entity_info()

        self.init_ui()

    def init_ui(self):
        print('MW LAUNCHER::: SG USER: ' + self.user_name)

        self.labelActiveUser.setText(self.user_name)
        self.labelActiveUserPermissions.setText(FL.user_permission_group)

        # Set Window Title
        self.setWindowTitle('Flow Launcher')

        # Create a list of buttons to group together based on their names in the UI file.
        # This is to create a radio button group
        self.launch_button_list = [self.buttonNuke, self.buttonMaya, self.buttonBlender, self.buttonHoudini,
                                   self.buttonSyntheyes]
        self.default_button_launch_list = [self.buttonDefaultNuke, self.buttonDefaultMaya, self.buttonDefaultBlender,
                                           self.buttonDefaultHoudini, self.buttonDefaultSyntheyes]
        self.default_tab_button_list = [self.buttonDefaultTasks, self.buttonDefaultFolders]

        # Create a button group for radio button functionality
        self.launch_button_group = QButtonGroup()
        self.default_launch_button_group = QButtonGroup()
        self.default_tab_button_group = QButtonGroup()
        self.buttonDefaultApplication.setEnabled(False)
        self.buttonDefaultTab.setEnabled(False)

        # Load settings from json file
        with open(settings_json, 'r') as file:
            data = json.load(file)
            # Load user defaults for radio buttons
            self.defaultTab = data['settingDefaultTabRadio']
            self.settingDefaultApplication = data['settingDefaultApplicationRadio']
            self.flowURL = data['settingFlowURL']
            self.display_field_list = data["settingDisplayFields"]

            # this is designed to get the value from the json and apply it to the matching name in the ui.
            # for this to work the line edit in the ui needs to have the same name as the propery in the json
            # ignore radio button settings
            for setting_name, setting_value in data.items():
                if "Radio" in setting_name.lower():
                    continue
                # if isinstance(setting_value, str) and hasattr(self, setting_name):
                if hasattr(self, setting_name):
                    line_edit = getattr(self, setting_name)
                    if isinstance(setting_value, list):
                        setting_value = ', '.join(setting_value)
                    line_edit.setText(setting_value)
                    line_edit.setReadOnly(True)
                    line_edit.setStyleSheet("QLineEdit[readOnly=\"true\"] { background-color: #f0f0f0; }")

        # # Setup radio button functionality for the button group
        self.setup_radio_button_group(self.launch_button_group, self.launch_button_list, setting=None,
                                      default_group=False, default_button=None, default_variable=None)
        self.setup_radio_button_group(self.default_launch_button_group, self.default_button_launch_list,
                                      setting='settingDefaultApplicationRadio',
                                      default_group=True, default_button=self.buttonDefaultApplication,
                                      default_variable=self.settingDefaultApplication)
        self.setup_radio_button_group(self.default_tab_button_group, self.default_tab_button_list,
                                      setting='settingDefaultTabRadio', default_group=True,
                                      default_button=self.buttonDefaultTab, default_variable=self.defaultTab)

        # Convert string to lists
        self.settingTaskTaskStatusesList = self.settingTaskTaskStatuses.text().split(', ')
        self.settingFolderShotStatusesList = self.settingFolderShotStatuses.text().split(', ')
        self.settingFolderTaskStatusesList = self.settingFolderTaskStatuses.text().split(', ')

        # Go through the system settings grid and define the button setting dict. as long as everything is named
        # in the UI file correctly as buttonBlenderFolder : settingBlenderFolder for example then it will work
        button_setting_dict = {}

        for i in range(self.systemSettingsGrid.rowCount()):
            for j in range(self.systemSettingsGrid.columnCount()):
                item = self.systemSettingsGrid.itemAtPosition(i, j)
                if item is not None and isinstance(item.widget(), QPushButton):
                    button = item.widget()
                    setting_name = 'setting' + button.objectName().replace('button', '')
                    setting = getattr(self, setting_name, None)  # Assuming self is the reference to the current object
                    if setting:
                        button_setting_dict[button] = setting

                # Call the connect_buttons method with the button_setting_dict
        self.connect_settings_buttons_and_line_edits(button_setting_dict)

        # Enable the button corresponding to the default application
        if self.settingDefaultApplication == "NUKE":
            self.buttonNuke.setChecked(True)
            self.buttonDefaultNuke.setChecked(True)
        elif self.settingDefaultApplication == "MAYA":
            self.buttonMaya.setChecked(True)
            self.buttonDefaultMaya.setChecked(True)
        elif self.settingDefaultApplication == "BLENDER":
            self.buttonBlender.setChecked(True)
            self.buttonDefaultBlender.setChecked(True)
        elif self.settingDefaultApplication == "HOUDINI":
            self.buttonHoudini.setChecked(True)
            self.buttonDefaultHoudini.setChecked(True)
        elif self.settingDefaultApplication == "SYNTHEYES":
            self.buttonSyntheyes.setChecked(True)
            self.buttonDefaultSyntheyes.setChecked(True)

        if self.defaultTab == "TASKS":
            self.buttonDefaultTasks.setChecked(True)

        if self.defaultTab == "FOLDERS":
            self.buttonDefaultFolders.setChecked(True)

        # Load the default view from the settings
        for i in range(self.appTabs.count()):
            tab_text = self.appTabs.tabText(i)
            if tab_text == self.defaultTab:
                self.appTabs.setCurrentIndex(i)
                break

        self.buttonFieldDisplay.clicked.connect(self.save_display_fields)

        # Setup taskFilterComboBox
        self.setupFilterComboBox("Task Task Status", self.taskFilterComboBox, data["settingTaskTaskStatuses"])

        # Setup foldersShotStatusFilter
        self.setupFilterComboBox("Folder Shot Status", self.foldersShotStatusFilter, data["settingFolderShotStatuses"])

        # Setup foldersTaskStatusFilter
        self.setupFilterComboBox("Folder Task Status", self.foldersTaskStatusFilter, data["settingFolderTaskStatuses"])

        self.buttonFlowSite.clicked.connect(lambda: self.openUrlWithHttps(self.flowURL))

        self.build_sg_task_field_controllers()

        self.load_display_fields()

        # Load user tasks
        self.convert_display_names_to_field_names()
        self.user_tasks = util_flow.get_user_tasks_custom(self.user_name, self.backend_field_list)

        # TODO: need to figure out way so that when you select columns to display those columns are updated in the table tasks table and table tasks is refreshed
        # reloading the project selected
        self.table_manager = table_controller.TableManager(self.tableTasks, self.tableTaskProjects, self.user_tasks, self.task_field_dict, self.backend_field_list, self.display_field_list)
        self.table_manager.table_creator()

    # # Go through mapping of fields to build proper field names based on field and entity relationships
    def convert_display_names_to_field_names(self):
        self.task_field_dict = {}
        self.backend_field_list = []

        for display_name in self.display_field_list:
            entity, display_field = display_name.split('.')
            field_dict = self.entity_map.get(entity)
            field_name = field_dict.get(display_field).get('field_name')
            data_type = field_dict.get(display_field).get('data_type')
            valid_type = field_dict.get(display_field).get('valid_types')

            # MAP RELATIONSHIPS FOR MODIFIED FIELD NAME AS IT RELATES TO TASK ENTITY
            if entity == 'Task':
                pass

            elif entity == 'Project':
                field_name = 'project.Project.' + field_name

            else:
                if data_type == 'entity':
                    field_name = 'entity.' + str(entity) + '.' + field_name + '.' + 'name'

                else:
                    field_name = 'entity.' + str(entity) + '.' + str(field_name)

            # key = (entity, field_name, display_field)  # Create a tuple key
            key = field_name

            if key not in self.task_field_dict:
                self.task_field_dict[key] = {}  # Use the tuple key
            if field_name:
                self.task_field_dict[key] = field_dict[display_field]

        self.backend_field_list = [key for key in self.task_field_dict.keys()]

        # ADD DEFAULT FIELDS TO TASK FIELD DICT
        self.task_field_dict[('id')] = {'data_type': 'number', 'entity_type': 'Task', 'display_name': 'Task Id', 'field_name': 'id', 'valid_types': None}
        self.task_field_dict[('project.Project.id')] = {'data_type': 'number', 'entity_type': 'Project', 'display_name': 'Project Id', 'field_name': 'project.Project.id', 'valid_types': None}
        self.task_field_dict[('entity.Shot.id')] = {'data_type': 'number', 'entity_type': 'Shot', 'display_name': 'Shot Id', 'field_name': 'entity.Shot.id', 'valid_types': None}

    def load_display_fields(self):
        task_field_list = []
        shot_field_list = []
        project_field_list = []
        for field in self.display_field_list:
            self.fieldList.addItem(field)
            if "Task." in field:
                field = field.replace("Task.", "")
                task_field_list.append(field)

            if "Project." in field:
                field = field.replace("Project.", "")
                project_field_list.append(field)

            if "Shot." in field:
                field = field.replace("Shot.", "")
                shot_field_list.append(field)

        self.taskFields.checkItems(task_field_list)
        self.shotFields.checkItems(shot_field_list)
        self.projectFields.checkItems(project_field_list)

        self.prev_selected_display_fields = self.display_field_list

    def save_display_fields(self):
        self.update_display_fields()
        self.update_json("settingDisplayFields", self.display_field_list, button=None, default_variable=None)

    def update_display_fields(self):
        self.display_field_list = []

        # Iterate over each item in self.fieldList
        for index in range(self.fieldList.count()):
            item = self.fieldList.item(index)
            # Append the text of the item to my_list
            self.display_field_list.append(item.text())

        self.convert_display_names_to_field_names()
        self.user_tasks = util_flow.get_user_tasks()
        self.table_manager.update_task_table(self.display_field_list)


    def build_sg_task_field_controllers(self):
        print("Building SG task fields")

        task_field_names = list(self.entity_map['Task'].keys())
        project_field_names = list(self.entity_map['Project'].keys())
        shot_field_names = list(self.entity_map['Shot'].keys())

        self.setupFilterComboBox("Task Fields", self.taskFields, task_field_names)
        self.setupFilterComboBox("Project Fields", self.projectFields, project_field_names)
        self.setupFilterComboBox("Shot Fields", self.shotFields, shot_field_names)

        self.taskFields.model().sort(0)
        self.projectFields.model().sort(0)
        self.shotFields.model().sort(0)

        self.fieldList.setStyleSheet("""
        QListWidget {
            alternate-background-color: #cce6ff; /* Light blue color */
            spacing: 3px; /* Adjust spacing between items */
        }
        """)

    def openUrlWithHttps(self, url):
        # Check if the URL starts with "http://" or "https://"
        if url.startswith("http://") or url.startswith("https://"):
            # If it does, open the URL directly
            QDesktopServices.openUrl(QUrl(url))
        else:
            # If it doesn't, prepend "https://" to the URL and then open it
            QDesktopServices.openUrl(QUrl("https://" + url))

    def setupFilterComboBox(self, type, combo_box, data):
        combo_box.addItems(data)
        combo_box.filter_type = type

        # Find the length of the longest item
        widest_item_length = max(len(combo_box.model().item(i).text()) for i in range(combo_box.model().rowCount()))

        # Adjust the width_factor as needed for additional spacing
        width_factor = 10  # Adjust this value as needed
        combo_box_width = widest_item_length * width_factor

        # Set the width of the combo box
        combo_box.setFixedWidth(combo_box_width)

        combo_box.selectionChanged.connect(self.handleSelectionChanged)

    def value_in_list(self,list, value):
        items = list.findItems(value, QtCore.Qt.MatchExactly)
        return len(items) > 0

    def handleSelectionChanged(self, type, selected, deselected):
        if type == "Task Task Status":
            self.filter_table(self.tableTasks)

        # TODO update for other tables
        elif type == "Folder Shot Status":
            self.filter_table(self.tableTasks)

        # TODO update for other tables
        elif type == "Folder Task Status":
            self.filter_table(self.tableTasks)

        elif type in ["Task Fields", "Project Fields", "Shot Fields"]:
            self.update_fields_by_type(type, selected)

    def update_fields_by_type(self, type, selected):
        selected_modified = []
        field_type = type.replace(" Fields", ".")
        for task_field in selected:
            task_field = field_type + task_field
            selected_modified.append(task_field)

        field_type_prefix = field_type[:-1]  # Remove the dot

        # Filter the previous and current selected display fields based on field type
        filtered_list1 = [item for item in self.prev_selected_display_fields if item.startswith(field_type)]
        filtered_list2 = [item for item in selected_modified if item.startswith(field_type)]

        # Convert filtered lists to sets
        set1 = set(filtered_list1)
        set2 = set(filtered_list2)

        # Find items added to list2 compared to list1
        added_items = set2 - set1

        # Find items removed from list2 compared to list1
        removed_items = set1 - set2

        # Remove items from the QListWidget
        for item_text in removed_items:
            if item_text.startswith(field_type_prefix):  # Check if the item belongs to the correct type
                item = self.fieldList.findItems(item_text, Qt.MatchExactly)
                if item:
                    self.fieldList.takeItem(self.fieldList.row(item[0]))
                    self.prev_selected_display_fields.remove(item_text)

        # Add items to the QListWidget
        for item_text in added_items:
            if item_text.startswith(field_type_prefix):  # Check if the item belongs to the correct type
                self.fieldList.addItem(item_text)
                self.prev_selected_display_fields.append(item_text)

        self.update_display_fields()

    def closeEvent(self, event):
        # Call your function here
        self.save_settings_on_exit()

    def save_settings_on_exit(self):
        # TODO: Add functionality for saving project, shot last on etc.
        print("TO DO SAVE SETTINGS")
        # current_launch_application = self.launch_button_group.checkedButton().text()
        # current_index = self.appTabs.currentIndex()
        # current_tab_name = self.appTabs.tabText(current_index)
        #
        # self.update_json("settingDefaultApplicationRadio", current_launch_application)
        # self.update_json("settingDefaultTabRadio", current_tab_name)

    def connect_settings_buttons_and_line_edits(self, button_setting_dict):
        for button, setting in button_setting_dict.items():
            button.clicked.connect(lambda b=button, s=setting: self.toggle_edit_mode(b, s))

    # Slot to handle button clicks
    def handle_radio_button_click(self, button_group, button, setting, default_group, default_button, default_variable):
        # Uncheck all buttons except the one that was clicked
        for btn in button_group.buttons():
            if btn is not button:
                btn.setChecked(False)

        # Handle default radio button click if it's a default group
        if default_group and button.text() != default_variable:
            default_button.setEnabled(True)
            default_button.clicked.connect(lambda: self.update_json(setting, button.text(), button=default_button, default_variable=default_variable))
        elif default_group:
            default_button.setEnabled(False)
            default_button.clicked.disconnect()  # Disconnect the signal

    def setup_radio_button_group(self, button_group, button_name_list, default_group=None, setting=None, default_button=None, default_variable=None):
        for button in button_name_list:
            button.setCheckable(True)
            button.setChecked(False)
            button.setStyleSheet(radio_button_style)
            button_group.addButton(button)

        # Set the exclusive property to True for the button group
        button_group.setExclusive(True)

        # Connect a slot to handle button clicks
        if default_group is False:
            button_group.buttonClicked.connect(lambda button: self.handle_radio_button_click(button_group, button, setting, default_group, default_button, default_variable))
        else:
            button_group.buttonClicked.connect(lambda button: self.handle_radio_button_click(button_group, button, setting, default_group, default_button, default_variable))

    def toggle_edit_mode(self, button, line_edit):
        if line_edit.isReadOnly():
            # Make line edit editable
            line_edit.setReadOnly(False)
            line_edit.setStyleSheet("{ background-color: #ffffff; }")
            button.setText("Save")
        else:
            # Save changes and make line edit read-only
            line_edit.setReadOnly(True)
            line_edit.setStyleSheet("background-color: #f0f0f0; }")
            button.setText("Edit")

            # Check if the line edit contains comma-separated values
            if ',' in line_edit.text():
                # Split the text by commas and create a list
                value_list = [item.strip() for item in line_edit.text().split(',')]
                # Update the JSON with the list
                self.update_json(line_edit.objectName(), value_list)
            else:
                # Update the JSON with the line edit's text
                self.update_json(line_edit.objectName(), line_edit.text())

    def update_json(self, key, value, button=None, default_variable=None):
        # Load JSON data
        with open('settings.json', 'r') as file:
            data = json.load(file)

        if key in data:
            del data[key]
        # If the key is already in the data and its value is a list
        if key in data and isinstance(data[key], list):
            # Update the existing list with the new value
            data[key] = value
        else:
            # Otherwise, simply update the key-value pair
            data[key] = value

        # Write updated JSON data back to the file
        with open('settings.json', 'w') as file:
            json.dump(data, file, indent=4)

        if button is not None:
            button.setEnabled(False)

        default_variable = value


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Create a QPixmap from the image
    pixmap = QPixmap('ui/images/application_icon.png')

    # Create a splash screen with the QPixmap
    splash = QSplashScreen(pixmap)

    # Show the splash screen
    splash.show()

    # Process events to ensure the splash screen is displayed
    app.processEvents()

    # Perform tasks while splash screen is displayed
    widget = FlowLaunch()

    # Hide the splash screen
    splash.finish(widget)

    # Show the main window
    widget.show()

    sys.exit(app.exec_())