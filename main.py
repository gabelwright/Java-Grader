from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, abort
from sqlalchemy import func, desc
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from flask import session as login_session
from werkzeug.utils import secure_filename
import random
import string
from db_setup import Base, User, Post, Assignment
import json
import hashlib
import os
from flask import make_response
import requests


app = Flask(__name__)

engine = create_engine('sqlite:///codin-site.db')
Base.metadata.bind = engine
DBsession = sessionmaker(bind=engine)
session = DBsession()


def hash_cookie(user):
    hash_text = hashlib.sha512(user.username).hexdigest()
    cookie_text = '%s|%s' % (user.username, hash_text)
    print cookie_text
    return cookie_text


def setCookie(user):
    cookie_value = hash_cookie(user)
    response = app.make_response(redirect(url_for('main')))
    response.set_cookie('user_id', value=cookie_value)
    return response


def check_for_user():
    cookie_value = request.cookies.get('user_id')
    print cookie_value
    if cookie_value:
        params = cookie_value.split('|')
        if hashlib.sha512(params[0]).hexdigest() == params[1]:
            user = session.query(User).filter(User.username == params[0]).first()
            if user:
                print 'logged in as ' + user.username
                return user


def make_salt():
    salt = ''.join(random.choice(
        string.ascii_uppercase + string.digits) for x in xrange(7))
    return salt


@app.route('/')
def main():
    user = check_for_user()
    posts = session.query(Post).all()
    return render_template('main.html',
                           user=user,
                           posts=posts)


@app.route('/newpost', methods=['GET', 'POST'])
def newPost():
    if request.method == 'GET':
        user = check_for_user()
        if not user:
            return redirect(url_for('login'))
        return render_template('newpost.html',
                               user=user,
                               p=None)
    else:
        print 'POST'
        title = request.form['title']
        post = request.form['post']
        user_id = request.form['user_id']
        print title, post, user_id
        if title and post and user_id:
            post = Post(title=title,
                        desc=post,
                        user_id=user_id)
            session.add(post)
            session.commit()
            return redirect(url_for('main'))
        else:
            error = "All fields are required. Do not leave any blank."
            return render_template('newpost.html',
                                   user=user,
                                   e=None,
                                   error_message=error)


@app.route('/post/<int:post_id>/0')
def postView(post_id):
    user = check_for_user()
    post = session.query(Post).filter(Post.id == post_id).first()
    return render_template('post.html',
                           user=user,
                           p=post)


@app.route('/edit/<int:post_id>', methods=['POST', 'GET'])
def editPost(post_id):
    post = session.query(Post).filter(Post.id == post_id).first()
    if request.method == 'GET':
        user = check_for_user()
        if not user:
            return redirect(url_for('postView', post_id=post_id))
        return render_template('newpost.html',
                               user=user,
                               p=post)
    else:
        title = request.form['title']
        des = request.form['post']
        if title and des:
            post.title = title
            post.desc = des
            session.commit()
            return redirect(url_for('postView', post_id=post_id))


@app.route('/delete/<int:post_id>', methods=['POST'])
def deletePost(post_id):
    post = session.query(Post).filter(Post.id == post_id).first()
    session.delete(post)
    session.commit()
    return redirect(url_for('main'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        user = check_for_user()
        if user:
            return redirect(url_for('main'))
        else:
            return render_template('login.html')
    else:
        username = request.form['username']
        password = request.form['password']

        user = session.query(User).filter(User.username == username).first()
        if user and user.password == hashlib.md5(password).hexdigest():
            return setCookie(user)
        else:
            error = 'Invalid username and/or password'
            return render_template('login.html',
                                   username=username,
                                   error=error)


@app.route('/logout')
def logout():
    response = app.make_response(redirect(url_for('main')))
    cookie_value = ''
    response.set_cookie('user_id', value=cookie_value)
    return response


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template('signup.html')
    else:
        name = request.form['name']
        username = request.form['username'].strip()
        password = request.form['password']
        verify = request.form['verify']
        email = request.form['email']
        userQuery = session.query(User).filter(User.username == username).first()

        if username and email and password and password == verify and not userQuery:
            salt = make_salt()
            hashed_password = hashlib.sha512(password + salt).hexdigest()
            user = User(name=name,
                        email=email,
                        username=username,
                        password=hashed_password,
                        salt=salt)
            session.add(user)
            session.commit()
            return redirect(url_for('login'))
        else:
            message = 'There was a problem with your form.  Please try again.'
            return render_template('signup.html', error_email=message)


@app.route('/all')
def all():
    users = session.query(User).all()
    assign = session.query(Assignment).all()
    posts = session.query(Post).all()

    return render_template('all.html',
                           users=users,
                           posts=posts,
                           assignments=assign)





if __name__ == '__main__':
    app.secret_key = 'something'
    app.debug = False
    app.run(host='0.0.0.0', port=5000)

