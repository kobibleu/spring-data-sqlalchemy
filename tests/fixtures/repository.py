from springdata_sqlalchemy.repository import PagingRepository
from tests.fixtures.orm import DummyOrm


class DummyRepository(PagingRepository[DummyOrm, int]):
    pass
