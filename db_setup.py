import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    username = Column(String(250), nullable=False)
    password = Column(String, nullable=False)
    salt = Column(String(10), nullable=False)


class Assignment(Base):
    __tablename__ = 'assignment'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    desc = Column(String)
    test1 = Column(String)
    test2 = Column(String)
    test3 = Column(String)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)


class Post(Base):
    __tablename__ = 'post'

    id = Column(Integer, primary_key=True)
    code = Column(String, nullable=False)
    notes = Column(String)
    results = Column(String)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)
    assignment_id = Column(Integer, ForeignKey('assignment.id'))
    assignment = relationship(Assignment)


engine = create_engine('sqlite:///codin-site.db')
Base.metadata.create_all(engine)
