#!/usr/bin/env python3

# Core python modules
import os
import logging

# Processing modules
import pandas as pd
import numpy as np
from difflib import SequenceMatcher

# External modules
from listing import Listing
from session import GoogleCalAPI


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
handler.setFormatter(logging.Formatter('%(asctime)s - Events: %(levelname)s - %(message)s', "%I:%M:%S"))
logger.addHandler(handler)


similarity = lambda a,b: SequenceMatcher(None, a, b).ratio()


class Events(): 

	def __init__(self, list_id, calendar_name): 

		self.local_dir     = '../listings/'
		self.manifest_path = os.path.join(self.local_dir, list_id, 'manifest.txt')
		self.urls_path     = os.path.join(self.local_dir, list_id, 'urls.txt')

		self.cal_name = calendar_name

		self.manifest = self._read_manifest()
		self.urls     = self._get_urls()

		self.new_urls = self._get_new_paths()

		self.service = None


	###### READ / WRITE ######

	def _get_urls(self): 

		with open(os.path.join(self.urls_path), 'r') as f: 
			return [line.rstrip() for line in f.readlines()]


	def _read_manifest(self): 

		if os.path.exists(self.manifest_path): 
			return pd.read_csv(self.manifest_path, sep='\t')
		else: 
			return pd.DataFrame([], columns=['description', 'message', 'event_id', 'is_correction', 'is_talk'])


	def _get_new_paths(self): 

		old_urls = self.manifest['description'].tolist() # description = url
		new_urls = [url for url in self.urls if url not in old_urls]

		return new_urls


	def _save_manifest(self): 
		
		self.manifest.to_csv(self.manifest_path, sep='\t', index=False)


	###### MANIFEST OPERATIONS ######

	def update_manifest(self): 

		# First sort new listings by posted date in chronological order
		new_listings = []
		for url in self.new_urls: 

			list_id = url.split('/')[-3]
			index = url.split('/')[-1]

			l = Listing(list_id, index)

			new_listings.append([l.posted_time, l])

		new_listings.sort(key=lambda x: x[0])

		# Then loop through listings and add to manifest
		for _, l in new_listings: 
			# TODO: replace -30 with something better
			metadata = self.get_listing_metadata(self.manifest[-30:], l)

			# If new listing is a talk and contains relevant metadata, check if it's a new one OR a corrected listing
			if metadata['is_talk'] and 'start' in metadata:
				if metadata['event_id'] == self.manifest['event_id'].max()+1 or metadata['is_correction'] or len(self.manifest) == 0: 

					self.push_to_google_calendar(metadata)
					metadata['pushed_to_cal'] = True
					self._save_manifest()

			self.manifest = self.manifest.append(metadata, ignore_index=True)
			logger.info("Added to manifest: " + l.url)


	def get_listing_metadata(self, previous_listing_rows, current_listing): 

		# Get metadata for new listing
		metadata = current_listing.get_parsed_metadata_dense()

		# Assign event_id based on similarity to event 
		for _,prev_l in previous_listing_rows.iterrows(): 
			s = similarity(prev_l['message'], metadata['message'])

			if s > 0.5: 
				metadata['event_id'] = prev_l['event_id']

			if prev_l['is_correction'] and s > 0.3: 
				metadata['event_id'] = prev_l['event_id']

		# Special case to handle if manifest does not exist
		if len(self.manifest) == 0: 
			metadata['event_id'] = 0
		else: 
			metadata['event_id'] = max(self.manifest['event_id']) + 1

		return metadata


	###### CALENDAR OPERATIONS ######

	def push_to_google_calendar(self, metadata): 

		if self.service == None: 
			self.service = GoogleCalAPI()

		self.service.create_event(self.cal_name, metadata)

