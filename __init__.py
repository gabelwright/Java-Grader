from flask import Flask, render_template, request, redirect, url_for, abort
from sqlalchemy import desc, and_
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from flask import session
# from flask_mail import Mail
# from flask_mail import Message
from functools import wraps
import random
import string
from db_setup import Base, User, Post, Assignment, Test
import json
import hashlib
import requests
import ast
import datetime


app = Flask(__name__)

engine = create_engine('postgresql://db:dbpass@localhost/db')
# engine = create_engine('sqlite:///codin-site.db')
Base.metadata.bind = engine
DBsession = sessionmaker(bind=engine)
session = DBsession() # noqa

onVM = True

if onVM:
    hash_salt = json.loads(
        open('hash_codes.json', 'r').read())['keys']['cookie_salt']
    api_salt = json.loads(
        open('hash_codes.json', 'r').read())['keys']['api_salt']
    flask_secret_key = json.loads(
        open('hash_codes.json', 'r').read())['keys']['secret_key']
else:
    HASH_CODE_FILE = '/var/www/java_grader/java_grader/hash_codes.json'
    hash_salt = json.loads(
        open(HASH_CODE_FILE, 'r').read())['keys']['cookie_salt']
    api_salt = json.loads(
        open(HASH_CODE_FILE, 'r').read())['keys']['api_salt']
    flask_secret_key = json.loads(
        open(HASH_CODE_FILE, 'r').read())['keys']['secret_key']

MAIN_METHOD_HEADER = 'public class CodinBlog{\n\n'
TEST_CODE_HEADER = '''
public class CodinBlog{\n
public static void main(String[] args){\n
'''


def hash_cookie(user):
    hash_text = hashlib.sha512(user.username + hash_salt).hexdigest()
    cookie_text = '%s|%s' % (user.username, hash_text)
    return cookie_text


def setCookie(user):
    cookie_value = hash_cookie(user)
    response = app.make_response(redirect(url_for('main')))
    response.set_cookie('user_id', value=cookie_value)
    return response


def check_for_user():
    cookie_value = request.cookies.get('user_id')
    if cookie_value:
        params = cookie_value.split('|')
        if hashlib.sha512(params[0] + hash_salt).hexdigest() == params[1]:
            user = session.query(User).filter(
                User.username == params[0]).first()
            if user:
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
        user = check_for_user()
        if not user:
            return redirect(url_for('login'))
        return f(user, *args, **kwargs)
    return wrapper


def admin_only(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        user = check_for_user()
        if not user or not user.admin:
            return abort(403)
        return f(user, *args, **kwargs)
    return wrapper


def make_salt():
    salt = ''.join(random.choice(
        string.ascii_uppercase + string.digits) for x in xrange(7))
    return salt


def java_api_call(user, raw_code):
    payload = {}
    payload['user'] = str(user)
    payload['code'] = raw_code
    payload['auth'] = hashlib.sha512(api_salt + payload['user']).hexdigest()
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
    if user:
        print(user.f_name)
    assign = session.query(Assignment).order_by(desc(Assignment.created)).all()
    return render_template('main.html',
                           user=user,
                           assign=assign)


@app.route('/assignment/<int:assign_id>', methods=['GET', 'POST'])
@authenicate
def assignView(user, assign_id):
    assign = session.query(Assignment).filter(
        Assignment.id == assign_id).first()
    tests = session.query(Test).filter(Test.assignment_id == assign_id).all()
    post = session.query(Post).filter(
        Post.user_id == user.id).filter(
        Post.assignment_id == assign_id).first()

    if request.method == 'GET':
        return render_template('assign.html',
                               user=user,
                               assign=assign,
                               tests=tests,
                               post=post)
    else:
        raw_code = request.form['code-block']
        if not raw_code:
            assign = session.query(Assignment).filter(
                Assignment.id == assign_id).first()
            tests = session.query(Test).filter(
                Test.assignment_id == assign_id).all()
            return render_template('assign.html',
                                   user=user,
                                   assign=assign,
                                   tests=tests)
        else:
            if assign.int_type == 0:
                c_code = MAIN_METHOD_HEADER + raw_code + '\n}'
                data = java_api_call(user.username, c_code)
            elif assign.int_type == 1:
                if not tests:
                    c_code = TEST_CODE_HEADER + '}' + raw_code + '\n}'
                    data = java_api_call(user.username, c_code)
                else:
                    for t in tests:
                        c_code = t.test_code + raw_code + '\n}'
                        data = java_api_call(user.username, c_code)
                        data['result'] += '\n'
            elif assign.int_type == 2:
                if not tests:
                    c_code = TEST_CODE_HEADER + '}\n}' + raw_code
                    data = java_api_call(user.username, c_code)
                else:
                    for t in tests:
                        c_code = t.test_code + '\n}' + raw_code
                        data = java_api_call(user.username, c_code)
                        data['result'] += '\n'
            elif assign.int_type == 3:
                data = {}
                data['result'] = 'Your post has been saved.'
                data['exit_code'] = 0
                data['status_code'] = 200
            if data['status_code'] != 200:
                data['result'] = 'Status code {0}. Please try again later. ' \
                    'If this continues to happen, please notify your ' \
                    'instructor.'.format(data['status_code'])
            else:
                if data['exit_code'] == 0:
                    pass
                elif data['exit_code'] == 124:
                    data['result'] += '\nMethod took too much time to ' \
                        'complete and was terminated early.'
                else:
                    data['result'] += '\nAn error was found in your code.\n' \
                        'Please double check it before resubmitting.\n' \
                        'Exit Code ' + str(data['exit_code'])
            if not post:
                post = Post(code=raw_code,
                            user=user,
                            assignment_id=assign_id,
                            results=data['result'],
                            notes='')
                session.add(post)
            else:
                post.code = raw_code
                post.results = data['result']
                post.created = datetime.datetime.now()
                if post.notes and '(Previous Submission)' not in post.notes:
                    post.notes = '(Previous Submission) ' + post.notes
            session.commit()
            return redirect(url_for('assignView', assign_id=assign_id))


@app.route('/assignment/review/<int:post_id>', methods=['GET', 'POST'])
@authenicate
def assignResultsReview(user, post_id):
    post = session.query(Post).filter(post_id == Post.id).first()
    assign = session.query(Assignment).filter(
        Assignment.id == post.assignment_id).first()
    if post.user_id != user.id and not user.admin:
        return abort(403)
    if request.method == 'GET':
        return render_template('assignReviewResults.html',
                               assign=assign,
                               post=post,
                               user=user)
    else:
        session.delete(post)
        session.commit()
        return redirect(url_for('assignView', assign_id=assign.id))


@app.route('/assignment/results/<int:assign_id>/<int:sort_id>')
@authenicate
def assignResults(user, assign_id, sort_id):
    assign = session.query(Assignment).filter(
        Assignment.id == assign_id).first()
    if user.admin:
        if sort_id == 0:
            posts = session.query(Post).join(Post.user).filter(
                Post.assignment_id == assign_id).order_by(
                    User.l_name, Post.created.desc())
        elif sort_id == 1:
            posts = session.query(Post).filter(
                Post.assignment_id == assign_id).order_by(Post.created.desc())
    else:
        posts = session.query(Post).filter(and_(
            Post.assignment_id == assign_id,
            Post.user_id == user.id)).order_by(desc(Post.created)).all()

    return render_template('assignResults.html',
                           user=user,
                           posts=posts,
                           assign=assign,
                           sort_id=sort_id)


@app.route('/assignment/postfeedback/<int:post_id>', methods=["POST"])
@admin_only
def postFeedback(user, post_id):
    post = session.query(Post).filter(Post.id == post_id).first()
    # form_id = 'feedback_box_%s' % post_id
    notes = request.form['data']
    print('notes', notes)
    if post:
        post.notes = notes
        session.commit()
        return notes
    else:
        print('no post')


@app.route('/assignment/results/feedback/<int:assign_id>')
@admin_only
def viewFeedback(user, assign_id):
    assign = session.query(Assignment).filter(
        Assignment.id == assign_id).first()
    posts = session.query(Post).join(Post.user).filter(
        Post.assignment_id == assign_id).order_by(
        User.l_name, Post.created.desc())
    return render_template('feedback.html',
                           user=user,
                           posts=posts,
                           assign=assign)


@app.route('/assignment/results')
@authenicate
def allResults(user):
    assign = session.query(Assignment).order_by(desc(Assignment.created)).all()
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
        params = {}
        return render_template('signup.html', params=params)
    else:
        params = {}
        params['f_name'] = request.form['f_name']
        params['l_name'] = request.form['l_name']
        params['username'] = request.form['username'].strip()
        password = request.form['password']
        verify = request.form['verify']
        params['email'] = request.form['email']

        if (not params['f_name'] or not params['l_name'] or not
                params['username']):
            params['message'] = 'Please enter your first name, last name, ' \
                'and a username.'
            return render_template('signup.html',
                                   params=params)

        userQuery = session.query(User).filter(
            User.username == params['username']).first()
        if userQuery:
            params['message'] = 'That username is already in use. ' \
                'Please choose a different one.'
            return render_template('signup.html', params=params)
        if not password:
            params['message'] = 'Please enter a valid password'
            return render_template('signup.html', params=params)
        if password != verify:
            params['message'] = 'Your passwords did not match. ' \
                'Please try again.'
            return render_template('signup.html', params=params)

        if not params['email']:
            params['message'] = 'Please enter a valid email address.'
            return render_template('signup.html', params=params)
        salt = make_salt()
        hashed_password = hashlib.sha512(password + salt).hexdigest()
        user = User(f_name=params['f_name'],
                    l_name=params['l_name'],
                    email=params['email'],
                    username=params['username'],
                    password=hashed_password,
                    salt=salt,
                    admin=False)
        session.add(user)
        session.commit()
        if(user.id == 1):
            user.admin = True
            session.commit()
        return redirect(url_for('login'))


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
        title = request.form['title'].replace(' ', '')
        descrip = request.form['desc']
        assign_type = request.form['assign_type']

        if title and descrip:
            assign = Assignment(name=title,
                                desc=descrip,
                                int_type=assign_type,
                                user=user)

            session.add(assign)
            session.commit()
            return redirect(url_for('assignView', assign_id=assign.id))
        else:
            params['title'] = title
            params['desc'] = descrip
            params['error'] = 'Please fill in both fields before continuing.'
            return render_template('admin.html',
                                   user=user,
                                   params=params)


@app.route('/admin/assignment/edit/<int:assign_id>', methods=['POST', 'GET'])
@admin_only
def editAssign(user, assign_id):
    assign = session.query(Assignment).filter(
        Assignment.id == assign_id).first()
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
            return redirect(url_for('assignView', assign_id=assign_id))
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
    assign = session.query(Assignment).filter(
        Assignment.id == assign_id).first()
    if request.method == 'GET':
        if assign:
            return render_template('deleteAssign.html',
                                   user=user,
                                   assign=assign)
    else:
        if assign:
            tests = session.query(Test).filter(
                Test.assignment_id == assign_id).all()
            posts = session.query(Post).filter(
                Post.assignment_id == assign_id).all()
            for t in tests:
                session.delete(t)
            for p in posts:
                session.delete(p)
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
        return redirect(url_for('assignView', assign_id=assign_id))


@app.route('/admin/test/<int:test_id>', methods=['GET', 'POST'])
@admin_only
def testView(user, test_id):
    test = session.query(Test).filter(Test.id == test_id).first()
    if request.method == 'GET':
        assign = session.query(Assignment).filter(
            Assignment.id == test.assignment_id).first()
        return render_template('testView.html',
                               test=test,
                               user=user,
                               assign=assign)


@app.route('/admin/reset', methods=['GET', 'POST'])
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
            status_message = 'User could not be found. ' \
                'Please verify their username and try again.'
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


@app.route('/admin/roster', methods=['GET', 'POST'])
@admin_only
def roster(user):
    if request.method == 'GET':
        users = session.query(User).filter(
            User.admin == False).order_by(User.l_name).all() # noqa
        admin = session.query(User).filter(
            User.admin).order_by(User.l_name).all()
        return render_template('roster.html',
                               user=user,
                               users=users,
                               admin=admin)
    else:
        username = request.form['username']
        user = session.query(User).filter(User.username == username).first()
        if user:
            session.delete(user)
            session.commit()
        return redirect(url_for('roster'))


@app.route('/admin/roster/delete/<int:user_id>', methods=['POST'])
@admin_only
def deleteUser(user, user_id):
    user = session.query(User).filter(User.id == user_id).first()
    posts = session.query(Post).filter(Post.user_id == user_id).all()
    if posts:
        for p in posts:
            session.delete(p)
            session.commit()
    if user:
        session.delete(user)
        session.commit()
    return redirect(url_for('roster'))


@app.route('/admin', methods=['GET', 'POST'])
@admin_only
def adminPage(user):
    if request.method == 'GET':
        return render_template('adminPage.html', user=user)
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
    app.secret_key = flask_secret_key
    app.debug = onVM
    app.run(host='0.0.0.0', port=5000)
