"""六十四卦 ORM 模型"""

from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class HexagramModel(Base):
    """六十四卦表模型"""
    __tablename__ = "hexagrams"

    id = Column(Integer, primary_key=True)
    sequence = Column(Integer, nullable=False)
    name = Column(String, nullable=False)
    symbol = Column(String)
    binary_code = Column(String, nullable=False, unique=True)
    upper_trigram = Column(String)
    lower_trigram = Column(String)
    gua_ci = Column(Text)
    tuan_ci = Column(Text)
    xiang_ci = Column(Text)
