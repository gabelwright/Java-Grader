from flask import Flask, make_response, jsonify, request, abort
import compileMethods
import hashlib

app = Flask(__name__)

# FILE_DIRECTORY = '/vagrant/static/posts'
FILE_DIRECTORY = '/var/www/java_api/java_api/static/posts'

hash_secret = ''

@app.route("/", methods=['GET'])
def hello():
    return make_response(jsonify({'status': 'Working'}), 200)


@app.route("/run", methods=['POST'])
def run():
	user = request.form.get('user')
	code = request.form.get('code')
	auth = request.form.get('auth')
	if not user or not code:
		return make_response(jsonify({'exit_code': None,'result':None}), 400)
	if not auth or auth != hashlib.sha512(hash_secret+user).hexdigest():
		return make_response(jsonify({'exit_code': None,'result':None}), 401)
	compileMethods.writeJavaFile(user,code)
	output = compileMethods.compileJava(user)
	return make_response(jsonify({'exit_code': output[0],'result':output[1]}), 200)


if __name__ == "__main__":
    app.secret_key = 'something'
    app.debug = False
    app.run(host='0.0.0.0', port=5000)