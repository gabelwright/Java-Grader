import os
import sys
import datetime
from sqlalchemy import Column, ForeignKey, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    f_name = Column(String(100), nullable=False)
    l_name = Column(String(100), nullable=False)
    email = Column(String(250), nullable=False)
    username = Column(String(250), nullable=False)
    password = Column(String, nullable=False)
    salt = Column(String(10), nullable=False)
    admin = Column(Boolean, nullable=False)
    created = Column(DateTime, default=datetime.datetime.today)


class Assignment(Base):
    __tablename__ = 'assignment'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    desc = Column(String)
    int_type = Column(Integer)
    created = Column(DateTime, default=datetime.datetime.today)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)


class Test(Base):
    __tablename__ = 'test'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    test_code = Column(String, nullable=False)
    created = Column(DateTime, default=datetime.datetime.today)
    assignment_id = Column(Integer, ForeignKey('assignment.id'))
    assignment = relationship(Assignment)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)


class Post(Base):
    __tablename__ = 'post'

    id = Column(Integer, primary_key=True)
    code = Column(String, nullable=False)
    notes = Column(String)
    results = Column(String)
    created = Column(DateTime, default=datetime.datetime.today)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)
    assignment_id = Column(Integer, ForeignKey('assignment.id'))
    assignment = relationship(Assignment)


engine = create_engine('postgresql://db:dbpass@localhost/db')
# engine = create_engine('sqlite:///codin-site.db')
Base.metadata.create_all(engine)
