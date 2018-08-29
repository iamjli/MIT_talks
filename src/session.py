#!/usr/bin/env python3

# Core python modules
import os
import logging

# Peripheral python modules
import pickle

# Web scraping modules
import json
import requests
from bs4 import BeautifulSoup

# Google API modules
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
handler.setFormatter(logging.Formatter('%(asctime)s - Session: %(levelname)s - %(message)s', "%I:%M:%S"))
logger.addHandler(handler)


class Session(): 

	def __init__(self, list_id, login='../credentials/MIT_login.json'):

		self.list_id = list_id
		self.cookies_path = '../credentials/cookies.{}.pkl'.format(self.list_id)

		# Import login data
		self.login_data = json.load(open(login))

		# Try reopenning session with cookies, otherwise open new session
		try: 
			self.session = self._load_session()
		except: 
			self.session = self._init_login()
			self._save_session()

		
	def _init_login(self): 
		# First login to obtain cookies
		session = requests.session()
		session.post("http://mailman.mit.edu/mailman/private/{}/".format(self.list_id), self.login_data) 

		return session


	def _save_session(self): 
		# Save session cookies
		with open(self.cookies_path, 'wb') as f: 
			pickle.dump(requests.utils.dict_from_cookiejar(self.session.cookies), f)

			logger.info("Session cookies saved to: "+self.cookies_path)


	def _load_session(self): 
		# Load session from cookies
		with open(self.cookies_path, 'rb') as f: 
			session = requests.session()
			session.cookies = requests.utils.cookiejar_from_dict(pickle.load(f))

			logger.info("Session cookies loaded from: "+self.cookies_path)

		return session


	def get_html(self, url): 
		# Return HRML for a given URL
		response = self.session.post(url)
		return BeautifulSoup(response.text, 'html.parser')


class GoogleCalAPI(): 

	def __init__(self): 

		self.service = self._get_service()

		self.calendar_list = self.get_calendar_list()


	def _get_service(self): 

		# Setup the Gmail API
		SCOPES = 'https://www.googleapis.com/auth/calendar'

		store = file.Storage('../credentials/credentials.json')
		creds = store.get()
		if not creds or creds.invalid:
			flow = client.flow_from_clientsecrets('../credentials/client_secret.json', SCOPES)
			creds = tools.run_flow(flow, store)

		service = build('calendar', 'v3', http=creds.authorize(Http()))

		return service


	###### CALENDAR OPERATIONS #######
	def get_calendar_list(self): 

		return self.service.calendarList().list().execute().get('items')


	def get_calendar_ID(self, calendar_name): 
		# Get first instance of matching calendar name, or create new calendar if it does not exist
		results = [ cal['id'] for cal in self.calendar_list if cal.get('summary') == calendar_name ]

		if len(results) > 0: return results[0]
		else: return self.create_calendar(calendar_name)


	def create_calendar(self, calendar_name): 

		calendar = {
			'summary': calendar_name,
			'timeZone': 'America/New_York'
		}

		# Create new calendar and update calendar list
		created_calendar = self.service.calendars().insert(body=calendar).execute()
		self.calendar_list = self.get_calendar_list()

		logger.info("{} calendar created: {}".format(calendar_name, created_calendar['id']))

		return created_calendar['id']


	####### EVENT OPERATIONS #######

	def create_event(self, calendar_name, metadata): 

		calendar_ID = self.get_calendar_ID(calendar_name)

		event = self.service.events().insert(calendarId=calendar_ID, body=metadata).execute()
		logger.info('Event created: %s' % (event.get('htmlLink')))

		return event


	def edit_event(self): 

		pass


	def delete_event(self): 

		pass











