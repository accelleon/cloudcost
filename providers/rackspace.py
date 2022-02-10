import json
import requests
import csv
import codecs
from datetime import datetime

from providers.base import CostItem

# API Endpoints
auth_endpoint = "https://identity.api.rackspacecloud.com/v2.0/tokens"
billing_endpoint = "https://billing.api.rackspacecloud.com/v2/accounts/{ran}/estimated_charges"
latest_invoice_endpoint = "https://billing.api.rackspacecloud.com/v2/accounts/{ran}/invoices/latest"
billing_summary = "https://billing.api.rackspacecloud.com/v2/accounts/{ran}/billing-summary"
invoice_detail_endpoint = "https://billing.api.rackspacecloud.com/v2/accounts/{ran}/invoices/{invoiceId}/detail"

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
        raise Exception(f'auth failure:\n{json.dumps(js,indent=4)}')
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
        raise Exception(f'estimated_charges failed:\n{json.dumps(js,indent=4)}')

    # This should result in estimated total for the current billing cycle
    ret = [
        CostItem(
            js['estimatedCharges']['chargeTotal'],
            js['estimatedCharges']['currentBillingPeriodStartDate'],
            js['estimatedCharges']['currentBillingPeriodEndDate']
        )
    ]
    return ret

def life(account_name, api_key, billing_number) -> "dict":
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
        raise Exception(f'auth failure: {json.dumps(js,indent=4)}')
    token = js['access']['token']['id']

    # Form the request for our latest invoice
    headers = {
        'Accept':'application/json',
        'X-Auth-Token':token
    }

    x = requests.get(latest_invoice_endpoint.format(ran=billing_number), headers = headers)
    if not x.ok:
        raise Exception(f'unable to get latest invoice: {x.text}')
    js = json.loads(x.text)
    invoiceId = js['invoice']['id']

    # our next request returns text/csv
    headers['Accept'] = 'text/csv'
    
    x = requests.get(invoice_detail_endpoint.format(ran=billing_number, invoiceId=invoiceId), headers=headers)
    if not x.ok:
        raise Exception(f'failed to get detailed report {x}')

    # We need to parse the csv
    # Create an iterator that will decode each line as text
    detail_iter = codecs.iterdecode(x.iter_lines(), 'utf-8')
    reader = csv.DictReader(detail_iter, delimiter=',')
    
    vms = {}
    for row in reader:
        # Ignore anything that isn't a charge for server uptime
        if row['IMPACT_TYPE'] != 'CHARGE' or row['EVENT_TYPE'] != 'NG Server Uptime':
            continue
        
        # If it exists, just add, otherwise create the key
        if row['RES_NAME'] in vms.keys():
            vms[row['RES_NAME']]['hours'] += float(row['QUANTITY'])
        else:
            vms[row['RES_NAME']] = {
                'hours': float(row['QUANTITY']),
                'invoice': invoiceId,
                'bill': row['BILL_NO'],
                'account': account_name,
            }
    
    # Filter for anything alive longer than 7 days
    ret = {k:v for (k,v) in vms.items() if v['hours'] > 24*7}
    
    return ret