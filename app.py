#!/usr/bin/env python
import sys
from flask import Flask, jsonify, abort, request, make_response, session
from flask_restful import reqparse, Resource, Api
from flask_session import Session
import MySQLdb
import json
import ldap
import ssl
import settings # Our server and db settings, stored in settings.py

app = Flask(__name__)
reload(sys)
sys.setdefaultencoding('utf-8')

app.secret_key = settings.SECRET_KEY
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_COOKIE_NAME'] = 'Chocolate'
app.config['SESSION_COOKIE_DOMAIN'] = settings.APP_HOST
Session(app)

# Error handlers
@app.errorhandler(400) # decorators to add to 400 response
def not_found(error):
	return make_response(jsonify( { 'status': 'Bad request' } ), 400)

@app.errorhandler(404) # decorators to add to 404 response
def not_found(error):
	return make_response(jsonify( { 'status': 'Resource not found' } ), 404)

class SignIn(Resource):
	def post(self):

		if not request.json:
			abort(400) # bad request

		# Parse the json
		parser = reqparse.RequestParser()
 		try:
 			# Check for required attributes in json document, create a dictionary
	 		parser.add_argument('username', type=str, required=True)
			parser.add_argument('password', type=str, required=True)
			#tempUser = 'username'
			request_params = parser.parse_args()
		except:
			abort(400) # bad request

		if request_params['username'] in session:
			response = {'status': 'success'}
			responseCode = 200
			#tempUser = 'username'
		else:
			try:
				l = ldap.open(settings.LDAP_HOST)
				l.start_tls_s()
				l.simple_bind_s("uid="+request_params['username']+
					", ou=People,ou=fcs,o=unb", request_params['password'])
				# At this point we have sucessfully authenticated.

				session['username'] = request_params['username']
				response = {'status': 'success' }
				#tempUser = session['username']
				responseCode = 201
			except ldap.LDAPError, error_message:
				response = {'status': 'Access denied'}
				responseCode = 403
			finally:
				l.unbind()

		return make_response(jsonify(response), responseCode)

	def get(self):
		success = False
		if 'username' in session:
			response = {'status': 'success'}
			responseCode = 200
		else:
			response = {'status': 'fail'}
			responseCode = 403

		return make_response(jsonify(response), responseCode)

class songs(Resource):
	# GET: Return all songs
	def get(self):
		try:
			connection = MySQLdb.connect(host=settings.MYSQL_HOST,user=settings.MYSQL_USER,passwd=settings.MYSQL_PASSWD,db=settings.MYSQL_DB, use_unicode=True, charset='utf8')
			cursor = connection.cursor()

			cursor.callproc('getSongs') # stored procedure, no arguments

			rows = cursor.fetchall()# get all the results

			field_names = [i[0] for i in cursor.description]
			set = [
				{description: value for description, value in zip(field_names, row)}
				for row in rows]
		except:
			abort(500) # Nondescript server error

		cursor.close()
		connection.close()
		return make_response(jsonify({'songs': set}), 200) # turn set into json and return it

	def post(self):
	# curl -i -H "Content-Type: application/json" -X POST
	#    -d '{"songTitle": "abc", "youTubeURL": "link", "userID":"mike"}'
	#         http://info3103.cs.unb.ca:43426/songs

		if not request.json or not 'songTitle' in request.json:
			abort(400) # bad request

		# Pull the results out of the json request
		#cSongID = request.json['songID'];
		cSongTitle = request.json['songTitle'];
		cYouTubeURL = request.json['youTubeURL'];
		cUserID = request.json['userID'];

		try:
			connection = MySQLdb.connect(host=settings.MYSQL_HOST,user=settings.MYSQL_USER,passwd=settings.MYSQL_PASSWD,db=settings.MYSQL_DB, use_unicode=True, charset='utf8')
			cursor = connection.cursor()

			cursor.callproc('createSong', (cSongTitle, cYouTubeURL, cUserID)) # stored procedure, with arguments
			connection.commit() # database was modified, commit the changes
		except:
			abort(500) # Nondescript server error

		cursor.close()
		connection.close()
		return make_response(jsonify( { 'status': 'success' } ), 201) # successful resource creation

class songResource(Resource):
	#GET: Return identified song
	def get(self, songID):
		try:
			connection = MySQLdb.connect(host=settings.MYSQL_HOST,user=settings.MYSQL_USER,passwd=settings.MYSQL_PASSWD,db=settings.MYSQL_DB, use_unicode=True, charset='utf8')
			cursor = connection.cursor(MySQLdb.cursors.DictCursor)

			cursor.callproc('getSong',[songID]) # stored procedure, with argument
			row = cursor.fetchone() # Should only be one result
		except:
		# 	Things messed up
			abort(404) # Resource not found

		cursor.close()
		connection.close()
		return make_response(jsonify({'songs': row}), 200) # successful

	#DELETE: Delete a song specified by the ID
	def delete(self, songID):
		try:
			connection = MySQLdb.connect(host=settings.MYSQL_HOST,user=settings.MYSQL_USER,passwd=settings.MYSQL_PASSWD,db=settings.MYSQL_DB, use_unicode=True, charset='utf8')
			cursor = connection.cursor(MySQLdb.cursors.DictCursor)

			#cSongID = request.json['songID'];

			cursor.callproc('deleteSong',(songID)) # stored procedure, with argument
			#row = cursor.fetchone() # Should only be one result
		except:
		# 	Things messed up
			abort(404) # Resource not found

		cursor.close()
		connection.close()
		return make_response(jsonify({'songs': row}), 204) # successful

############################################################################################

# Identify/create endpoints and endpoint objects
api = Api(app)
api.add_resource(SignIn, '/signin')
api.add_resource(songs, '/signin/songs')
api.add_resource(songResource, '/signin/songs/{int:songID}')

if __name__ == "__main__":
	context = ('cert.pem', 'key.pem') # Identify the certificates you've generated.
    	app.run(host=settings.APP_HOST, port=settings.APP_PORT, debug=settings.APP_DEBUG, ssl_context=context)
