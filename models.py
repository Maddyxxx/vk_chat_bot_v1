
from pony.orm import Database, Required, Json

from settings import DB_CONFIG

db = Database()
db.bind(**DB_CONFIG)


class UserState(db.Entity):
    """Состояние позьзователя внутри сценария """
    user_id = Required(str, unique=True)
    scenario_name = Required(str)
    step_name = Required(str)
    context = Required(Json)


class Ticket(db.Entity):
    """Информация по билету"""
    dep_city = Required(str)
    dest_city = Required(str)
    fly_date = Required(str)
    flight = Required(str)
    places = Required(int)
    comment = Required(str)
    name = Required(str)
    phone_number = Required(str)


db.generate_mapping(create_tables=True)
