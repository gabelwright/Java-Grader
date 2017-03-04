from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db_setup import Base, User, Assignment, Test, Post

# engine = create_engine('postgresql://db:dbpass@localhost/db')
engine = create_engine('sqlite:///codin-site.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

# Promote user to admin
# USER_TO_PROMOTE = 'username goes here'
# user = session.query(User).filter(User.username == USER_TO_PROMOTE).first()
# if user:
# 	user.admin = True
# 	session.commit()


post = session.query(Post).filter(Post.id == 1).first()
post.created = None
session.commit()


# Demote user from admin
# USER_TO_DEMOTE = 'username goes here'
# user = session.query(User).filter(User.username == USER_TO_DEMOTE).first()
# if user:
# 	user.admin = False
# 	session.commit()


# Delete all data in database
# us = session.query(Test).delete()
# print 'deleted %s rows from Test' % us
# session.commit()
# us = session.query(Assignment).delete()
# print 'deleted %s rows from Test' % us
# session.commit()
# us = session.query(Post).delete()
# print 'deleted %s rows from Test' % us
# session.commit()
# us = session.query(User).delete()
# print 'deleted %s rows from Test' % us
# session.commit()


# Drop all tables
# Base.metadata.drop_all(engine)
