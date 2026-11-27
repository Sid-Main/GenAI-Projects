"""Declarative base for all ORM models, with a consistent constraint naming convention."""

from sqlalchemy import MetaData

# DeclarativeBase: parent class for ORM models (Python classes mapped to tables)
from sqlalchemy.orm import DeclarativeBase

# Predictable names for indexes/constraints, so migrations can reliably find and drop them
NAMING_CONVENTION = {
    # index
    "ix": "ix_%(column_0_label)s",
    # unique constraint
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    # check constraint
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    # foreign key
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    # primary key
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    # Every model inheriting from Base registers its table in this metadata
    metadata = MetaData(naming_convention=NAMING_CONVENTION)
