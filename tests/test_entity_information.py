import pytest

from springdata_sqlalchemy.utils import EntityInformation
from tests.fixtures.orm import DummyOrm


@pytest.fixture
def entity_information():
    return EntityInformation[DummyOrm, int](DummyOrm)


@pytest.fixture
def entity():
    return DummyOrm(id=1, data="a")


def test_should_get_attribute_names(entity_information):
    assert entity_information.attribute_names == ("id","data")


def test_should_get_id_attribute_names(entity_information):
    assert entity_information.id_attribute_names == ("id",)


def test_should_get_id_attributes(entity_information):
    assert entity_information.id_attributes == (DummyOrm.id,)


def test_should_not_have_composite_id(entity_information):
    assert not entity_information.has_composite_id()


def test_should_get_entity_id(entity_information, entity):
    assert entity_information.get_id(entity) == 1


def test_should_be_new(entity_information, entity):
    entity.id = None
    assert entity_information.is_new(entity)


def test_should_not_be_new(entity_information, entity):
    assert not entity_information.is_new(entity)
