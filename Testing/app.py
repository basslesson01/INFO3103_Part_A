#!/usr/bin/env python
import sys
from flask import Flask, jsonify, abort, request, make_response
from flask_restful import Resource, Api
import MySQLdb
import json

import settings # Our server and db settings, stored in settings.py

app = Flask(__name__)
reload(sys)
sys.setdefaultencoding('utf-8')

# Error handlers
@app.errorhandler(400) # decorators to add to 400 response
def not_found(error):
	return make_response(jsonify( { 'status': 'Bad request' } ), 400)

@app.errorhandler(404) # decorators to add to 404 response
def not_found(error):
	return make_response(jsonify( { 'status': 'Resource not found' } ), 404)

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
	#    -d '{"Name": "abc", "Province": "NB", "Language":
	#		  "EN", "Level": "simple"}'
	#         http://info3103.cs.unb.ca:xxxxx/schools

		if not request.json or not 'songTitle' in request.json:
			abort(400) # bad request

		# Pull the results out of the json request
		#cSongID = request.json['songID'];
		cSongTitle = request.json['songTitle'];
		cYouTubeURL = request.json['youTubeURL'];

		try:
			connection = MySQLdb.connect(host=settings.MYSQL_HOST,user=settings.MYSQL_USER,passwd=settings.MYSQL_PASSWD,db=settings.MYSQL_DB, use_unicode=True, charset='utf8')
			cursor = connection.cursor()

			cursor.callproc('createSong', (cSongTitle, cYouTubeURL)) # stored procedure, with arguments
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

# Identify/create endpoints and endpoint objects
api = Api(app)
api.add_resource(songs, '/songs')
api.add_resource(songResource, '/songs/<int:songID>')

if __name__ == "__main__":
    app.run(host=settings.APP_HOST, port=settings.APP_PORT, debug=settings.APP_DEBUG)
