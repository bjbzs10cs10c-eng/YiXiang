"""占卜记录 ORM 模型"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from models.hexagram_model import Base


class InterpretationModel(Base):
    """解释表模型"""
    __tablename__ = "interpretations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    target_type = Column(String, nullable=False)
    target_id = Column(Integer, nullable=False)
    source = Column(String)
    title = Column(String)
    content = Column(Text)


class DivinationRecordModel(Base):
    """占卜记录表模型"""
    __tablename__ = "divination_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    create_time = Column(DateTime)
    question = Column(Text)
    original_hexagram = Column(Integer, ForeignKey("hexagrams.id"))
    changed_hexagram = Column(Integer, ForeignKey("hexagrams.id"))
    moving_lines = Column(Text)    # JSON格式
    yao_values = Column(Text)      # JSON格式
    notes = Column(Text)


class SettingModel(Base):
    """设置表模型"""
    __tablename__ = "settings"

    key = Column(String, primary_key=True)
    value = Column(String)
