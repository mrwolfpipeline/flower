import os
import requests
from datetime import datetime
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

#TODO: dynamically store image paths based on settings. so settings sets the image saving directory
def hide_id_column(table, column_name):
    header = table.horizontalHeader()
    for logical_index in range(header.count()):
        visual_index = header.visualIndex(logical_index)
        if header.model().headerData(visual_index, Qt.Horizontal) == column_name:
            column_id = visual_index

    table.setColumnHidden(column_id, True)

def download_image(url, task_id, save_dir='images'):
    """
    Download an image from the given URL and save it locally.

    Args:
        url (str): The URL of the image to download.
        task_id (str): The unique identifier for the task, used to name the image file.
        save_dir (str): The directory where the image will be saved. Default is 'images'.

    Returns:
        str: The file path of the downloaded image if successful, else None.
    """
    # Create the save directory if it doesn't exist
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    # Extract the file extension from the URL
    file_extension = 'jpg'

    # Construct the file name for the image
    image_filename = f"{task_id}.{file_extension}"

    # Check if the image already exists locally
    local_image_path = os.path.join(save_dir, image_filename)
    if os.path.exists(local_image_path):
        # print(f"Image already exists locally: {local_image_path}")
        return local_image_path

    try:
        # Make a request to download the image
        response = requests.get(url)
        if response.status_code == 200:
            # Save the image locally
            with open(local_image_path, 'wb') as f:
                f.write(response.content)
            # print(f"Image downloaded successfully: {local_image_path}")
            return local_image_path
        else:
            print(f"Failed to download image from URL: {url}")
            return None
    except Exception as e:
        print(f"Error downloading image: {e}")
        return None

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
                        image_path = image

                    else:
                        image_path = download_image(task_field, task[id_field])

                    # Load the image as QPixmap
                    image_pixmap = QPixmap(image_path)

                    # Scale the pixmap to fit within 80x80 while preserving aspect ratio
                    scaled_pixmap = image_pixmap.scaled(QSize(60, 36))

                    # Create a QLabel to display the icon
                    task_table_item = QLabel()
                    task_table_item.setPixmap(scaled_pixmap)
                    task_table_item.setAlignment(Qt.AlignCenter)  # Center the icon within the QLabel

                    table.setCellWidget(row, col, task_table_item)

                # HANDLE TEXT
                elif field_type == 'text' or field_type == 'entity' or field_type == 'str':
                    # Create a QTableWidgetItem
                    # print(field == 'entity.Shot.code')
                    if field == 'entity.Shot.code':
                        if task['entity.type'] == 'Shot':
                            pass
                        elif task['entity.type'] == 'Asset':
                            task_field = task['entity']

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

    hide_id_column(table, id_field)
    # Find the index of the column with the header 'Shot Key ID'
    if table_type == 'Task':
        resize_columns(table)


def resize_columns(table_widget):
    table_widget.setShowGrid(True)
    ignore_column_name = 'Thumbnail'
    # Create a QFontMetrics object to measure text width
    font_metrics = QFontMetrics(table_widget.font())

    # Iterate through each column
    for col in range(table_widget.columnCount()):
        # Check if the current column should be ignored
        header_item = table_widget.horizontalHeaderItem(col)
        if header_item is not None and header_item.text() == ignore_column_name:
            continue

        # Initialize the maximum width to zero
        max_width = 0

        # Measure the header item text width
        if header_item is not None:
            header_text = header_item.text()
            header_text_width = font_metrics.width(header_text)
            max_width = max(max_width, header_text_width)

        # Iterate through each row to find the maximum width of items in the column
        for row in range(table_widget.rowCount()):
            item = table_widget.item(row, col)
            if item is not None:
                text = item.text()
                item.setTextAlignment(Qt.AlignCenter)
                text_width = font_metrics.width(text)
                if text_width > max_width:
                    max_width = text_width

        # Add some padding to the maximum width
        padding = 20
        max_width += padding

        # Set the column width to the maximum width found
        table_widget.setColumnWidth(col, max_width)