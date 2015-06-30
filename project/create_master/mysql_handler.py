#!/usr/bin/python

import MySQLdb

# Open database connection
server = "localhost"
user = "root"
password = "tree"
database_name = "MASTER"
db = MySQLdb.connect(server, user, password, database_name)

# prepare a cursor object using cursor() method
cursor = db.cursor()

# Dict of sources and associated data scrape files
sources = {"MIT": "mit_data.csv",
		   "STANFORD": "stanford_data.csv"}

# Drop table if it already exist using execute() method.
cursor.execute("DROP TABLE IF EXISTS EMPLOYEE")

# Create table from first source
for source in sources.keys():
	create_table = "CREATE TABLE" + source + """(
	         FIRST_NAME CHAR(1) NOT NULL,
	         LAST_NAME CHAR(1) NOT NULL,
	         PREFIX CHAR(1),
	         SUFFIX CHAR(1),
	         INDUSTRY CHAR(1),
	         COMPANY CHAR(1),
	         JOB TITLE CHAR(1),
	         HOME_STREET CHAR(1),
	         HOME_CITY CHAR(1),
	         HOME_ZIPCODE CHAR(1),
	         WORK_STREET CHAR(1),
	         WORK_CITY CHAR(1),
	         WORK_ZIPCODE CHAR(1),   
	         HOME_PHONE CHAR(1),
	         MOBILE_PHONE CHAR(1),
	         WORK_PHONE CHAR(1),
	         EMAIL_ONE CHAR(1),
	         EMAIL_TWO CHAR(1),
	         EMAIL_THREE CHAR(1),
	         HOME_LAST_UPDATED DATE,
	         WORK_LAST_UPDATED DATE)"""

	cursor.execute(create_table)

# Insert data into table
for key in sources.keys():
	data_file = sources[key]
	f = open(data_file, "r")
	lines = f.readlines()
	fields = lines[0] # list of data fields
	people_data = lines[1:] #list of data associated with people scraped (one person per line)

	for person_data in people_data:
		insert_table = "INSERT TABLE" + key + "("
						  fields + ")"
						  + "(" + person_data + ")"
		cursor.execute(insert_table)

# Merge data with master table

# disconnect from server
db.close()