from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

engine = create_engine("sqlite:///foodie.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    restaurants = relationship("SavedRestaurant", back_populates="user")

class SavedRestaurant(Base):
    __tablename__ = "saved_restaurants"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    yelp_id = Column(String)
    name = Column(String)
    image_url = Column(String)
    url = Column(String)
    saved_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="restaurants")

Base.metadata.create_all(bind=engine)

