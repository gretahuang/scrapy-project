import csv 
import fuzzy

"""
List of Fields (for reference):
FIRST_NAME,
LAST_NAME,
PREFIX,
SUFFIX,
INDUSTRY,
COMPANY,
JOB TITLE,
HOME_STREET,
HOME_CITY,
HOME_ZIPCODE,
WORK_STREET,
WORK_CITY,
WORK_ZIPCODE,   
HOME_PHONE,
MOBILE_PHONE,
WORK_PHONE,
EMAIL_ONE,
EMAIL_TWO,
EMAIL_THREE,
HOME_LAST_UPDATED DATE,
WORK_LAST_UPDATED DATE
"""

class Merger():
	def extract_data(file_names, master_data):
		for file_name in file_names:
			f = open(file_name)
			file_data = csv.reader(f)
			self.merge(file_data, master_data)

	def merge(file_data, master_data):
		file_fields = file_data[0]
		file_records = file_data[1:]
		master_fields = master_data[0]
		master_records = master_data[1:]
		for file_record in file_records:
			for master_record in master_records: # each record is an individual's data
				#calculate score
				

	def calculate_match_score(file_fields, file_record, master_fields, master_record):
		matched_fields = {}
		for field in master_fields:
			if field in file_fields:
				file_field_index = file_fields.index(field)
				master_field_index = master_fields.index(field)
				file_field_data = file_record[file_field_index]
				master_field_data = master_record[master_field_index]
				file_soundex = fuzzy.soundex(file_field_data)
				field_score = 0
				# exact match
				if file_field_data == master_field_data:
					field_score += 1
				# similar match
				if file_soundex == master_soundex:
					field_score += 0.5

				





		