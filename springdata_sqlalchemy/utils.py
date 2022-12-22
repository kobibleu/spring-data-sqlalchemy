from typing import List, Any, Generic, TypeVar, Tuple

from sqlalchemy.orm import DeclarativeMeta


T = TypeVar("T", bound=DeclarativeMeta)
ID = TypeVar("ID")


class EntityInformation(Generic[T, ID]):
    def __init__(self, orm_class: DeclarativeMeta):
        self._orm_class = orm_class

    @property
    def attribute_names(self) -> Tuple[str, ...]:
        return tuple(self._orm_class.__table__.columns.keys())

    @property
    def id_attributes(self) -> Tuple:
        return tuple(getattr(self._orm_class, attr) for attr in self.id_attribute_names)

    @property
    def id_attribute_names(self) -> Tuple[str, ...]:
        return tuple(self._orm_class.__table__.primary_key.columns.keys())

    def has_composite_id(self) -> bool:
        return len(self._orm_class.__table__.primary_key.columns.keys()) > 1

    def get_id(self, entity: T) -> ID:
        if not self.has_composite_id():
            return getattr(entity, self.id_attribute_names[0])
        return (getattr(entity, attr) for attr in self.id_attribute_names)

    def is_new(self, entity: T) -> bool:
        return not bool(self.get_id(entity))
