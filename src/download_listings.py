#!/usr/bin/env python3

# Core python modules
import os

# Web scraping modules
from session import Session


class ListServe(): 

	def __init__(self, list_id, local_listing_dir='../listings/'): 

		self.list_id  = list_id

		self.local_dir	     = os.path.join(local_listing_dir, self.list_id)
		self.local_urls_path = os.path.join(self.local_dir, 'urls.txt')

		self.local_urls = self.get_local_manifest()

		self.s = Session(self.list_id)


	####################################
	#####     UPDATE FUNCTIONS     #####
	####################################

	def update_local_dir(self): 
		# Find new listings and save them locally
		urls = self.get_new_listings()

		for url in urls: 
			self.save_listing(url) 
			self.local_urls.append(url)

		# Update url manifest
		self.update_manifest()
		print("{} new listings added.".format(len(urls)))

	
	def get_new_listings(self): 

		# Request home
		home_url = os.path.join("http://mailman.mit.edu/mailman/private/", self.list_id)
		home_html = self.s.get_html(home_url)

		# Get batch URLs (by date)
		batch_urls = [os.path.join(home_url, subpage.get('href')) for subpage in home_html.body.table.find_all(href=True) if 'date' in subpage.get('href')]

		# Get all listing URLs
		urls = []
		for batch_url in batch_urls: 
			# For each batch, obtain listing indices
			batch_html = self.s.get_html(batch_url) 
			indices = [subpage.get('href') for subpage in batch_html.body.find_all('ul')[1].find_all(href=True)]

			# For each listing index, record full URL
			for index in indices[::-1]: 
				url = os.path.join(os.path.dirname(batch_url), index)
				if url not in self.local_urls: 
					urls.append(url)
				else: 
					return urls

		return urls


	################################
	#####     READ / WRITE     #####
	################################

	def get_local_manifest(self): 

		# Check if local directory exists, create if not.
		if os.path.isdir(self.local_dir): 
			if os.path.isfile(self.local_urls_path): 
				with open(self.local_urls_path, 'r') as f: 
					return [x.rstrip() for x in f.readlines()]
		else: 
			os.makedirs(self.local_dir)

		return []

	def update_manifest(self): 

		with open(self.local_urls_path, 'w') as f: 
			f.write('\n'.join(self.local_urls))


	def save_listing(self, url): 

		index = os.path.basename(url)
		local_path = os.path.join(self.local_dir, index)

		with open(local_path, 'w') as f: 
			f.write(str(self.s.get_html(url)))
			print("New listing found and written to: "+local_path)


def main(): 

	list_serves = [ 'mitml', 'bestudents' ]

	for list_id in list_serves: 

		l = ListServe(list_id)
		l.update_local_dir()


if __name__ == "__main__":
	main()