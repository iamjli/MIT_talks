#!/usr/bin/env python3

# Core python modules
import os

# Peripheral python modules
import re
import pickle
from collections import Counter

import pandas as pd
import numpy as np

# Web scraping modules
import json
import requests
from bs4 import BeautifulSoup
from session import Session

# Language processing modules
from datetime import datetime, timedelta
from dateutil import parser
from sutime import SUTime


# Helper functions
flatten = lambda l: [item for sublist in l for item in sublist]

def highlight_string(text, start, end): 
	# Bolds and colors string indexed by start and end locations
	return text[:start] + '\x1b[1;31m' + text[start:end] + '\x1b[0m' + text[end:]

def get_datetime_type(text): 
	try: 
		datetime.strptime(text, '%Y-%m-%d')
		return 'date'
	except (ValueError, TypeError): pass

	try: 
		datetime.strptime(text, '%Y-%m-%dT%H:%M')
		return 'datetime'
	except (ValueError, TypeError): pass

	try: 
		datetime.strptime(text, 'T%H:%M')
		return 'time'
	except (ValueError, TypeError): pass

	if type(text) == dict and 'begin' in text and 'end' in text: 
		if get_datetime_type(text['begin']) in ['time', 'datetime'] and get_datetime_type(text['end']) in ['time', 'datetime']:
			return 'dict'

	return 'other'


# Instantiate SUTime object
jar_files = "../../packages/python-sutime/jars/"
try: sutime = SUTime(jars=jar_files, mark_time_ranges=True, include_range=True)
except OSError: sutime = SUTime(jars=jar_files, jvm_started=True, mark_time_ranges=True, include_range=True)

# MIT rooms list
with open('../listings/mit_rooms.csv', 'r') as f: 
	rooms = [line.split(' ')[0] for line in f.readlines() if '-' in line.split(' ')[0] and len(line.split(' ')[0]) < 15]
	rooms.sort(key = len, reverse=True)


class Listing(): 

	def __init__(self, list_id, index, local_lising_dir='../listings/'): 

		self.list_id = list_id
		self.index   = index

		# Set local directories
		self.local_dir  = os.path.join(local_lising_dir, self.list_id)
		self.local_path = os.path.join(self.local_dir, self.index)

		# Extract content from listing
		self.url   	 = self._get_url()
		self.html    = self._get_html()
		self.title	 = self.html.title.text.strip()
		self.message = self.html.pre.text.strip().split('-------------- next part --------------')[0]

		# Initial processing of the listing
		self.is_talk       = self._is_talk()
		# self.is_correction = self._is_correction()

		self.posted_time = parser.parse(self.html.i.text, fuzzy=True).isoformat()
		self.posted_date = self.posted_time.split("T")[0]

		self.title_mod = self._replace_month_date(self.title)
		self.message_mod = self._replace_month_date(self.message)


	###### HELPER FUNCTIONS ######

	def _get_url(self): 

		with open(os.path.join(self.local_dir, 'urls.txt'), 'r') as f: 
			urls = [line.rstrip() for line in f.readlines()]

		for url in urls: 
			if self.index in url: return url


	def _get_html(self): 

		if os.path.isfile(self.local_path): 
			with open(self.local_path, 'r') as f: 
				return BeautifulSoup(''.join(f.readlines()), 'html.parser')


	def _is_talk(self): 

		keywords = ['talk', 'seminar', 'thesis defense']

		for keyword in keywords: 
			if keyword in self.title.lower(): return True

		return False


	###### PARSE LISTING ######

	def get_parsed_metadata(self): 

		event = {} 

		title = self._remove_list_info(self.title)
		location = self.get_location()
		date, start, end = self.get_datetime_predictions()

		event['summary'] = title
		event['description'] = self.url
		if location != "NA": event['location'] = location

		if date != "NA" and start != "NA" and end != "NA": 
			event['start'] = {
				'dateTime': parser.parse('T'.join([date, start])).isoformat(), 
				'timeZone': 'America/New_York'
			}
			event['end'] = {
				'dateTime': parser.parse('T'.join([date, end])).isoformat(), 
				'timeZone': 'America/New_York'	
			}

		return event


	def get_location(self): 

		matches = []
		for room in rooms: 
			if room in self.message and room not in ' '.join([match[0] for match in matches]):
				matches.append([room, self.message.find(room)]) 
		matches.sort(key=lambda x: x[1]) 

		if len(matches) == 0: 
			return "NA" 

		return matches[0][0]


	def get_datetime_predictions(self): 

		# Get date time fragments from title and message
		self.datetime_df = self.get_datetime_dataframes()
		# Sort snippets into date and time dataframes
		dates_df, times_df = self.extract_datetime_features(self.datetime_df)

		### MODEL
		# Score each piece of evidence -- model to be learned in the future
		dates_df['score'] = dates_df['source'].apply(lambda x: 1.5 if x == 'title' else 1) * \
								 dates_df['format'].apply(lambda x: 1.5 if x == 'dict' else 1)

		times_df['score'] = times_df['source'].apply(lambda x: 1.5 if x == 'title' else 1) * \
								 times_df['format'].apply(lambda x: 1.5 if x == 'dict' else 1) * \
								 times_df['time'].apply(lambda x: 1 if x[-2:] in ['00', '15', '30', '45'] else 0.5)

		# Pick top scoring date and times
		if len(dates_df) == 0: 
			predict_date = "NA"
		else:
			predict_date = dates_df.groupby(dates_df.columns[0]).sum().sort_values('score', ascending=False).index[0]

		if len(times_df) == 0: 
			predict_start = "NA"
		else:
			predict_start = times_df.groupby(times_df.columns[0]).sum().sort_values('score', ascending=False).index[0]

		if predict_start == "NA": 
			predict_end = "NA"
		else:
			# Infer the end time from start time by setting each meeting to 1 hour default. 
			predict_end = format(datetime.strptime(predict_start, '%H:%M') + timedelta(hours=1), '%H:%M')
			# If `DURATION` exists, update end time prediction
			for dic in self.datetime_df[self.datetime_df['format'] == 'dict']['value']: 
				if self._convert_time_to_pm(dic['begin'].split('T')[1]) == predict_start: 
					predict_end = self._convert_time_to_pm(dic['end'].split('T')[1])

		return predict_date, predict_start, predict_end


	###### HELPERS FOR DATETIME PARSING ######

	def get_sutime_results_as_dataframe(self, text): 

		results = sutime.parse(text, self.posted_date)

		
		for result in results: 
			# Sometimes `2pm` can be misaligned to the posted date. In order to accommodate text that does not contain 
			# a specified date, if text length is shorter than 8, force the format to be hour:minutes. 
			if result['type'] == 'TIME' and len(result['text']) <= 8 and get_datetime_type(result['value']) == 'datetime':
				result['value'] = format(parser.parse(result['value']), 'T%H:%M')
			# Sometimes `Friday` can be misaligned to the post date. To accomodate, if parsed date is before post date, 
			# check if the following week is after the post date. If so, change it. 
			if result['type'] == 'DATE' and get_datetime_type(result['value']) == 'date' and result['value'] < self.posted_date: 
				new_date = format(parser.parse(result['value']) + timedelta(weeks=1), '%Y-%m-%d')
				if new_date >= self.posted_date: 
					result['value'] = new_date
				else: 
					result['value'] = 'XXX'
			# Datetime could feasibly be messed up too, but we'll ignore that here


		if len(results) > 0:
			results_df = pd.DataFrame(results)
			results_df = results_df[['start', 'end', 'text', 'type', 'value']]
			results_df['format'] = results_df['value'].apply(get_datetime_type)
			datetime_df = results_df[results_df['format'].isin(['datetime', 'date', 'time', 'dict'])]

			# Fix up times and dates

			return datetime_df

		return pd.DataFrame([], columns=['start', 'end', 'text', 'type', 'value', 'format'])


	def get_datetime_dataframes(self): 

		# Get information from title
		title_df = self.get_sutime_results_as_dataframe(self.title_mod)
		# If more than one date time instance, best to concatenate the two and rerun.
		if len(title_df) > 1: 
			title_df = self.get_sutime_results_as_dataframe(' '.join(title_df['text']))
		title_df['source'] = 'title'

		# Get information from message
		message_df = self.get_sutime_results_as_dataframe(self.message_mod)
		message_df['source'] = 'message'

		return pd.concat([title_df, message_df])


	def extract_datetime_features(self, datetime_df): 

		# Sort evidence into date and times
		dates = []
		times = []
		for i, row in datetime_df.iterrows(): 
			if row['format'] == 'date': dates.append([row['value'], row['source'], row['format']])
			elif row['format'] == 'datetime' or row['format'] == 'time': 
				date, time = row['value'].split('T')
				dates.append([date, row['source'], row['format']])
				times.append([self._convert_time_to_pm(time), row['source'], row['format']])
			elif row['format'] == 'dict': 
				date, time = row['value']['begin'].split('T')
				dates.append([date, row['source'], row['format']])
				times.append([self._convert_time_to_pm(time), row['source'], row['format']])
			else: pass

		dates_df = pd.DataFrame(dates, columns=['date', 'source', 'format']).replace('', np.nan).dropna()
		times_df = pd.DataFrame(times, columns=['time', 'source', 'format']).replace('', np.nan).dropna()

		return dates_df, times_df


	###### BASIC TEXT PROCESSING ######

	def highlight_text(self, text): 

		results = sutime.parse(text, self.posted_date)

		for match in results[::-1]: 
			text = highlight_string(text, match['start'], match['end'])

		print(text)


	def _remove_list_info(self, text): 

		# Remove whitespace from ends
		# TODO: remove "Fwd:" tags
		text = text.strip()
		# If text begins with left brackets, remove the first instance of enclosed text
		if text[0] in ['(', '[']: 
			text = re.sub("[\(\[].*?[\)\]]", "", text, count=1)
			# In case there are several brackets, run it again
			return self._remove_list_info(text)

		return text


	def _replace_month_date(self, text): 

		text = text.replace('--', '-')

		# SUTime has trouble parsing dates of the form `03/01` (March 1). This function finds these dates and 
		slash_indices = [i for i, ltr in enumerate(text) if ltr == '/']
		# Only include if format is not `03/01/1993`
		substrings = [text[i-2:i+3].strip() for i in slash_indices if text[i-3:i+4].count('/') == 1]

		for substring in substrings: 
			try: 
				# Replace date form with plain text date
				date_string = datetime.strptime(substring, '%m/%d').strftime('%B %d')
				text = text.replace(substring, date_string)
			except ValueError: 
				pass

		return text


	def _convert_time_to_pm(self, time): 

		if time < '08:00': 
			return format(datetime.strptime(time, '%H:%M') + timedelta(hours=12),'%H:%M')
		return time


	def __str__(self):
		return self.index

	def __repr__(self): 
		return self.__str__()
