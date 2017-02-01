from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, abort
from sqlalchemy import func, desc, and_
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from flask import session as login_session
from werkzeug.utils import secure_filename
from functools import wraps
import random
import string
from db_setup import Base, User, Post, Assignment, Test
import json
import hashlib
import os
from flask import make_response
import requests
import shutil
import compileMethods


app = Flask(__name__)

engine = create_engine('sqlite:///codin-site.db')
Base.metadata.bind = engine
DBsession = sessionmaker(bind=engine)
session = DBsession()

ASSIGN_FILE_PATH = '/vagrant/static/assignments/'
POST_DIRECTORY = '/vagrant/static/posts'
ALLOWED_EXTENSIONS = set(['txt'])
ADMIN_LIST = ['mgwright']
MAIN_METHOD_HEADER = 'public class CodinBlog{\n\n'


hash_secret = 'sjkbfkjsbvkfjsdnv;ldfknvlkfssavgfnlghf389562349'


def hash_cookie(user):
    hash_text = hashlib.sha512(user.username + hash_secret).hexdigest()
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
        if hashlib.sha512(params[0] + hash_secret).hexdigest() == params[1]:
            user = session.query(User).filter(User.username == params[0]).first()
            if user:
                print 'logged in as ' + user.username
                return user


def check_password(password, user):
    hashed_pass = hashlib.sha512(password + user.salt).hexdigest()
    if hashed_pass == user.password:
        return True
    else:
        return False


def authenicate(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        print 'Method Decorated'
        user = check_for_user()
        if not user:
            return redirect(url_for('login'))
        return f(user,*args, **kwargs)
    return wrapper


def admin_only(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        print 'admin decorator'
        user = check_for_user()
        if not user or user.username not in ADMIN_LIST:
            return abort(403)
        return f(user,*args, **kwargs)
    return wrapper



def make_salt():
    salt = ''.join(random.choice(
        string.ascii_uppercase + string.digits) for x in xrange(7))
    return salt


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def main():
    user = check_for_user()
    assign = session.query(Assignment).order_by(desc(Assignment.id)).all()
    return render_template('main.html',
                           user=user,
                           assign=assign)


@app.route('/assignment/<int:assign_id>', methods=['GET', 'POST'])
@authenicate
def assignView(user,assign_id):
    if request.method == 'GET':
        assign = session.query(Assignment).filter(Assignment.id == assign_id).first()
        tests = session.query(Test).filter(Test.assignment_id == assign_id).all()
        return render_template('assign.html',
                               user=user,
                               assign=assign,
                               tests=tests)
    else:
        raw_code = request.form['code-block']
        if not raw_code:
            assign = session.query(Assignment).filter(Assignment.id == assign_id).first()
            tests = session.query(Test).filter(Test.assignment_id == assign_id).all()
            return render_template('assign.html',
                               user=user,
                               assign=assign,
                               tests=tests)
        else:
            raw_code = MAIN_METHOD_HEADER + raw_code + '\n}'
            compileMethods.writeJavaFile(user, raw_code)
            results = compileMethods.compileJava(user)
            print 'here are the results:'
            print results
            post = Post(code=raw_code, user=user, assignment_id=assign_id, results=results)
            session.add(post)
            session.commit()
            return redirect(url_for('assignResults',assign_id=assign_id))


@app.route('/assignment/results/<int:assign_id>')
@authenicate
def assignResults(user,assign_id):
	assign = session.query(Assignment).filter(Assignment.id == assign_id).first()
	if user.username in ADMIN_LIST:
		posts = session.query(Post).join(Post.user).filter(Post.assignment_id == assign_id).order_by(User.name,Post.id.desc())
	else:
		posts = session.query(Post).filter(and_(Post.assignment_id == assign_id, Post.user_id == user.id)).order_by(desc(Post.id)).all()

	return render_template('assignResults.html',
                           user=user,
                           posts=posts,
                           assign=assign)


@app.route('/assignment/results')
@authenicate
def allResults(user):
    assign = session.query(Assignment).order_by(desc(Assignment.id)).all()
    return render_template('allResults.html',
                           user=user,
                           assign=assign)


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
        if user:
            hashed_password = hashlib.sha512(password + user.salt).hexdigest()
            if user.password == hashed_password:
                return setCookie(user)

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
            post_location = '%s/%s' % (POST_DIRECTORY,str(user.id))
            os.makedirs(post_location)
            return redirect(url_for('login'))
        else:
            message = 'There was a problem with your form.  Please try again.'
            return render_template('signup.html', error_email=message)


@app.route('/admin/new', methods=['GET', 'POST'])
@admin_only
def newAssign(user):
    if request.method == 'GET':
            params = {}
            return render_template('admin.html',
                                   user=user,
                                   params=params)
    else:
        params = {}
        title = request.form['title']
        descrip = request.form['desc']
        tf = request.form.get('include_testfiles')

        if title and descrip:
            assign = Assignment(name=title,
                                desc=descrip,
                                user=user)
            if tf:
            	assign.include_tf = True
            else:
            	assign.include_tf = False

            session.add(assign)
            session.commit()
            return redirect(url_for('assignView',assign_id=assign.id))
        else:
            params['title'] = title
            params['desc'] = descrip
            params['error'] = 'Please fill in both fields before continuing.'
            return render_template('admin.html',
                                   user=user,
                                   params=params)


@app.route('/admin/assignment/edit/<int:assign_id>', methods=['POST','GET'])
@admin_only
def editAssign(user, assign_id):
	assign = session.query(Assignment).filter(Assignment.id == assign_id).first()
	params = {}
	if request.method == 'GET':
		params['title'] = assign.name
		params['desc'] = assign.desc
		if assign.include_tf:
			params['tf'] = 'checked'
		else:
			params['tf'] = ''
		return render_template('admin.html',
							   user=user,
							   params=params)
	else:
		title = request.form['title']
		descrip = request.form['desc']
		include_tf = request.form.get('include_testfiles')
		if title and descrip:
			assign.name = title
			assign.desc = descrip
			if include_tf:
				assign.include_tf = True
			else:
				assign.include_tf = False
			session.commit()
			return redirect(url_for('assignView',assign_id=assign_id))
		else:
			params['title'] = title
			params['desc'] = descrip
			params['error'] = 'Please fill in both fields before continuing.'
			return render_template('admin.html',
                                   user=user,
                                   params=params)


@app.route('/admin/testfile/upload/<int:assign_id>', methods=['POST'])
@admin_only
def uploadTest(user, assign_id):    
    if request.method == 'POST':
        file = request.files['test_file']
        name = request.form['name']
        if not name or not file or not allowed_file(file.filename):
            print 'error found'
            return redirect(url_for('assignView',assign_id=assign_id))

        directory = ASSIGN_FILE_PATH + secure_filename(str(assign_id))
        if not os.path.exists(directory):
            os.makedirs(directory)
        filename = secure_filename(file.filename)
        full_path = directory+'/'+filename
        if os.path.exists(full_path):
            print 'file already exists'
            return redirect(url_for('assignView', assign_id=assign_id))
        file.save(os.path.join(directory, filename))
        test = Test(name=name,
                    location=full_path,
                    assignment_id=assign_id,
                    user=user)
        session.add(test)
        session.commit()
        return redirect(url_for('assignView', assign_id=assign_id))


@app.route('/admin/assignment/delete/<int:assign_id>', methods=['GET', 'POST'])
@admin_only
def deleteAssign(user, assign_id):
    assign = session.query(Assignment).filter(Assignment.id == assign_id).first()
    if request.method == 'GET':
        if assign:
            return render_template('deleteAssign.html',
                                   user=user,
                                   assign=assign)
    else:
        if assign:
            tests = session.query(Test).filter(Test.assignment_id == assign_id).all()
            for t in tests:
                session.delete(t)
            if os.path.exists(ASSIGN_FILE_PATH + str(assign.id)+'/'):
                shutil.rmtree(ASSIGN_FILE_PATH + str(assign.id)+'/')
            session.delete(assign)
            session.commit()
        return redirect(url_for('main'))


@app.route('/admin/testfile/delete/<int:testfile_id>', methods=['POST'])
@admin_only
def deleteTestfile(user, testfile_id):
    if request.method == 'POST':
        file = session.query(Test).filter(Test.id == testfile_id).first()
        assign_id = file.assignment_id
        directory = file.location
        print directory
        os.remove(directory)
        session.delete(file)
        session.commit()
        return redirect(url_for('assignView',assign_id=assign_id))


@app.route('/all')
@authenicate
def all(user):
    users = session.query(User).all()
    assign = session.query(Assignment).all()
    posts = session.query(Post).all()
    tests = session.query(Test).all()

    return render_template('all.html',
                           users=users,
                           posts=posts,
                           assign=assign,
                           tests=tests,
                           user=user)





if __name__ == '__main__':
    app.secret_key = 'something'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)

