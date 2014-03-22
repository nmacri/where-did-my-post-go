class etl_controller(object):
	"""ETL Routines for collecting and storing reblog graphs"""
	def __init__(self):
		import json
		import os
		import urllib

		import mysql.connector
		import pytumblr

		# Auth credentials are stored in secrets.json
		secrets_file = open('secrets.json','rb')
		secrets = json.load(secrets_file)
		secrets_file.close()

		# Build an Authorized Tumblr Client
		self.tumblr_client = pytumblr.TumblrRestClient(**secrets['tumblr_tokens'])

		# Build an Authorized Database Connection
		self.mysql_connection = mysql.connector.connect(**secrets['mysql'])