#!/usr/bin/env python3

# Core python modules
import os
import logging

# External modules
from download_listings import ListServe
from events import Events


LIST_SERVES = [ 'mitml', 'bestudents', 'stat-events']


def main(): 

	for list_id in LIST_SERVES: 

		# Download any new listings
		l = ListServe(list_id)
		l.update_local_dir()

		e = Events(list_id, list_id)
		e.update_manifest()


if __name__ == "__main__":
	main()