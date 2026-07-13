"""爻辞 ORM 模型"""

from sqlalchemy import Column, Integer, String, Text, ForeignKey
from models.hexagram_model import Base


class YaoLineModel(Base):
    """爻辞表模型"""
    __tablename__ = "yao_lines"

    id = Column(Integer, primary_key=True, autoincrement=True)
    hexagram_id = Column(Integer, ForeignKey("hexagrams.id"), nullable=False)
    position = Column(Integer, nullable=False)
    yao_name = Column(String)
    yao_type = Column(String)
    original_text = Column(Text)
    translation = Column(Text)
