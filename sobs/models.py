import os

from peewee import *
from playhouse.sqlite_ext import SqliteExtDatabase, JSONField


def get_database():
    db = SqliteExtDatabase(
        "sra.sqlite3",
        pragmas=(
            ("cache_size", -1024 * 64),  # 64MB page cache
            ("journal_mode", "wal"),  # use WAL-mode (you should always use this!)
            ("foreign_keys", 1),  # enforce foreign key constraints (is this not on by default?)
        ),
    )
    return db


class Base(Model):
    class Meta:
        database = get_database()


class Sample(Base):
    id = CharField(primary_key=True, index=True)
    taxid = IntegerField(null=True, index=True)
    attributes = JSONField()

    scientific_name = CharField(null=True)


class Experiment(Base):

    id = CharField(primary_key=True, index=True)
    sample_accession = CharField(null=True, index=True)
    description = TextField(null=True)

    library_name = CharField(null=True)
    library_strategy = CharField(null=True)
    library_source = CharField(null=True)
    library_selection = CharField(null=True)
    library_layout = CharField(null=True)
    platform_type = CharField(null=True)
    platform_instrument_model = CharField(null=True)


class Run(Base):
    id = CharField(primary_key=True, index=True)

    experiment_accession = CharField(null=True, index=True)
    title = CharField(null=True)
