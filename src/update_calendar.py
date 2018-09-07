#!/usr/bin/env python3

# Core python modules
import os
import logging

# External modules
from download_listings import ListServe
from events import Events


LIST_SERVES = [
	{
		"host" : "http://mailman.mit.edu/mailman/private/", 
		"list_id" : "mitml"
	}, 
	{
		"host" : "http://mailman.mit.edu/mailman/private/", 
		"list_id" : "bestudents"
	}, 
	{
		"host" : "http://mailman.mit.edu/mailman/private/", 
		"list_id" : "stat-events"
	}, 
	{
		"host" : "https://lists.csail.mit.edu/pipermail/", 
		"list_id" : "seminars"
	}
]


def main(): 

	for list_serve in LIST_SERVES: 

		# Download any new listings
		l = ListServe(list_serve["list_id"], list_serve["host"])
		l.update_local_dir()

		e = Events(list_serve["list_id"], list_serve["list_id"])
		e.update_manifest()




if __name__ == "__main__":
	main()