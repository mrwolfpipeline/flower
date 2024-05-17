from shotgun_api3 import Shotgun, AuthenticationFault
from tank.authentication import ShotgunAuthenticator
import util_globals as FL

def get_sg_connection():
    """
    Create a Shotgun connection via the user object
    This will initialize globals as well.
    Use at the start of a hook script.
    """
    Shotgun.NO_SSL_VALIDATION = True
    sa = ShotgunAuthenticator()

    # THIS LOGIN METHOD LOOKS TO SEE IF A USER IS LOGGED IN AND IF NOT CLOSES OUT OF NUKE BY RETURNING NONE
    user = sa.get_default_user()

    # ENABLE THESE TWO LINES TO ADD USER AUTHENTICATION LINKED BY PERSONAL ACCESS TOKEN
    # user = sa.get_user()
    # sg = user.create_sg_connection()

    if user:
        # todo: this can error out!
        sg = user.create_sg_connection()

        FL.sg = sg
        FL.sg_user_object = user.login
        return sg
    else:
        print("ERROR")
        print('No ShotGrid User found...Please log in using SG Desktop.')

    return None

def get_sg_user_object():
    """
    Get the current Shotgun user
    """
    # print("GETTING SG USER")
    sa = ShotgunAuthenticator()
    user = sa.get_default_user()
    if user:
        # print('SG User: ' + str(user))
        FL.user_object = user.login
        FL.user_name = str(user.login)
        return user
    else:
        print("Can't find SG User!")
        return None

def get_user_details(user):
    sg = FL.sg
    user_fields = ['id', 'login', 'email', 'name', 'phone', 'permission_rule_set']
    user_data = sg.find_one('HumanUser', [['login', 'is', user]], fields=user_fields)

    FL.user_id = user_data['id']
    FL.user_login = user_data['login']
    FL.user_email = user_data['email']
    FL.user_permission_group = user_data['permission_rule_set'].get("name")

    return user_data

def get_user_tasks(user):
    sg = FL.sg
    
    # Find the user based on the login
    filters = [["task_assignees.HumanUser.login", "is", user]]
    result_format = ['content',
                     'entity',
                     'entity.Shot.image',
                     'sg_status_list',
                     'sg_version',
                     'step.Step.code',
                     'step',
                     'id',
                     'project.Project.name',
                     'entity.project.Project',
                     'project.Project.id',
                     'entity.Shot.sg_sequence.Sequence.episode',
                     'project.Project.sg_mw_shot_regex',
                     'project.Project.image',
                     'est_in_mins',
                     'time_logs_sum',
                     'due_date',
                     'sg_last_opened_in_launcher']

    tasks = sg.find('Task', filters, result_format, include_archived_projects=False)

    tasks = extract_names_from_tasks(tasks)

    return tasks

def extract_names_from_tasks(data):
    if isinstance(data, list):
        return [extract_names_from_tasks(item) for item in data]
    elif isinstance(data, dict):
        new_data = {}
        for key, value in data.items():
            if isinstance(value, dict) and 'name' in value:
                new_data[key] = value['name']
            else:
                new_data[key] = extract_names_from_tasks(value)
        return new_data
    else:
        return data

def get_user_tasks_custom(user, fields_to_get):
    sg = FL.sg

    # Find the user based on the login
    filters = [["task_assignees.HumanUser.login", "is", user]]
    # Set default fields to get
    result_format = ['content', 'entity', 'step', 'id', 'project.Project.id', 'entity.Shot.id']
    result_format.extend(fields_to_get)

    tasks = sg.find('Task', filters, result_format, include_archived_projects=False)

    tasks = extract_names_from_tasks(tasks)

    print("USER TASKS CUSTOM")
    print(tasks)

    return tasks

def get_status_list(entity_type):
    try:
        # Create a Shotgun API connection
        sg = FL.sg

        # Retrieve the schema for the specified entity type
        schema = sg.schema_field_read(entity_type)

        print("SCHEMA")
        print(schema)

        # Get the list of possible statuses from the schema
        statuses = schema[entity_type]['properties']['sg_status_list']['properties']['valid_values']['value']
        return statuses
    except KeyError:
        print("Error: Entity type '{}' not found in the Shotgun schema.".format(entity_type))
        return []


def get_field_display_names(entity_type, field_names):
    # Retrieve the schema for the entity type
    schema = FL.sg.schema_field_read(entity_type)

    field_info = {}
    # Iterate over the specified field names
    for field_name in field_names:
        # Check if the field exists in the schema
        if field_name in schema:
            # Retrieve the display name of the field
            display_name = schema[field_name]['name']
            field_info[field_name] = (field_name, display_name)
        else:
            field_info[field_name] = (field_name, None)  # Field not found in schema

    return field_info

# Gets just field names
def get_all_field_names(entity_type):
    # Retrieve the schema for the specified entity type
    schema = FL.sg.schema_field_read(entity_type)

    # Extract field names from the schema
    field_names = list(schema.keys())

    return field_names

# Gets field names with display names
def get_field_names_with_display_names(entity_type):
    # Retrieve the schema for the specified entity type
    schema = FL.sg.schema_field_read(entity_type)

    # Extract field names and display names from the schema
    field_info = {}
    for field_name, info in schema.items():
        if 'name' in info:
            field_info[info['name']['value']] = field_name
        else:
            field_info[field_name] = field_name  # Use field name as display name if 'label' is missing

    # print("OLD INFO")
    # print(field_info)

    return field_info

def get_all_field_info(entity_type):
    # Retrieve the schema for the specified entity type
    schema = FL.sg.schema_field_read(entity_type)

    # Create a dictionary to store field info
    field_info = {}

    print("SCHEMA")
    print(schema)

    # Iterate over each field in the schema
    for field_name, field_data in schema.items():
        # Extract field type and display name
        data_type = field_data['data_type']['value']
        entity_type = field_data['entity_type']['value']
        display_name = field_data['name']['value']

        if data_type == 'status_list':
            print(field_data)
        display_values = field_data.get('display_values', {}).get('value', {})

        # Check if 'valid_types' exists before accessing it
        if 'properties' in field_data and 'valid_types' in field_data['properties'] and \
                field_data['properties']['valid_types']['value']:
            valid_type = field_data['properties']['valid_types']['value'][0]
        else:
            valid_type = None  # or any default value you prefer

        # Store field info in the dictionary
        field_info[display_name] = {
            'data_type': data_type,
            'entity_type': entity_type,
            'display_name': display_name,
            'field_name': field_name,
            'valid_types': valid_type,
            'display_values': display_values
        }

    return field_info

def get_entity_info():
    # Get all entity types
    entities = ['Task', 'Shot', 'Sequence', 'Asset', 'Project', 'Episode', 'Version']

    entity_dict = {}

    for entity in entities:
        field_info = get_all_field_info(entity)

        entity_dict[entity] = field_info

    print(entity_dict)

    return entity_dict

if __name__ == "__main__":
    sg = get_sg_connection()
    user = get_sg_user_object()
    user = str(user)


    tasks = get_user_tasks(user)
    # print(tasks)

