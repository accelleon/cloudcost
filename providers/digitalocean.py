import requests
import json
from datetime import datetime
from dateutil.relativedelta import relativedelta

from providers.base import CostItem

# API endpoint
endpoint = "https://api.digitalocean.com/v2/customers/my/balance"

# Do the cost thing
def cost(account_name, api_key) -> "list[CostItem]":
	# Dictionary of headers for the request
	headers = {
		'Authorization':'Bearer {}'.format(api_key),
		'Content-Type':'application/json'
	}

	resp = requests.get(endpoint, headers=headers)
	if not resp.ok:
		raise Exception(f'API Call Failed\n{json.dumps(resp.json(),indent=4)}')
 
	# Generate our start and end dates, this is always 1st to 1st for DO
	ret = [
		CostItem(
			resp.json()['month_to_date_usage'],
			datetime.today().replace(day=1).strftime('%Y-%m-%d'),
			(datetime.today()+relativedelta(months=1, day=1)).strftime('%Y-%m-%d')
		)
	]

	return ret
