import requests
import json

from providers.base import CostItem

auth_endpoint = 'https://login.microsoftonline.com/{tenant_id}/oauth2/token'
usage_endpoint = 'https://management.azure.com/subscriptions/{subscriptionId}/providers/Microsoft.Consumption/usageDetails'
period_endpoint = 'https://management.azure.com/subscriptions/{subscriptionId}/providers/Microsoft.Billing/billingPeriods?api-version=2017-04-24-preview'

def cost(account_name, password, subscription, client_id, tenant_id) -> "list[CostItem]":

    # Build payload for authentication 
    data = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': password,
        'resource': 'https://management.azure.com/',
    }

    # Do the auth, grab the token
    x = requests.post(auth_endpoint.format(tenant_id=tenant_id), data=data)
    token = json.loads(x.text)['access_token']

    # Headers
    headers = {
        'Authorization': f'Bearer {token}'
    }

    # Parameters for the initial request
    params = {
        # Microsoft, thats all I have to say
        'api-version': '2021-10-01',
        # This is required to get information for the current billing period
        '$expand': 'properties/meterDetails',
    }

    # This is the initial request, you could just manually append the parameters to the URL but this is easier to change
    # We're just building the URL and makes looping later cleaner
    p = requests.Request('GET', usage_endpoint.format(subscriptionId=subscription), params=params).prepare()
    next_url = p.url
    
    startDate = None
    endDate = None

    total = 0
    # We loop here to handle pagination
    while next_url is not None:
        # We already appended the parameters above
        x = requests.get(next_url, headers=headers)
        js = json.loads(x.text)

        # Loop through the returned itemized JSON and total
        [total := total + i['properties']['paygCostInUSD'] for i in js['value']]
        
        # If we haven't grabbed the billing start and end dates do so now
        if startDate is None:
            startDate = js['value'][0]['properties']['servicePeriodStartDate']
            endDate = js['value'][0]['properties']['servicePeriodEndDate']

        # Check if there is another page
        if 'nextLink' in js.keys():
            # Yep, make this the request
            next_url = js['nextLink']
        else:
            # Nope break the loop
            break

    # Return a list of namedtuple CostItem()
    ret = [
        CostItem(total, startDate, endDate),
    ]
    return ret