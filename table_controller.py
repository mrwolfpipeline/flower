from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

import util_flow
import flow_launch
import table_populator

#TODO: need a method for filtering statuses of tasks
#TODO: method for filtering task types / pipeline steps
#TODO: method for fileting episodes
#TODO: need to be able to display episode field

class TableManager(flow_launch.FlowLaunch):
	def __init__(self, table_tasks, user, table_task_projects, user_tasks, task_field_dict, backend_field_dict, display_field_list):
		self.tableTasks = table_tasks
		self.tableTaskProjects = table_task_projects
		self.display_field_list = display_field_list
		self.selected_project = None
		self.selected_task = None
		self.user_tasks = user_tasks
		self.task_field_dict = task_field_dict
		self.backend_field_list = backend_field_dict
		self.task_info = None
		self.user_name = user

		# ESTABLISH DEFAULT PROJECT COLUMNS AND DATA FIELDS
		self.project_id_field = 'project.Project.id'
		self.project_field_list = ['project.Project.image', 'project.Project.name', 'project.Project.id']
		self.project_field_dict = {
			'project.Project.image': {'data_type': 'image', 'entity_type': 'Project', 'display_name': 'Thumbnail', 'field_name': 'image', 'valid_types': None},
			'project.Project.name': {'data_type': 'text', 'entity_type': 'Project', 'display_name': 'Project Name', 'field_name': 'name', 'valid_types': None},
			'project.Project.id': {'data_type': 'number', 'entity_type': 'Project', 'display_name': 'Project ID', 'field_name': 'id', 'valid_types': None}
		}
		self.project_display_fields = ['Image', "Project Name"]

	def on_header_clicked(self, logicalIndex):
		table = self.sender().parentWidget()
		self.sort_column(table, logicalIndex)

	def table_creator(self):
		self.create_project_table(self.tableTaskProjects)
		self.create_task_table(self.tableTasks)

	def update_task_table(self, task_field_dict, backend_field_list, display_field_list):
		id_column = self.find_column_index(self.tableTasks, 'id')
		self.tableTasks.setColumnHidden(id_column, False)
		self.task_field_dict = task_field_dict
		self.backend_field_list = backend_field_list
		self.display_field_list = display_field_list
		print("UPDATING USER TASKS")
		self.user_tasks = util_flow.get_user_tasks_custom(self.user_name, self.backend_field_list)
		print("DONE UPDATING USER TASKS")
		table_populator.populate_table(self.tableTasks, self.backend_field_list, self.display_field_list,
		                               self.user_tasks, self.selected_project, self.task_field_dict, 'id', filter=None,
		                               table_type='Task')

		id_column = self.find_column_index(self.tableTasks, 'id')
		self.tableTasks.setColumnHidden(id_column, True)
		
	def refresh_data(self, user_tasks, task_field_dict, backend_field_list, display_field_list):
		project_id_columb = self.find_column_index(self.tableTaskProjects, 'project.Project.id')
		self.tableTaskProjects.setColumnHidden(project_id_columb, False)
		
		self.task_field_dict = task_field_dict
		self.backend_field_list = backend_field_list
		self.display_field_list = display_field_list
		self.user_tasks = user_tasks

		# clear task table
		self.tableTasks.setRowCount(0)

		# populate project table
		table_populator.populate_table(
			self.tableTaskProjects, self.project_field_list, self.project_display_fields, self.user_tasks,
			self.selected_project, self.project_field_dict, self.project_id_field, filter=None, table_type='Project'
		)

		# sort project table
		self.sort_table_by_column(self.tableTaskProjects, 1)

	def create_task_table(self, table):
		print('create task table function called and populating task table')
		table.verticalHeader().setVisible(False)
		table.removeRow(0)
		table.setShowGrid(False)
		table.setSelectionBehavior(QAbstractItemView.SelectRows)
		table.setEditTriggers(QAbstractItemView.NoEditTriggers)
		table.verticalHeader().setDefaultSectionSize(80)
		table.cellClicked.connect(lambda row, col: self.on_row_clicked(row, table, 'id'))
		table.horizontalHeader().sectionClicked.connect(self.on_header_clicked)
		table.setAlternatingRowColors(True)

		table_populator.populate_table(
			self.tableTasks, self.backend_field_list, self.display_field_list, self.user_tasks,
			self.selected_project, self.task_field_dict, 'id', filter=None, table_type='Task'
		)

		table.horizontalHeader().setSectionsMovable(True)

		id_column = self.find_column_index(table, 'id')
		table.setColumnHidden(id_column, True)

	def create_project_table(self, table):
		table.removeRow(0)
		table.setShowGrid(False)
		table.setSelectionBehavior(QAbstractItemView.SelectRows)
		table.setEditTriggers(QAbstractItemView.NoEditTriggers)
		table.verticalHeader().setVisible(False)
		table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
		table.verticalHeader().setDefaultSectionSize(80)
		table.setStyleSheet("""
		QTableWidget::item { padding: 5px; }
		QTableWidget::item:selected { padding: 5px; }
		""")

		table_populator.populate_table(
			self.tableTaskProjects, self.project_field_list, self.project_display_fields, self.user_tasks,
			self.selected_project, self.project_field_dict, self.project_id_field, filter=None, table_type='Project'
		)

		table.cellClicked.connect(lambda row, col: self.on_row_clicked(row, table, 'project.Project.id'))
		table.cellClicked.connect(lambda row, col: self.filter_table(table))

		self.sort_table_by_column(table, 1)

		id_column = self.find_column_index(table, 'project.Project.id')
		table.setColumnHidden(id_column, True)

	def on_row_clicked(self, row, table_widget, id_field):
		# Find the column index for the given id_field
		column_index = self.find_column_index(table_widget, id_field)
		if column_index == -1:
			print(f"Column '{id_field}' not found.")
			return

		# Retrieve the item from the specified column in the clicked row
		item = table_widget.item(row, column_index)
		if not item:
			return

		# Update selected project or task based on the table
		item_id = item.data(Qt.DisplayRole)
		if table_widget == self.tableTaskProjects:
			self.selected_project = int(item_id)
			self.selected_task = None
		elif table_widget == self.tableTasks:
			self.selected_task = int(item_id)

		# Perform additional actions after row click
		# TODO: CAN BE DELETED
		self.get_selected_info()

	def sort_table_by_column(self, table, column_index, descending=False):
		table.sortItems(column_index, Qt.DescendingOrder if descending else Qt.AscendingOrder)

	def find_column_index(self, table, column_name):
		header = table.horizontalHeader()
		for logical_index in range(header.count()):
			visual_index = header.visualIndex(logical_index)
			if header.model().headerData(visual_index, Qt.Horizontal) == column_name:
				return visual_index
		return -1

	def sort_column(self, table, logicalIndex):
		order = table.horizontalHeader().sortIndicatorOrder()
		table.sortItems(logicalIndex, order)

	def get_selected_item_id(self, table, id_column):
		selected_items = table.selectedItems()
		if selected_items:
			id_column_index = self.find_column_index(table, id_column)
			selected_item = selected_items[0]
			id_item = table.item(selected_item.row(), id_column_index)
			if id_item:
				return id_item.text()
		return None

	def filter_table(self, table):
		print('filter table function called and populated table')
		self.selected_project = int(self.get_selected_item_id(table, 'project.Project.id'))
		if self.selected_project is not None:
			self.tableTasks.clearContents()
			self.tableTasks.setRowCount(0)
			table_populator.populate_table(
				self.tableTasks, self.backend_field_list, self.display_field_list,
				self.user_tasks, self.selected_project, self.task_field_dict, 'id',
				filter='Project', table_type='Task'
			)

	def get_selected_info(self):
		print(f"Selected Project: {self.selected_project}")
		print(f"Selected Task: {self.selected_task}")

		self.task_info = {
			'project_id': self.selected_project,
			'project_folder': None,
			'shot_name': None,
			'shot_id': None,
			'task_name': None,
			'pipeline_step': None,
			'sequence': None,
			'episode': None
		}

		for task in self.user_tasks:
			# Get project info from the selected project id
			if task.get('project.Project.id') == self.selected_project:
				self.task_info['project_folder'] = task.get('project.Project.sg_project_folder')

			# Get task info from selected task id (if selected)
			if task.get('id') == self.selected_task:
				self.task_info.update({
					'shot_name': task.get('entity.Shot.code'),
					'shot_id': task.get('entity.Shot.id'),
					'task_name': task.get('content'),
					'pipeline_step': task.get('step'),
					'sequence': task.get('entity.Shot.sg_sequence.name'),
					'episode': task.get('entity.Shot.sg_sequence.Sequence.episode.name')
				})
				break  # Exit loop once the task is found

		# Print the task information dictionary
		for key, value in self.task_info.items():
			print(f"{key.replace('_', ' ').title()}: {value}")

		return self.task_info

		# return task_info, system_path



