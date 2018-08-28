#!/usr/bin/env python3

# Core python modules
import os

# Peripheral python modules
import pickle

# Web scraping modules
import json
import requests
from bs4 import BeautifulSoup


MIT_LOGIN_PATH = '../credentials/MIT_login.json'

class Session(): 

	def __init__(self, session_ID):

		self.session_ID = session_ID
		self.cookies_path = '../credentials/cookies.{}.pkl'.format(self.session_ID)

		# Import login data
		self.login_data = json.load(open(MIT_LOGIN_PATH))

		# Try reopenning session with cookies, otherwise open new session
		try: 
			self.session = self._load_session()
		except: 
			self.session = self._init_login()
			self._save_session()

		
	def _init_login(self): 
		# First login to obtain cookies
		session = requests.session()
		session.post("http://mailman.mit.edu/mailman/private/{}/".format(self.session_ID), self.login_data) 

		return session


	def _save_session(self): 
		# Save session cookies
		with open(self.cookies_path, 'wb') as f: 
			pickle.dump(requests.utils.dict_from_cookiejar(self.session.cookies), f)

			print("Session cookies saved to: "+self.cookies_path)


	def _load_session(self): 
		# Load session from cookies
		with open(self.cookies_path, 'rb') as f: 
			session = requests.session()
			session.cookies = requests.utils.cookiejar_from_dict(pickle.load(f))

			print("Session cookies loaded from: "+self.cookies_path)

		return session


	def get_html(self, url): 
		# Return HRML for a given URL
		response = self.session.post(url)
		return BeautifulSoup(response.text, 'html.parser')