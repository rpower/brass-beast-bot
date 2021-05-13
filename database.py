import json
import sqlalchemy as db
from sqlalchemy.orm import declarative_base, sessionmaker

with open('credentials.json') as credentials_file:
    credentials = json.loads(credentials_file.read())

engine = db.create_engine(credentials['sql_details']['path_to_db'])

Base = declarative_base()

class Log(Base):
    __tablename__ = credentials['sql_details']['table_name']

    datetime = db.Column(db.DateTime, primary_key = True)
    server = db.Column(db.String)
    action = db.Column(db.String)
    user_id = db.Column(db.String)
    user_name = db.Column(db.String)
    channel = db.Column(db.String)

def add_log_entry(datetime, server, action, user_id, user_name, channel):
    # Create session
    original_session = sessionmaker()
    original_session.configure(bind = engine)
    session = original_session()

    # Create new entry
    new_log_entry = Log(
        datetime = datetime,
        server = server,
        action = action,
        user_id = user_id,
        user_name = user_name,
        channel = channel
    )
    session.add(new_log_entry)

    # Commit to server
    session.commit()
    session.close()