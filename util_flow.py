from shotgun_api3 import Shotgun, AuthenticationFault
from tank.authentication import ShotgunAuthenticator
import util_globals as FL

def get_sg_connection():
    """
    Create a Shotgun connection via the user object
    This will initialize MWB.sg and MWB.sg_username Globals as well.
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
                     'step',
                     'id',
                     'project.Project.name',
                     'entity.project.Project',
                     'project.Project.id',
                     'entity.Shot.sg_sequence.Sequence.episode',
                     'project.Project.sg_mw_shot_regex',
                     'project.Project.image']

    tasks = sg.find('Task', filters, result_format, include_archived_projects=False)

    print(tasks[0].get('entity.Shot.image'))
    print(tasks[0].get('project.Project.image'))

    sample_list = []
    i = 0
    for task in tasks:
        i += 1
        if i <= 6:
            print(tasks[i])
            sample_list.append(tasks[i])

    return sample_list
    # return tasks

# Used to extract from all user tasks the unique and sorted project names and project images
def get_project_names_and_images(tasks):
    unique_project_names = set()
    for task in tasks:
        project_name = task.get('project.Project.name')
        if project_name:
            unique_project_names.add(project_name)
    return sorted(list(unique_project_names))


def get_unique_project_tasks(project, tasks):
    pass

