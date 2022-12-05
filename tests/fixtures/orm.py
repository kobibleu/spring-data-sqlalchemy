from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class DummyOrm(Base):
    id: int = Column(Integer, primary_key=True)
    data: str = Column(String(255), nullable=False)

    __tablename__ = "dummy"
