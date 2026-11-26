from sqlalchemy import Column, Integer, Float, DateTime, Boolean
from .database import Base


class Reading(Base):
    __tablename__ = "readings"

    id = Column(Integer, primary_key=True, index=True)
    ts = Column(DateTime, nullable=False, index=True)
    kwh = Column(Float, nullable=False)
    is_anomaly = Column(Boolean, nullable=False, default=False)
    score = Column(Float, nullable=True)
