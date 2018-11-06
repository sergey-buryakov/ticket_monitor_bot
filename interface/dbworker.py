from vedis import Vedis

db_file = "database.vdb"


def get_user(user_id):
    with Vedis(db_file) as db:
        try:
            return db[user_id]
        except KeyError:
            return None

def set_user(user_id, value):
    with Vedis(db_file) as db:
        try:
            db[user_id] = value
            return True
        except:
            return False