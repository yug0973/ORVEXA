import os
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import declarative_base, relationship
from backend.config import settings

Base = declarative_base()

# Determine database dialect to support SQLite async fallback without GIS errors
DATABASE_URL = os.getenv("DATABASE_URL", settings.DATABASE_URL)
IS_SQLITE = "sqlite" in DATABASE_URL.lower()

if IS_SQLITE:
    # Under SQLite fallback, store the GeoJSON/WKT polygon geometry as Text
    from sqlalchemy import Text
    SpatialType = Text
else:
    # Under real PostgreSQL, use GeoAlchemy2 spatial Geometry type mapping to PostGIS Polygon type (SRID 4326)
    from geoalchemy2 import Geometry
    SpatialType = Geometry(geometry_type='POLYGON', srid=4326)


class Satellite(Base):
    __tablename__ = 'satellites'
    
    norad_id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    operator = Column(String(100))
    type = Column(String(50))
    tle1 = Column(String(100), nullable=False)
    tle2 = Column(String(100), nullable=False)
    updated_at = Column(DateTime, nullable=False)

    # Relationships
    state_vectors = relationship("StateVector", back_populates="satellite", cascade="all, delete-orphan")
    reentry_alert = relationship("ReentryAlert", back_populates="satellite", uselist=False, cascade="all, delete-orphan")


class StateVector(Base):
    __tablename__ = 'state_vectors'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    norad_id = Column(Integer, ForeignKey('satellites.norad_id', ondelete='CASCADE'), nullable=False)
    epoch = Column(DateTime, nullable=False)
    
    # 3D position [x,y,z] in km
    position_x = Column(Float, nullable=False)
    position_y = Column(Float, nullable=False)
    position_z = Column(Float, nullable=False)
    
    # 3D velocity [vx,vy,vz] in km/s
    velocity_x = Column(Float, nullable=False)
    velocity_y = Column(Float, nullable=False)
    velocity_z = Column(Float, nullable=False)

    # Relationship
    satellite = relationship("Satellite", back_populates="state_vectors")


class ConjunctionEvent(Base):
    __tablename__ = 'conjunction_events'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    primary_norad = Column(Integer, ForeignKey('satellites.norad_id', ondelete='CASCADE'), nullable=False)
    secondary_norad = Column(Integer, ForeignKey('satellites.norad_id', ondelete='CASCADE'), nullable=False)
    tca = Column(DateTime, nullable=False)
    miss_distance = Column(Float, nullable=False)
    
    # Encounter frame relative coordinate offsets
    radial = Column(Float)
    in_track = Column(Float)
    cross_track = Column(Float)
    
    pc = Column(Float, nullable=False)
    covariance_matrix = Column(JSON)  # Maps automatically to JSONB on Postgres
    compliance_status = Column(String(50))


class ReentryAlert(Base):
    __tablename__ = 'reentry_alerts'
    
    norad_id = Column(Integer, ForeignKey('satellites.norad_id', ondelete='CASCADE'), primary_key=True)
    name = Column(String(100), nullable=False)
    current_altitude = Column(Float, nullable=False)
    decay_rate = Column(Float)
    eta = Column(DateTime)
    uncertainty_hours = Column(Float)
    survival_pct = Column(Float)
    corridor_geom = Column(SpatialType)  # Spatial geometry or Text fallback
    casualty_probability = Column(Float)

    # Relationship
    satellite = relationship("Satellite", back_populates="reentry_alert")


class ComplianceFiling(Base):
    __tablename__ = 'compliance_filings'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    operator = Column(String(100), nullable=False)
    satellite = Column(String(100), nullable=False)
    tca = Column(DateTime, nullable=False)
    form_data = Column(JSON)  # Maps automatically to JSONB on Postgres
    pdf_path = Column(String(255))
    status = Column(String(50), nullable=False)
    submitted_at = Column(DateTime, nullable=False)


class ManeuverNegotiation(Base):
    __tablename__ = 'maneuver_negotiations'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    conjunction_id = Column(Integer, ForeignKey('conjunction_events.id', ondelete='CASCADE'), nullable=False)
    status = Column(String(50), default="Proposed") # "Proposed", "Accepted", "Rejected", "Completed"
    
    primary_maneuver = Column(JSON, nullable=True) # { dv_radial, dv_in_track, dv_cross_track, epoch }
    primary_status = Column(String(50), default="Pending") # "Pending", "Approved", "Declined"
    
    secondary_maneuver = Column(JSON, nullable=True) # { dv_radial, dv_in_track, dv_cross_track, epoch }
    secondary_status = Column(String(50), default="Pending") # "Pending", "Approved", "Declined"
    
    updated_at = Column(DateTime, nullable=False, default=datetime.now)
