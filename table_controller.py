from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

import util_flow
import flow_launch
import table_populator


class TableManager:
	def __init__(self, table_tasks, table_task_projects, user_tasks, task_field_dict, backend_field_dict,
	             display_field_list):
		self.tableTasks = table_tasks
		self.tableTaskProjects = table_task_projects
		self.display_field_list = display_field_list
		self.selected_project = None
		self.user_tasks = user_tasks
		self.task_field_dict = task_field_dict
		self.backend_field_list = backend_field_dict

	def on_header_clicked(self, logicalIndex):
		table = self.sender().parentWidget()
		self.sort_column(table, logicalIndex)

	def table_creator(self):
		self.create_project_table(self.tableTaskProjects)
		self.create_task_table(self.tableTasks)

	def update_task_table(self, display_field_list):
		self.display_field_list = display_field_list
		table_populator.populate_table(self.tableTasks, self.backend_field_list, self.display_field_list,
		                               self.user_tasks,
		                               self.selected_project, self.task_field_dict, 'id', filter=None,
		                               table_type='Task')

	def create_task_table(self, table):
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

		id_field = 'project.Project.id'
		fields_list = ['project.Project.image', 'project.Project.name', 'project.Project.id']
		project_field_dict = {
			'project.Project.image': {'data_type': 'image', 'entity_type': 'Project', 'display_name': 'Thumbnail',
			                          'field_name': 'image', 'valid_types': None},
			'project.Project.name': {'data_type': 'text', 'entity_type': 'Project', 'display_name': 'Project Name',
			                         'field_name': 'name', 'valid_types': None},
			'project.Project.id': {'data_type': 'number', 'entity_type': 'Project', 'display_name': 'Project ID',
			                       'field_name': 'id', 'valid_types': None}
		}
		display_fields_list = ['Image', "Project Name"]

		table_populator.populate_table(
			self.tableTaskProjects, fields_list, display_fields_list, self.user_tasks,
			self.selected_project, project_field_dict, id_field, filter=None, table_type='Project'
		)

		table.cellClicked.connect(lambda row, col: self.on_row_clicked(row, table, 'project.Project.id'))
		table.cellClicked.connect(lambda row, col: self.filter_table(table))
		self.sort_table_by_column(table, 1)

		id_column = self.find_column_index(table, 'project.Project.id')
		table.setColumnHidden(id_column, True)

	def on_row_clicked(self, row, table_widget, id_field):
		column_index = self.find_column_index(table_widget, id_field)
		if column_index == -1:
			print("Column 'id' not found.")
			return
		project_id_item = table_widget.item(row, column_index)
		if project_id_item:
			project_id = project_id_item.data(Qt.DisplayRole)
			self.selected_project = project_id

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
		self.selected_project = self.get_selected_item_id(table, 'project.Project.id')
		if self.selected_project is not None:
			self.tableTasks.clearContents()
			self.tableTasks.setRowCount(0)
			table_populator.populate_table(
				self.tableTasks, self.backend_field_list, self.display_field_list,
				self.user_tasks, self.selected_project, self.task_field_dict, 'id',
				filter='Project', table_type='Task'
			)
