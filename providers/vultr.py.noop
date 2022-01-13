import requests
import json

api_endpoint = "https://api.vultr.com/v2/billing/invoices/17249440/items"

def cost(account_name, api_key):
	# Headers for the request
	headers = {
		'Authorization':'Bearer {api_key}'.format(api_key=api_key)
	}

	x = requests.get(api_endpoint, headers=headers)

	print(json.dumps(json.loads(x.text), indent=4))
