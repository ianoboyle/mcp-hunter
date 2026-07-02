import uuid

from peewee import (
    BooleanField,
    CharField,
    DateTimeField,
    ForeignKeyField,
    IntegerField,
    SqliteDatabase,
    Model,
    TextField,
    UUIDField,
)
from config import SQLITE_DATABASE_NAME

db = SqliteDatabase(SQLITE_DATABASE_NAME)


class BaseModel(Model):
    id = UUIDField(primary_key=True, default=uuid.uuid4)

    class Meta:
        database = db


class RegistryItem(BaseModel):
    name = CharField()
    repository = TextField()


class Repository(BaseModel):
    registry_item = ForeignKeyField(RegistryItem, backref="registry")
    owner_repo = CharField()
    repo_url = TextField()
    stars = IntegerField(null=True)
    ecosystem = CharField(null=True)
    commit_sha = CharField(null=True)
    active = BooleanField(null=True)
    last_pushed = DateTimeField(null=True)
    error = TextField(null=True)
