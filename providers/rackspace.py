import json
import requests

from providers.base import CostItem

# API Endpoints
auth_endpoint = "https://identity.api.rackspacecloud.com/v2.0/tokens"
billing_endpoint = "https://billing.api.rackspacecloud.com/v2/accounts/{ran}/estimated_charges"

# Do the cost thing
def cost(account_name, api_key, billing_number) -> "list[CostItem]":
	# Need to authenticate
	headers = {
		'Content-Type':'application/json'
	}

	# Post data, build json object
	data = json.dumps({
		'auth': {
			'RAX-KSKEY:apiKeyCredentials' : {
				'username': account_name,
				'apiKey': api_key
			}
		}
	})

	# Do the auth
	x = requests.post(auth_endpoint, headers = headers, data = data)
	js = json.loads(x.text)
	if not x.ok:
		raise Exception(f'Rackspace {account_name} auth failure: {json.dumps(js,indent=4)}')
	token = js['access']['token']['id']

	# Form the request for estimated charges
	headers = {
		'Accept':'application/json',
		'X-Auth-Token':token
	}

	# URL contains a parameter, format it and do the thing
	url = billing_endpoint.format(ran=billing_number)
	x = requests.get(url, headers= headers)
	js = json.loads(x.text)
	if not x.ok:
		raise Exception(f'Rackspace {account_name} estimated_charges failed:\n\
      		{json.dumps(js,indent=4)}')

	# This should result in estimated total for the current billing cycle
	ret = [
		CostItem(
			js['estimatedCharges']['chargeTotal'],
			js['estimatedCharges']['currentBillingPeriodStartDate'],
			js['estimatedCharges']['currentBillingPeriodEndDate']
		)
	]
	return ret