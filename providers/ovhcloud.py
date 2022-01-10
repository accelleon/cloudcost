import requests
import json

from providers.base import CostItem

# OVH does some unique shit like signing API requests so cave to their SDK
import ovh

def cost(account_name, endpoint, app_key, app_secret, consumer_key):
	client = ovh.Client(
		endpoint=endpoint,
		application_key=app_key,
		application_secret=app_secret,
		consumer_key=consumer_key)

	usage = client.get('/me/consumption/usage/history')

	print(json.dumps(usage, indent=4))