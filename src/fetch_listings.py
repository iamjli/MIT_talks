#!/usr/bin/env python3

# Core python modules
import os

# Web scraping modules
from session import Session


list_id = "mitml"
base_url = "http://mailman.mit.edu/mailman/private/"
local_dir = '../listings/'


def main(): 

	# Initialize session
	s = Session()

	# Request home
	home_url = os.path.join(base_url, list_id)
	home_html = s.get_html(home_url)

	# Get batch URLs (by date)
	batch_urls = [os.path.join(home_url, subpage.get('href')) for subpage in home_html.body.table.find_all(href=True) if 'date' in subpage.get('href')]

	# Get all listing URLs
	urls = []
	for batch_url in batch_urls: 
		# For each batch, obtain listing indices
		batch_html = s.get_html(batch_url) 
		indices = [subpage.get('href') for subpage in batch_html.body.find_all('ul')[1].find_all(href=True)]

		# For each listing index, record full URL
		for index in indices[::-1]: 
			url = os.path.join(os.path.dirname(batch_url), index)
			urls.append(url)

	# If index does not exist locally, save html
	for url in urls: 

		index = os.path.basename(url)
		local_path = os.path.join(local_dir, list_id, index)

		if not os.path.isfile(local_path): 
			with open(local_path, 'w') as f: 
				f.write(str(s.get_html(url)))
				print("New listing found and written to: "+local_path)

	# Save all URLs 
	with open(os.path.join(local_dir, list_id, 'urls.txt'), 'w') as f: 
		f.write('\n'.join(urls))


if __name__ == "__main__": 
	main()
