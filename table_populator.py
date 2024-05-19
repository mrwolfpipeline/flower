import requests
from datetime import datetime
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

def populate_table(table, fields_list, display_field_list, user_tasks, selected_project, ref_field_dict, id_field, filter=None, table_type=None):
    header_labels = [field.split('.')[-1] for field in display_field_list]
    header_labels.append(id_field)
    fields_list.append(id_field)

    # TABLE CLEAR
    table.setRowCount(0)
    table.setColumnCount(len(header_labels))
    table.setHorizontalHeaderLabels(header_labels)

    row = 0
    col = 0
    added_ids = set()  # To keep track of already added project IDs

    if table_type == 'Project':
        # If the table is for projects, don't filter tasks
        filtered_tasks = user_tasks.copy()
        filtered_tasks.append({'project.Project.name': '[.ALL PROJECTS.]', 'project.Project.id': 0, 'project.Project.image': None})

    else:
        # Filter tasks based on the selected project ID
        if selected_project == 0:
            filtered_tasks = user_tasks

        else:
            filtered_tasks = [task for task in user_tasks if task.get('project.Project.id') == selected_project]


    for task in filtered_tasks:
        if task[id_field] in added_ids:
            continue

        else:
            table.insertRow(row)
            added_ids.add(task[id_field])
            for field in fields_list:
                task_field = task[field]

                # TODO: possibly better way to handle this. maybe passing the dict into the function
                if table_type is not None:
                    field_type = ref_field_dict.get(field).get('data_type')

                else:
                    field_type = type(task_field)

                # HANDLE IMAGE
                if field_type == 'image':
                    if task_field is None:
                        # Default shot image path goes here
                        image = 'ui/images/missing_image.png'
                        # Load default application image
                        image_pixmap = QPixmap(image)

                    else:
                        response = requests.get(task_field)
                        image_data = response.content
                        # Create a QPixmap from the image data
                        image_pixmap = QPixmap()
                        image_pixmap.loadFromData(image_data)

                    # Scale the pixmap to fit within 80x80 while preserving aspect ratio
                    if table_type == 'Task':
                        scaled_pixmap = image_pixmap.scaled(QSize(60, 36))
                    else:
                        scaled_pixmap = image_pixmap.scaled(QSize(60, 36))

                    # Create a QLabel to display the icon
                    task_table_item = QLabel()
                    task_table_item.setPixmap(scaled_pixmap)
                    task_table_item.setAlignment(Qt.AlignCenter)  # Center the icon within the QLabel

                    table.setCellWidget(row, col, task_table_item)

                # HANDLE TEXT
                elif field_type == 'text' or field_type == 'entity' or field_type == 'str':
                    # Create a QTableWidgetItem
                    task_table_item = QTableWidgetItem(task_field)
                    table.setItem(row, col, task_table_item)

                # HANDLE NUMBER
                elif field_type == 'number' or field_type == 'int':
                    task_field = str(task_field)
                    task_table_item = QTableWidgetItem(task_field)
                    table.setItem(row, col, task_table_item)

                # HANDLE DATE
                elif field_type == 'date':
                    if task_field is None:
                        task_field = ""

                    else:
                        # Convert string to datetime object
                        date_obj = datetime.strptime(task_field, "%Y-%m-%d")

                        # Format the datetime object
                        formatted_date = date_obj.strftime("%a %b %d")

                        task_field = str(formatted_date)

                    task_table_item = QTableWidgetItem(task_field)
                    table.setItem(row, col, task_table_item)

                elif field_type == 'date_time':
                    if task_field is None:
                        task_field = ""

                    else:
                        # Format the date and time
                        formatted_date_time = task_field.strftime('%a %b %d')

                        # Manually handle leading zero removal
                        if formatted_date_time[8] == '0':
                            formatted_date_time = formatted_date_time[:8] + formatted_date_time[9:]
                        if formatted_date_time[-5] == '0':
                            formatted_date_time = formatted_date_time[:-5] + formatted_date_time[-4:]

                        task_field = formatted_date_time

                    task_field = str(task_field)
                    task_table_item = QTableWidgetItem(task_field)
                    table.setItem(row, col, task_table_item)

                # TODO: add lookup for status display name
                elif field_type == 'status_list':
                    if task_field is not None:
                        task_field = ref_field_dict.get(field).get('display_values').get(task_field)

                    task_field = str(task_field)
                    task_table_item = QTableWidgetItem(task_field)
                    table.setItem(row, col, task_table_item)

                col += 1
            col = 0
            row += 1

