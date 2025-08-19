from sqlalchemy import Boolean, Column, DateTime, ForeignKey, LargeBinary, String, Integer, func
from sqlalchemy.orm import relationship

from .db import Base


class Vin(Base):
    __tablename__ = "vins"

    vin = Column(String(17), primary_key=True, index=True)
    wmi = Column(String(3), nullable=False)
    vds = Column(String(6), nullable=False)
    vis = Column(String(8), nullable=False)
    model_year = Column(Integer, nullable=True)
    plant = Column(String(1), nullable=True)
    valid_check_digit = Column(Boolean, nullable=True)
    make = Column(String, nullable=True)
    model = Column(String, nullable=True)
    decoded_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    images = relationship("VinImage", back_populates="vin_ref", cascade="all, delete-orphan")
    nhtsa_data = relationship("NHTSADecodedData", back_populates="vin_ref", cascade="all, delete-orphan")


class VinImage(Base):
    __tablename__ = "vin_images"

    id = Column(Integer, primary_key=True, autoincrement=True)
    vin = Column(String(17), ForeignKey("vins.vin", ondelete="CASCADE"), index=True, nullable=False)
    content_type = Column(String(100), nullable=False, default="image/png")
    data = Column(LargeBinary, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    vin_ref = relationship("Vin", back_populates="images")


class NHTSADecodedData(Base):
    __tablename__ = "nhtsa_decoded_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    vin = Column(String(17), ForeignKey("vins.vin", ondelete="CASCADE"), index=True, nullable=False)
    variable = Column(String, nullable=False)
    value = Column(String, nullable=True)
    variable_id = Column(Integer, nullable=True)
    value_id = Column(String, nullable=True)

    vin_ref = relationship("Vin", back_populates="nhtsa_data")