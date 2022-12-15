from typing import TypeVar, Generic, List, Optional, get_args

from springdata.domain import Page, Sort, Pageable
from sqlalchemy import select, delete, func
from sqlalchemy.orm import Session, DeclarativeMeta
from sqlalchemy.sql import Select

from springdata_sqlalchemy.utils import EntityInformation

T = TypeVar("T", bound=DeclarativeMeta)
ID = TypeVar("ID")


class CrudRepository(Generic[T, ID]):
    """
    Interface for generic CRUD operations on a repository for a SQLAlchemy Object Relational Mapper.
    """

    def __init__(self, session: Session):
        type_args = get_args(self.__orig_bases__[0])
        self._orm = type_args[0]
        self._session = session
        self.entity_information = EntityInformation[T, ID](self._orm)
        if self.entity_information.has_composite_id():
            raise ValueError("Object Relational Mapper must have one and only primary key")

    def clear(self) -> None:
        """
        Deletes all entities managed by the repository.
        """
        self._session.execute(delete(self._orm))
        self._session.commit()

    def count(self) -> int:
        """
        Returns the number of entities available.

        :return: the number of entities.
        """
        return self._execute_count(select(self._orm))

    def delete(self, entity: T) -> None:
        """
        Deletes a given entity.

        :param entity: must not be None.
        :raises ValueError: in case the given entity is None.
        """
        if entity is None:
            raise ValueError("Entity must not be None")
        self._session.delete(entity)
        self._session.commit()

    def delete_all(self, entities: List[T]) -> None:
        """
        Deletes the given entities.

        :param entities: must not be None. Must not contain None elements.
        :raises ValueError: in case the given entities or one of its entities is None.
        """
        if entities is None or any(e is None for e in entities):
            raise ValueError("Entities or one of its elements must not be None")
        for e in entities:
            self._session.delete(e)
        self._session.commit()

    def delete_all_by_id(self, ids: List[ID]) -> None:
        """
        Deletes all entities with the given IDs.

        Entities that aren't found in the persistence store are silently ignored.

        :param ids: must not be None. Must not contain None elements.
        :raises ValueError: in case the given ids or one of its elements is None.
        """
        if ids is None or any(id_ is None for id_ in ids):
            raise ValueError("IDs or one of its elements must not be None")
        statement = delete(self._orm).where(self.entity_information.id_attributes[0].in_(ids))
        self._session.execute(statement)

    def delete_by_id(self, id_: ID) -> None:
        """
        Deletes the entity with the given id.

        If the entity is not found in the persistence store it is silently ignored.

        :param id_: must not be None.
        :raises ValueError: if id is None.
        """
        if id_ is None:
            raise ValueError("ID must not be None")
        statement = delete(self._orm).where(self.entity_information.id_attributes[0] == id_)
        self._session.execute(statement)

    def exists_by_id(self, id_: ID) -> bool:
        """
        Returns whether an entity with the given id exists.

        :param id_: must not be None.
        :return: true if an entity with the given id exists, false otherwise.
        :raises ValueError: if id is None.
        """
        if id_ is None:
            raise ValueError("ID must not be None")
        statement = select(self._orm).where(self.entity_information.id_attributes[0] == id_)
        return bool(self._execute_count(statement))

    def find_all(self, sort: Optional[Sort] = None) -> List[T]:
        """
        Returns all entities.

        :param sort: the specification to sort the results by, default to None.
        :return: all entities.
        """
        statement = self._with_ordering(select(self._orm), sort)
        return self._session.execute(statement).unique().scalars().all()

    def find_all_by_id(self, ids: List[ID], sort: Optional[Sort] = None) -> List[T]:
        """
        Returns all entities with the given IDs.

        If some or all ids are not found, no entities are returned for these IDs.

        :param ids: must not be None nor contain any None values.
        :param sort: the specification to sort the results by, default to None.
        :return: guaranteed to be not None. The size can be equal or less than the number of given ids.
        :raises ValueError: in case the given ids or one of its elements is None.
        """
        statement = select(self._orm).where(self.entity_information.id_attributes[0].in_(ids))
        statement = self._with_ordering(statement, sort)
        return self._session.execute(statement).unique().scalars().all()

    def find_by_id(self, id_: ID) -> Optional[T]:
        """
        Retrieves an entity by its id.

        :param id_: must not be None.
        :return: the entity with the given id or None if none found.
        :raises ValueError: if id is None.
        """
        return self._session.get(self._orm, id_)

    def save(self, entity: T) -> T:
        """
        Saves a given entity.

        Use the returned instance for further operations as the save operation might have changed the entity instance
        completely.

        :param entity: must not be None.
        :return: the saved entity, will never be None.
        :raises ValueError: in case the given entity is None.
        """
        entity = self._synchronize_entity(entity)
        self._session.add(entity)
        self._session.commit()
        self._session.refresh(entity)
        return entity

    def save_all(self, entities: List[T]) -> List[T]:
        """
        Saves all given entities.

        :param entities: must not be None nor must it contain None.
        :return: the saved entities; will never be None. The returned iterable will have the same size as the iterable
                 passed as an argument.
        :raises ValueError: in case the given entities or one of its entities is None.
        """
        entities = [self._synchronize_entity(e) for e in entities]
        self._session.add_all(entities)
        self._session.commit()
        for e in entities:
            self._session.refresh(e)
        return entities

    def _execute_count(self, statement: Select) -> int:
        """
        Execute a COUNT function with the given SELECT statement.

        :param statement: must not be None
        :return: count result
        """
        statement = statement.with_only_columns([func.count(self.entity_information.id_attributes[0])])
        return self._session.execute(statement).scalar()

    def _with_ordering(self, statement: Select, sort: Optional[Sort]) -> Select:
        """
        Returns a SELECT statements with the given list of ORDER BY criteria applied.

        :param statement: must not be None
        :param sort: the specification to sort the results by
        :return: same statement if sort is None else new statement with sort applied
        """
        if sort is None:
            return statement
        clauses = []
        for order in sort.orders:
            attr = getattr(self._orm, order.property)
            clauses.append(attr.asc() if order.is_ascending() else attr.desc())
        return statement.order_by(*clauses)

    def _synchronize_entity(self, entity: T):
        """
        Synchronize the entity to the one persisted in database if exists.

        :param entity: must not be None
        :return: synchronized entity
        """
        if self.entity_information.is_new(entity):
            return entity
        else:
            old_entity = self._session.get(self._orm, self.entity_information.get_id(entity))
            if old_entity:
                for attr in self.entity_information.attribute_names:
                    v = getattr(entity, attr)
                    setattr(old_entity, attr, v)
                entity = old_entity
            return entity


class PagingRepository(Generic[T, ID], CrudRepository[T, ID]):
    """
    Interface to retrieve entities using the pagination.
    """

    def find_page(self, pageable: Pageable, sort: Optional[Sort] = None) -> Page[T]:
        """
        Returns a :class:`Page` of entities meeting the paging restriction provided in the :class:`Pageable` object.

        :param pageable: must not be None.
        :param sort: the specification to sort the results by, default to None.
        :return: a page of entities.
        :raises ValueError: in case the :class:`Pageable` is None.
        """
        if pageable is None:
            raise ValueError("Pageable must not be None")
        return self._execute_page(select(self._orm), pageable, sort)

    def _execute_page(self, statement: Select, pageable: Pageable, sort: Optional[Sort] = None) -> Page[T]:
        """
        Execute a COUNT function and the given SELECT statement.

        :param statement: must not be None
        :param sort: the specification to sort the results by, default to None.
        :return: a page of entities
        """
        total = self._execute_count(statement)
        statement = self._with_paging(statement, pageable)
        statement = self._with_ordering(statement, sort)
        content = self._session.execute(statement).unique().scalars().all()
        return Page(content, pageable, total)

    def _with_paging(self, statement: Select, pageable: Pageable) -> Select:
        """
        Returns a SELECT statements with the given offset and limit applied.

        :param statement: must not be None
        :param pageable: the information to request a paged result, must not be None
        :return: new statement
        """
        return statement.offset(pageable.offset).limit(pageable.page_size)
