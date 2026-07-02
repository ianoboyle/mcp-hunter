import logging
import peewee as pw
from typing import Dict
from config import SQLITE_DATABASE_NAME
from models import RegistryItem, Repository


db = pw.SqliteDatabase(SQLITE_DATABASE_NAME)
db.create_tables([RegistryItem, Repository])


def write_registry_item_if_not_exist(json: Dict) -> None:

    if RegistryItem.select().where(RegistryItem.name == json.get("name")).exists():
        return

    RegistryItem.create(
        name=json.get("name"),
        repository=json.get("repository", {"url": ""}).get("url"),
    )


def write_repository_if_not_exist(registry_item: RegistryItem, data: Dict) -> None:

    if (
        Repository.select()
        .where(Repository.owner_repo == data.get("owner_repo"))
        .exists()
    ):
        return

    try:
        Repository.create(
            registry_item=registry_item.id,
            owner_repo=data.get("owner_repo"),
            repo_url=data.get("repo_url"),
            stars=data.get("stars"),
            ecosystem=data.get("language"),
            # TODO: Fetch Commit SHA
            commit_sha="",
            # TODO: Figure out active logic (maybe just not 404)
            active=True,
            last_pushed=data.get("pushed_at"),
            error=data.get("error"),
        )
    except pw.IntegrityError as ex:
        logging.error(f"Failed to write row for {registry_item.id}: {data}")
        logging.error(f"{ex}")
        raise ex
