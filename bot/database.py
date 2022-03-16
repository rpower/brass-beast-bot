import datetime
import sqlalchemy as db
from sqlalchemy.orm import declarative_base, sessionmaker

table_name = 'server_logs'
engine = db.create_engine(f'sqlite:///../{table_name}.db')
Base = declarative_base()

def create_table():
    meta = db.MetaData()

    logs_table = db.Table(
        table_name, meta,
        db.Column('datetime', db.DateTime, primary_key=True),
        db.Column('server', db.String),
        db.Column('action', db.String),
        db.Column('user_id', db.String),
        db.Column('user_name', db.String),
        db.Column('channel', db.String)
    )

    meta.create_all(engine)

# Create table if it doesn't exist
does_table_exist = db.inspect(engine).has_table(table_name)
if not does_table_exist:
    create_table()

class Log(Base):
    __tablename__ = table_name

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

async def log_message(message):
    add_log_entry(
        datetime.datetime.now(),
        message.guild.id,
        'message',
        message.author.id,
        message.author.display_name,
        message.channel.id
    )

async def log_voice(member, before, after):
    if before.channel is None and after.channel is not None and member.bot is not None:
        add_log_entry(
            datetime.datetime.now(),
            after.channel.guild.id,
            'voice',
            member.id,
            member.display_name,
            after.channel.id
        )