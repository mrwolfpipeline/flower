from shotgun_api3 import Shotgun, AuthenticationFault
from tank.authentication import ShotgunAuthenticator
import util_globals as FL

def get_sg_connection():
    """
    Create a Shotgun connection via the user object
    This will initialize globals as well.
    Use at the start of a hook script.
    """
    print("GETTING SG CONNECTION")
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

def get_user_details(user):
    print("GETTING USER DETAILS")
    sg = FL.sg
    user_fields = ['id', 'login', 'email', 'name', 'phone', 'permission_rule_set']
    user_data = sg.find_one('HumanUser', [['login', 'is', user]], fields=user_fields)

    FL.user_id = user_data['id']
    FL.user_login = user_data['login']
    FL.user_email = user_data['email']
    FL.user_permission_group = user_data['permission_rule_set'].get("name")

    return user_data

def get_user_tasks(user, add_fields=None):
    print("GETTING USER TASKS")
    sg = FL.sg
    
    # Find the user based on the login
    filters = [["task_assignees.HumanUser.login", "is", user]]
    result_format = ['content',
                     'entity']
    if add_fields:
        result_format.extend(add_fields)
    # result_format = ['content',
    #                  'entity',
    #                  'entity.Shot.image',
    #                  'sg_status_list',
    #                  'sg_version',
    #                  'step.Step.code',
    #                  'step',
    #                  'id',
    #                  'project.Project.name',
    #                  'entity.project.Project',
    #                  'project.Project.id',
    #                  'entity.Shot.sg_sequence.Sequence.episode',
    #                  'project.Project.sg_mw_shot_regex',
    #                  'project.Project.image',
    #                  'est_in_mins',
    #                  'time_logs_sum',
    #                  'due_date',
    #                  'sg_last_opened_in_launcher']

    tasks = sg.find('Task', filters, result_format, include_archived_projects=False)

    tasks = extract_names_from_tasks(tasks)

    return tasks

def get_pipeline_step_data():
    sg = FL.sg
    entity_type = "Step"
    field_names = ["short_name", "code"]  # Assuming you want to retrieve the "short_name" and "code" fields

    # Query Shotgun for all Step records
    steps = sg.find(entity_type, [], field_names)

    print(steps)

    return steps

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
    result_format = ['content', 'entity', 'step', 'id', 'project.Project.id', 'entity.Shot.id', 'project.Project.image', 'project.Project.name']
    result_format.extend(fields_to_get)

    tasks = sg.find('Task', filters, result_format, include_archived_projects=False)

    tasks = extract_names_from_tasks(tasks)

    return tasks

def get_status_list(entity_type):
    try:
        # Create a Shotgun API connection
        sg = FL.sg

        # Retrieve the schema for the specified entity type
        schema = sg.schema_field_read(entity_type)

        # Get the list of possible statuses from the schema
        statuses = schema[entity_type]['properties']['sg_status_list']['properties']['valid_values']['value']
        return statuses
    except KeyError:
        print("Error: Entity type '{}' not found in the Shotgun schema.".format(entity_type))
        return []

# THIS NEEDS TO MATCH THE DISPLAY TO FIELD NAME CONVERTER IN FLOW LAUNCH
# TODO: BETTER WAY TO HANDLE THIS BASED ON FIELD NAMES?
def build_task_relationship_field_name(entity, field_name, data_type):
    mapped_name = None

    if entity == 'Task':
        mapped_name = field_name

    elif entity == 'Project':
        mapped_name = 'project.Project.' + field_name

    elif entity =='Episode':
        mapped_name = 'entity.Shot.sg_sequence.Sequence.episode.name'

    else:
        if data_type == 'entity':
            mapped_name = 'entity.' + str(entity) + '.' + field_name + '.' + 'name'

        else:
            mapped_name = 'entity.' + str(entity) + '.' + str(field_name)


    # if entity == 'Episode':
    #     print(mapped_name)

    # if mapped_name is None:
    #     print(entity)
    #     print(field_name)
    #     print(data_type)

    return mapped_name

def get_all_field_info(entity_type):
    # Retrieve the schema for the specified entity type
    schema = FL.sg.schema_field_read(entity_type)

    # Create a dictionary to store field info
    field_info = {}
    all_mapped_fields = []

    # Iterate over each field in the schema
    for field_name, field_data in schema.items():
        # Extract field type and display name
        data_type = field_data['data_type']['value']
        entity_type = field_data['entity_type']['value']
        display_name = field_data['name']['value'] if 'name' in field_data else field_name

        # Extract display values if they exist
        if 'properties' in field_data and 'display_values' in field_data['properties'] and 'value' in field_data['properties']['display_values']:
            display_values = field_data['properties']['display_values']['value']
        else:
            display_values = None

        # Extract valid types if they exist
        if 'properties' in field_data and 'valid_types' in field_data['properties'] and field_data['properties']['valid_types']['value']:
            valid_type = field_data['properties']['valid_types']['value'][0]
        else:
            valid_type = None  # or any default value you prefer

        mapped_name = build_task_relationship_field_name(entity_type, field_name, data_type)

        all_mapped_fields.append(mapped_name)

        # Store field info in the dictionary
        field_info[display_name] = {
            'data_type': data_type,
            'entity_type': entity_type,
            'display_name': display_name,
            'field_name': field_name,
            'valid_types': valid_type,
            'display_values': display_values,
            'mapped_name': mapped_name
        }


    return field_info, all_mapped_fields

def get_entity_info():
    print("GETTING ENTITY MAP")
    # Get all entity types
    entities = ['Task', 'Shot', 'Sequence', 'Asset', 'Project', 'Episode', 'Version']

    entity_dict = {}
    all_mapped_fields = []

    for entity in entities:
        field_info, mapped_fields = get_all_field_info(entity)

        entity_dict[entity] = field_info

        all_mapped_fields.extend(mapped_fields)

    # print(entity_dict)
    # print("ALL MAPPED FIELDS")
    # print(all_mapped_fields)
    return entity_dict, all_mapped_fields

if __name__ == "__main__":
    sg = get_sg_connection()

    user_object = FL.sg_user_object
    user = str(user_object)

    fields = ['episode',
              'episode.Episode.name',
              'name',
              'step',
              'entity.Shot.sg_sequence.Sequence.episode',
              'entity.Sequence.episode',
              'entity.Sequence.episode.name',
              'entity.Sequence.episode.code',
              'project.Project.name',
              'id']

    tasks = get_user_tasks(user, fields)

    for task in tasks:
        if task['project.Project.name'] == '[COY] Coyote - Season 0':
            print(task)

    get_pipeline_step_data()
    # print(tasks)

