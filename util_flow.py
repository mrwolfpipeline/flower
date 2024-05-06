from shotgun_api3 import Shotgun, AuthenticationFault
from tank.authentication import ShotgunAuthenticator
import util_globals


def get_sg_connection():
    """
    Create a Shotgun connection via the user object
    This will initialize MWB.sg and MWB.sg_username Globals as well.
    Use at the start of a hook script.
    """
    Shotgun.NO_SSL_VALIDATION = True
    # sgtk.LogManager().initialize_custom_handler()
    # sgtk.LogManager().global_debug = True
    sa = ShotgunAuthenticator()

    # THIS LOGIN METHOD LOOKS TO SEE IF A USER IS LOGGED IN AND IF NOT CLOSES OUT OF NUKE BY RETURNING NONE
    user = sa.get_default_user()

    # ENABLE THESE TWO LINES TO ADD USER AUTHENTICATION LINKED BY PERSONAL ACCESS TOKEN
    # user = sa.get_user()
    # sg = user.create_sg_connection()

    if user:
        # todo: this can error out!
        sg = user.create_sg_connection()

        util_globals.sg = sg
        util_globals.sg_user_login = user.login
        return sg
    else:
        print("ERROR")
        print('No ShotGrid User found...Please log in using SG Desktop.')

    return None
