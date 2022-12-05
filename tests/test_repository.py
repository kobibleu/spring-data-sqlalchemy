import pytest
from springdata.domain import Sort, Direction, Pageable
from sqlalchemy import create_engine, delete
from sqlalchemy.orm import Session

from tests.fixtures.orm import Base, DummyOrm
from tests.fixtures.repository import DummyRepository


engine = create_engine("sqlite:///:memory:", echo=True)

with engine.begin() as conn:
    conn.run_callable(Base.metadata.create_all)


@pytest.fixture
def session():
    session = Session(bind=engine)
    yield session
    session.close()


@pytest.fixture
def repository(session):
    return DummyRepository(session)


@pytest.fixture
def dummies(session):
    dummies = [
        DummyOrm(id=1, data="a"),
        DummyOrm(id=2, data="b"),
        DummyOrm(id=3, data="c"),
    ]
    session.add_all(dummies)
    session.commit()
    return dummies


@pytest.fixture
def clean_database(session):
    yield
    session.execute(delete(DummyOrm))
    session.commit()


@pytest.mark.usefixtures("dummies", "clean_database")
def test_should_count_repository(repository):
    assert repository.count() == 3


@pytest.mark.usefixtures("dummies", "clean_database")
def test_should_clear_repository(repository):
    repository.clear()
    assert repository.count() == 0


@pytest.mark.usefixtures("clean_database")
def test_should_delete_entity(repository, dummies):
    repository.delete(dummies[0])
    assert repository.count() == 2


@pytest.mark.usefixtures("clean_database")
def test_should_delete_all_entities(repository, dummies):
    repository.delete_all([dummies[0], dummies[1]])
    assert repository.count() == 1


@pytest.mark.usefixtures("dummies", "clean_database")
def test_should_delete_all_entities_by_id(repository):
    repository.delete_all_by_id([1, 2])
    assert repository.count() == 1


@pytest.mark.usefixtures("dummies", "clean_database")
def test_should_delete_entity_by_id(repository):
    repository.delete_by_id(1)
    assert repository.count() == 2


@pytest.mark.usefixtures("dummies", "clean_database")
def test_should_entity_exists_by_id(repository):
    assert repository.exists_by_id(1)


@pytest.mark.usefixtures("clean_database")
def test_should_entity_does_not_exist_by_id(repository):
    assert not repository.exists_by_id(1)


@pytest.mark.usefixtures("dummies", "clean_database")
def test_should_find_all_entities(repository):
    result = repository.find_all()
    assert [row.id for row in result] == [1, 2, 3]


@pytest.mark.usefixtures("dummies", "clean_database")
def test_should_find_all_entities_with_sorting(repository):
    result = repository.find_all(Sort.by("id", direction=Direction.DESC))
    assert [row.id for row in result] == [3, 2, 1]


@pytest.mark.usefixtures("dummies", "clean_database")
def test_should_find_all_entities_by_id(repository):
    result = repository.find_all_by_id([1, 2, 4])
    assert [row.id for row in result] == [1, 2]


@pytest.mark.usefixtures("dummies", "clean_database")
def test_should_find_entity_by_id(repository):
    result = repository.find_by_id(1)
    assert result.id == 1


@pytest.mark.usefixtures("clean_database")
def test_should_not_find_entity_by_id(repository):
    result = repository.find_by_id(1)
    assert not result


@pytest.mark.usefixtures("clean_database")
def test_should_save_entity(repository):
    result = repository.save(DummyOrm(id=1, data="a"))
    assert result.id == 1
    assert repository.count() == 1


@pytest.mark.usefixtures("clean_database")
def test_should_save_all_entities(repository):
    result = repository.save_all([
        DummyOrm(id=1, data="a"),
        DummyOrm(id=2, data="b"),
        DummyOrm(id=3, data="c"),
    ])
    assert [row.id for row in result] == [1, 2, 3]
    assert repository.count() == 3


@pytest.mark.usefixtures("dummies", "clean_database")
def test_should_find_page_of_entities(repository):
    result = repository.find_page(Pageable.of_size(10))
    assert [row.id for row in result.content] == [1, 2, 3]
    assert result.total_elements == 3
