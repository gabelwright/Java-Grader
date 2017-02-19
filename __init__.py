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
import ast


app = Flask(__name__)

# engine = create_engine('postgresql://db:dbpass@localhost/db')
engine = create_engine('sqlite:///codin-site.db')
Base.metadata.bind = engine
DBsession = sessionmaker(bind=engine)
session = DBsession()

# ASSIGN_FILE_PATH = '/var/www/java_grader/java_grader/static/assignments/'
# POST_DIRECTORY = '/var/www/java_grader/java_grader/static/posts'

ASSIGN_FILE_PATH = '/vagrant/static/assignments/'
POST_DIRECTORY = '/vagrant/static/posts'

MAIN_METHOD_HEADER = 'public class CodinBlog{\n\n'
TEST_CODE_HEADER = '''
public class CodinBlog{\n
public static void main(String[] args){\n
'''

hash_salt = json.loads(
    open('hash_codes.json', 'r').read())['keys']['cookie_salt']
api_salt = json.loads(
    open('hash_codes.json', 'r').read())['keys']['api_salt']


def hash_cookie(user):
    hash_text = hashlib.sha512(user.username + hash_salt).hexdigest()
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
        if hashlib.sha512(params[0] + hash_salt).hexdigest() == params[1]:
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
        if not user or not user.admin:
            return abort(403)
        return f(user,*args, **kwargs)
    return wrapper


def make_salt():
    salt = ''.join(random.choice(
        string.ascii_uppercase + string.digits) for x in xrange(7))
    return salt


def java_api_call(user,raw_code):
    payload = {}
    payload['user'] = str(user)
    payload['code'] = raw_code
    payload['auth'] = hashlib.sha512(api_salt+payload['user']).hexdigest()
    url = 'http://104.236.77.41/run'

    res = requests.post(url, data=payload)
    data = {}
    if res.status_code == 200:
    	data = ast.literal_eval(res.text)
    data['status_code'] = res.status_code
    return data


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
    assign = session.query(Assignment).filter(Assignment.id == assign_id).first()
    tests = session.query(Test).filter(Test.assignment_id == assign_id).all()
    if request.method == 'GET':
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
            if assign.int_type == 0:
                raw_code = MAIN_METHOD_HEADER + raw_code + '\n}'
                data = java_api_call(user.username,raw_code)
            elif assign.int_type == 1:
                for t in tests:
                    c_code = t.test_code + raw_code + '\n}'
                    data = java_api_call(user.username,c_code)
                    data['result'] += '\n'
            elif assign.int_type == 2:
                for t in tests:
                    c_code = t.test_code + '\n}' + raw_code
                    data = java_api_call(user.username,c_code)
                    data['result'] += '\n'
            if data['status_code'] != 200:
                data['result'] = 'Status code {0}. Please try again later.  If this continues to happen, please notify your instructor.'.format(data['status_code'])
            else:
	            if data['exit_code'] == 0:
	                print "Exit code: 0"
	            elif data['exit_code'] == 124:
	                data['result'] += '\nMethod took too much time to complete and was terminated early.'
	            else:
	                data['result'] += '\nAn error was found in your code.  Please double check it before resubmitting.'
            post = Post(code=raw_code, user=user, assignment_id=assign_id, results=data['result'])
            session.add(post)
            session.commit()
            return redirect(url_for('assignResultsReview',post_id=post.id))


@app.route('/assignment/review/<int:post_id>', methods=['GET', 'POST'])
@authenicate
def assignResultsReview(user,post_id):
    post = session.query(Post).filter(post_id == Post.id).first()
    assign = session.query(Assignment).filter(Assignment.id == post.assignment_id).first()
    if post.user_id != user.id and user.username not in ADMIN_LIST :
            return abort(403)
    if request.method == 'GET':
        
        return render_template('assignReviewResults.html',
                                assign=assign,
                                post=post)
    else:
        session.delete(post)
        session.commit()
        return redirect(url_for('assignView',assign_id=assign.id))


@app.route('/assignment/results/<int:assign_id>')
@authenicate
def assignResults(user,assign_id):
    assign = session.query(Assignment).filter(Assignment.id == assign_id).first()
    if user.admin:
        posts = session.query(Post).join(Post.user).filter(Post.assignment_id == assign_id).order_by(User.l_name,Post.id.desc())
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
        f_name = request.form['f_name']
        l_name = request.form['l_name']
        username = request.form['username'].strip()
        password = request.form['password']
        verify = request.form['verify']
        email = request.form['email']
        userQuery = session.query(User).filter(User.username == username).first()

        if f_name and l_name and username and email and password and password == verify and not userQuery:
            salt = make_salt()
            hashed_password = hashlib.sha512(password + salt).hexdigest()
            user = User(f_name=f_name,
                        l_name=l_name,
                        email=email,
                        username=username,
                        password=hashed_password,
                        salt=salt,
                        admin=False)
            session.add(user)
            session.commit()
            if(user.id == 1):
                user.admin = True
                session.commit()
            else:
                post_location = '%s/%s' % (POST_DIRECTORY,str(user.id))
                os.makedirs(post_location)
            return redirect(url_for('login'))
        else:
            message = 'There was a problem with your form.  Please try again.'
            return render_template('signup.html', error_email=message)


@app.route('/admin/assignment/new', methods=['GET', 'POST'])
@admin_only
def newAssign(user):
    if request.method == 'GET':
            params = {}
            return render_template('admin.html',
                                   user=user,
                                   params=params)
    else:
        params = {}
        title = request.form['title'].replace(' ','')
        descrip = request.form['desc']
        assign_type = request.form['assign_type']
        print 'here is the assign type'
        print assign_type

        if title and descrip:
            assign = Assignment(name=title,
                                desc=descrip,
                                int_type=assign_type,
                                user=user)

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
        return render_template('admin.html',
                               user=user,
                               params=params)
    else:
        title = request.form['title']
        descrip = request.form['desc']
        assign_type = request.form['assign_type']
        include_tf = request.form.get('include_testfiles')
        if title and descrip:
            assign.name = title
            assign.desc = descrip
            assign.int_type = assign_type
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


@app.route('/admin/test/add/<int:assign_id>', methods=['POST'])
@admin_only
def addTest(user, assign_id):    
    if request.method == 'POST':
        title = request.form['title']
        test_code = request.form['test_code']
        if not title or not test_code:
            assign = session.query(Assignment).filter(assign_id == Assignment.id).first()
            return redirect(url_for('assignView',
                                   assign_id=assign_id))
        else:
            test_code = TEST_CODE_HEADER + test_code + '\n}'
            test = Test(name=title,
                        test_code=test_code,
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


@app.route('/admin/test/delete/<int:test_id>', methods=['POST'])
@admin_only
def deleteTest(user, test_id):
    if request.method == 'POST':
        test = session.query(Test).filter(Test.id == test_id).first()
        assign_id = test.assignment_id
        session.delete(test)
        session.commit()
        return redirect(url_for('assignView',assign_id=assign_id))


@app.route('/admin/test/<int:test_id>', methods=['GET','POST'])
@admin_only
def testView(user, test_id):
    test = session.query(Test).filter(Test.id == test_id).first()
    if request.method == 'GET':
        assign = session.query(Assignment).filter(Assignment.id == test.assignment_id).first()
        return render_template('testView.html',
                               test=test,
                               user=user,
                               assign=assign)


@app.route('/admin/reset', methods=['GET','POST'])
@admin_only
def resetPassword(user):
	if request.method == 'GET':
		return render_template('resetPass.html',
							   user=user)
	else:
		username = request.form['username']
		password = request.form['password']
		if not username or not password:
			status_message = 'Both fields are required.'
			return render_template('resetPass.html',
								   status_message=status_message,
								   user=user)
		user = session.query(User).filter(User.username == username).first()
		if not user:
			status_message = 'User could not be found. Please verify their username and try again.'
			return render_template('resetPass.html',
								   status_message=status_message,
								   user=user)
		salt = make_salt()
		user.salt = salt
		user.password = hashlib.sha512(password + salt).hexdigest()
		session.commit()
		status_message = 'Users password has been changed.'
		return render_template('resetPass.html',
							   status_message=status_message,
							   user=user)


@app.route('/admin', methods=['GET','POST'])
@admin_only
def adminPage(user):
	if request.method == 'GET':
		return render_template('adminPage.html',user=user)
	else:
		pass


@app.route('/all')
@admin_only
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

