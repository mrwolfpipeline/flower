import json
import sys
import requests
from PySide2.QtCore import QSize
from PySide2.QtGui import QPixmap, QIcon, QFont
from PySide2.QtWidgets import (
    QApplication, QWidget, QButtonGroup, QPushButton, QTableWidgetItem,
    QLabel, QSplashScreen, QHeaderView, QAbstractItemView
)
from auto_load_ui import autoloadUi  # Import the autoloadUi function
from flow_launch_stylesheet import radio_button_style
import util_flow
import util_globals as FL

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
from datetime import datetime
from ui_checkable_combobox import checkablecombobox

settings_json = 'settings.json'

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
        self.init_ui()

    def init_ui(self):
        # Load the UI file using autoloadUi
        self.ui = autoloadUi(self, customWidgets=[checkablecombobox])

        # Authenticate User
        FL.sg = util_flow.get_sg_connection()
        self.user_object = util_flow.get_sg_user_object()
        self.user_name = str(self.user_object)
        self.user_details = util_flow.get_user_details(self.user_name)
        self.user_tasks = util_flow.get_user_tasks(self.user_name)

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

        # Filter button groups for button creation on tasks and folders views
        # self.tasks_filter_button_group = []
        # self.folders_shots_filter_button_group = []
        # self.folders_tasks_filter_button_group = []

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

            # Creates the filter button groups for the tasks view and the folders view
            # self.create_filter_button_group(data["settingTaskTaskStatuses"], self.tasksFilterBar, self.tasks_filter_button_group)
            # self.create_filter_button_group(data["settingFolderShotStatuses"], self.foldersShotsFilterBar,
            #                                 self.folders_shots_filter_button_group)
            # self.create_filter_button_group(data["settingFolderTaskStatuses"], self.foldersTasksFilterBar,
            #                                 self.folders_tasks_filter_button_group)

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

        # Define a dictionary mapping buttons to their corresponding settings
        button_setting_dict = {
            self.buttonDefaultProject: self.settingDefaultProject,
            self.buttonTaskTaskStatuses: self.settingTaskTaskStatuses,
            self.buttonFolderShotStatuses: self.settingFolderShotStatuses,
            self.buttonFolderTaskStatuses: self.settingFolderTaskStatuses,
            self.buttonMacServerPath: self.settingMacServerPath,
            self.buttonPCServerPath: self.settingPCServerPath,
            self.buttonPythonLibraries: self.settingPythonLibraries,
            self.buttonNukeFolder: self.settingNukeFolder,
            self.buttonNukeInit: self.settingNukeInit,
            self.buttonNukeMenu: self.settingNukeMenu,
            self.buttonMayaFolder: self.settingMayaFolder,
            self.buttonBlenderFolder: self.settingBlenderFolder,
            self.buttonHoudiniFolder: self.settingHoudiniFolder,
            self.buttonSyntheyesFolder: self.settingSyntheyesFolder
        }

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

        self.create_project_list()
        self.create_task_list()

        # Setup taskFilterComboBox
        self.setupFilterComboBox("Task Task Status", self.taskFilterComboBox, data["settingTaskTaskStatuses"])

        # Setup foldersShotStatusFilter
        self.setupFilterComboBox("Folder Shot Status", self.foldersShotStatusFilter, data["settingFolderShotStatuses"])

        # Setup foldersTaskStatusFilter
        self.setupFilterComboBox("Folder Task Status", self.foldersTaskStatusFilter, data["settingFolderTaskStatuses"])

        # for status in data["settingTaskTaskStatuses"]:
        # self.taskFilterComboBox.addItems(data["settingTaskTaskStatuses"])
        # self.foldersShotStatusFilter.addItems(data["settingFolderShotStatuses"])
        # self.foldersTaskStatusFilter.addItems(data["settingFolderTaskStatuses"])
        #
        # # Find the length of the longest item
        # widest_item_length = max(len(self.taskFilterComboBox.model().item(i).text()) for i in
        #                          range(self.taskFilterComboBox.model().rowCount()))
        #
        # # Calculate the width based on the length of the longest item
        # # Adjust the width_factor as needed for additional spacing
        # width_factor = 10  # Adjust this value as needed
        # combo_box_width = widest_item_length * width_factor
        #
        # # Set the width of the combo box
        # self.taskFilterComboBox.setFixedWidth(combo_box_width)
        #
        # self.taskFilterComboBox.selectionChanged.connect(self.handleSelectionChanged)

    def setupFilterComboBox(self, type, combo_box, data):
        combo_box.addItems(data)
        combo_box.filter_type = type

        # Find the length of the longest item
        widest_item_length = max(len(combo_box.model().item(i).text()) for i in range(combo_box.model().rowCount()))

        # Calculate the width based on the length of the longest item
        # Adjust the width_factor as needed for additional spacing
        width_factor = 10  # Adjust this value as needed
        combo_box_width = widest_item_length * width_factor

        # Set the width of the combo box
        combo_box.setFixedWidth(combo_box_width)

        combo_box.selectionChanged.connect(self.handleSelectionChanged)

    def handleSelectionChanged(self, filter, selected, deselected):
        print("Outputting filters")
        print("Filter Type: ", filter)
        print("Selected items:", selected)
        print("Deselected items:", deselected)


    def find_column_index(self, table_widget, column_name):
        header = table_widget.horizontalHeader()
        for logical_index in range(header.count()):
            visual_index = header.visualIndex(logical_index)
            if header.model().headerData(visual_index, Qt.Horizontal) == column_name:
                return visual_index
        return -1  # Return -1 if the column name is not found

    def adjust_image_sizes(self, logical_index, old_size, new_size):
        print("CALLING IMAGE SIZE ADJUSTMENT")
        # Iterate over all rows to adjust the image sizes
        for row in range(self.tableTasks.rowCount()):
            # Get the QTableWidgetItem containing the image
            item = self.ui.tableTaskProjects.item(row, 0)  # Adjust column_index as needed
            if item is not None:
                pixmap = item.pixmap()
                if pixmap is not None:
                    # Calculate new image width and height based on the new column width
                    new_image_width = new_size
                    new_image_height = int(new_image_width * (3 / 2))  # Maintain 2:3 ratio of height to width

                    # Scale the pixmap to the new size
                    scaled_pixmap = pixmap.scaled(new_image_width, new_image_height, Qt.KeepAspectRatio)

                    # Set the new pixmap and adjust the row height
                    item.setIcon(QIcon(scaled_pixmap))
                    self.ui.tableTaskProjects.setRowHeight(row,
                                                           new_image_height + 10)  # Add some extra padding if needed

    def create_task_list(self):
        self.tableTasks.verticalHeader().setVisible(False)
        # self.tableTasks.horizontalHeader().setVisible(False)

        self.tableTasks.removeRow(0)
        self.tableTasks.setShowGrid(False)

        # Hide ID column
        id_column = self.find_column_index(self.tableTasks, 'id')
        self.tableTasks.setColumnHidden(id_column, True)

        self.tableTasks.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tableTasks.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tableTasks.verticalHeader().setVisible(False)

        self.tableTasks.verticalHeader().setDefaultSectionSize(80)

        self.tableTasks.cellClicked.connect(lambda row, col: self.on_row_clicked(row, self.tableTasks))

        # Function to handle sorting by the header column clicked. Can be added to other tables.
        self.tableTasks.horizontalHeader().sectionClicked.connect(self.on_header_clicked)

        self.tableTasks.setAlternatingRowColors(True)

        # TODO: maybe dynamically resize images, rows, columns height based on image size
        # TODO: add settings for which fields are displayed and make it so you can add whichever field you want from sg
        # TODO: figure out method for displaying columns based on settings, getting fields from sg, displaying those fields as columpns and then populating the data
        # TODO: figure out filtering methods for tasks

        # Set the row height for all rows
        self.ui.tableTaskProjects.verticalHeader().setDefaultSectionSize(60)

        row = 0
        added_task_ids = set()  # To keep track of already added project IDs
        for task in self.user_tasks:
            task_id = task['id']
            if task_id in added_task_ids:
                continue

            added_task_ids.add(task_id)

            shot_image = task['entity.Shot.image']
            shot_name = task['entity'].get('name')
            shot_episode = task['entity.Shot.sg_sequence.Sequence.episode']
            task_name = task['content']
            task_type = task['step'].get('name')
            task_bid_mins = task['est_in_mins']

            # Convert bid mids to hours
            if task_bid_mins is not None:
                task_bid_hours = task_bid_mins/60

            else:
                task_bid_hours = 0

            # Convert logged mins to hours
            task_logged_mins = task['time_logs_sum']

            if task_logged_mins is not None:
                task_logged_hours = task_logged_mins/60

            else:
                task_logged_hours = 0

            task_due_date = task['due_date']
            task_last_worked = task['sg_last_opened_in_launcher']

            if task_last_worked is not None:
                # Format the datetime object as "Sun May 12 12:00AM"
                task_last_worked = task_last_worked.strftime("%a %b %d %I:%M%p")
            else:
                task_last_worked = ''

            if task_bid_hours != 0:
                task_logged_vs_bid = round(task_logged_hours/task_bid_hours * 100)
                task_logged_vs_bid_percent = (f"{task_logged_vs_bid}%")

            else:
                task_logged_vs_bid_percent = 0

            # Convert string to datetime object
            task_due_date_object = datetime.strptime(task_due_date, "%Y-%m-%d")

            # Format the datetime object as "Sun May 12" format
            task_due_date = task_due_date_object.strftime("%a %b %d")

            # Convert variables to table items
            shot_name_item = QTableWidgetItem(shot_name)
            shot_episode_item = QTableWidgetItem(str(shot_episode))
            task_name_item = QTableWidgetItem(task_name)
            task_type_item = QTableWidgetItem(task_type)
            task_due_item = QTableWidgetItem(task_due_date)
            task_bid_hours_item = QTableWidgetItem(str(task_bid_hours))
            task_logged_hours_item = QTableWidgetItem(str(task_logged_hours))
            task_logged_vs_bid_item = QTableWidgetItem(str(task_logged_vs_bid_percent))
            task_last_worked_item = QTableWidgetItem(str(task_last_worked))
            task_id = QTableWidgetItem(str(task_id))

            # Download the image
            if shot_image is None:
                # Default shot image path goes here
                shot_image = 'ui/images/missing_image.png'
                # Load default application image
                task_pixmap = QPixmap(shot_image)

            else:
                response = requests.get(shot_image)
                image_data = response.content
                # Create a QPixmap from the image data
                task_pixmap = QPixmap()
                task_pixmap.loadFromData(image_data)

            # Scale the pixmap to fit within 80x80 while preserving aspect ratio
            scaled_pixmap = task_pixmap.scaled(QSize(80, 50))

            # Create a QLabel to display the icon
            icon_label = QLabel()
            icon_label.setPixmap(scaled_pixmap)
            icon_label.setAlignment(Qt.AlignCenter)  # Center the icon within the QLabel

            # Insert a new row and set the items
            self.tableTasks.insertRow(row)
            self.tableTasks.setCellWidget(row, 0, icon_label)

            self.tableTasks.setItem(row, 1, shot_name_item)
            self.tableTasks.setItem(row, 2, task_name_item)
            self.tableTasks.setItem(row, 3, task_due_item)
            self.tableTasks.setItem(row, 4, task_bid_hours_item)
            self.tableTasks.setItem(row, 5, task_logged_hours_item)
            self.tableTasks.setItem(row, 6, task_logged_vs_bid_item)
            self.tableTasks.setItem(row, 7, task_last_worked_item)


            self.tableTasks.setItem(row, id_column, task_id)

    def on_header_clicked(self, logicalIndex):
        # Retrieve the table header view that emitted the signal
        header_view = self.sender()
        # Retrieve the table widget associated with the header view
        table_widget = header_view.parentWidget()
        # Sort the table by the clicked column
        self.sort_column(table_widget, logicalIndex)

    def sort_column(self, table, logicalIndex):
        order = table.horizontalHeader().sortIndicatorOrder()
        table.sortItems(logicalIndex, order)

    def on_row_clicked(self, row, table_widget):
        # Get the column index of the column named "id"
        column_index = -1
        for column in range(table_widget.columnCount()):
            if table_widget.horizontalHeaderItem(column).text() == "id":
                column_index = column
                break

        if column_index == -1:
            print("Column 'id' not found.")
            return

        # Get the project ID from the clicked row and column
        project_id_item = table_widget.item(row, column_index)
        if project_id_item:
            project_id = project_id_item.data(Qt.DisplayRole)
            print("Selected ID:", project_id)

    def sort_table_by_column(self, table, column_index, descending=False):
        # Sort the table by the specified column index
        table.sortItems(column_index, Qt.DescendingOrder if descending else Qt.AscendingOrder)

    def create_project_list(self):
        # Remove the first row from the QT Designer file using for testing
        self.tableTaskProjects.removeRow(0)
        self.tableTaskProjects.setShowGrid(False)

        # Hide ID column
        id_column = self.find_column_index(self.tableTaskProjects, 'id')
        self.tableTaskProjects.setColumnHidden(id_column, True)

        self.tableTaskProjects.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tableTaskProjects.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.tableTaskProjects.verticalHeader().setVisible(False)
        self.tableTaskProjects.horizontalHeader().setVisible(False)

        # Set the resize mode of the second column to stretch
        self.tableTaskProjects.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)

        self.tableTaskProjects.verticalHeader().setDefaultSectionSize(80)
        self.tableTaskProjects.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tableTaskProjects.setStyleSheet("""
            QTableWidget::item { 
                padding: 5px;  /* padding for unselected items */
            }
            QTableWidget::item:selected { 
                padding: 5px;  /* padding for selected items */
            }
        """)

        # Connect the cellClicked signal to the custom slot
        self.tableTaskProjects.cellClicked.connect(lambda row, col: self.on_row_clicked(row, self.tableTaskProjects))

        row = 0
        added_project_ids = set()  # To keep track of already added project IDs
        for task in self.user_tasks:
            project_name = task['project.Project.name']
            project_image = task['project.Project.image']
            project_id = task['project.Project.id']

            # Check if the project ID is already added, skip if it's a duplicate
            if project_id in added_project_ids:
                continue

            # Add the project ID to the set of added project IDs
            added_project_ids.add(project_id)

            if project_image is None:
                # Default shot image path goes here
                shot_image = 'ui/images/missing_image.png'
                # Load default application image
                project_pixmap = QPixmap(project_image)

            else:
                response = requests.get(project_image)
                image_data = response.content
                # Create a QPixmap from the image data
                project_pixmap = QPixmap()
                project_pixmap.loadFromData(image_data)

            # Scale the pixmap to fit within 80x80 while preserving aspect ratio
            scaled_pixmap = project_pixmap.scaled(QSize(100, 60))

            # Create a QLabel to display the icon
            icon_label = QLabel()
            icon_label.setPixmap(scaled_pixmap)
            icon_label.setAlignment(Qt.AlignCenter)  # Center the icon within the QLabel

            # Insert a new row and set the items
            self.tableTaskProjects.insertRow(row)
            self.tableTaskProjects.setCellWidget(row, 0, icon_label)

            # Create a QTableWidgetItem for project name
            project_name_item = QTableWidgetItem(project_name)

            # Set left margin padding for the project name using style sheet
            project_name_item.setTextAlignment(
                Qt.AlignVCenter | Qt.AlignLeft)  # Horizontally to the left, vertically centered
            font = QFont()
            font.setPointSize(9)
            project_name_item.setFont(font)

            self.tableTaskProjects.setItem(row, 1, project_name_item)

            # Create a QTableWidgetItem for project id (invisible column)
            project_id_item = QTableWidgetItem()
            project_id_item.setData(Qt.DisplayRole, project_id)
            project_id_item.setFlags(Qt.ItemIsEnabled)  # Disable editing and selection
            self.tableTaskProjects.setItem(row, 2, project_id_item)

            # Increment row counter
            row += 1

        self.sort_table_by_column(self.tableTaskProjects, 1)

    # def create_filter_button_group(self, status_list, filter_bar_layout, filter_button_group):
    #     # Iterate over the list of task statuses and create buttons
    #     for status in status_list:
    #         button = QPushButton(status, self)
    #         button.setStyleSheet(radio_button_style)
    #         button.setCheckable(True)
    #         button.setMinimumWidth(80)
    #         button.setMinimumHeight(30)
    #         filter_button_group.append(button)
    #         button.setChecked(True)
    #         button.clicked.connect(lambda: self.filter_button_click(filter_button_group))
    #
    #         filter_bar_layout.addWidget(button)

    # def filter_button_click(self, button_group):
    #     # Print the status of all buttons in the group
    #     status = [f"{btn.text()} is {'checked' if btn.isChecked() else 'unchecked'}" for btn in button_group]
    #     print(", ".join(status))

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

        # Update JSON data with the new key-value pair
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