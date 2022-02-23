import requests
import json
from datetime import datetime
from dateutil.relativedelta import relativedelta

from providers.base import CostItem

endpoint = 'https://ruh.cloudsigma.com/api/2.0'

def cost(account_name, password) -> 'list[CostItem]':
    # Some date magic
    # Just first of this month, Start is inclusive
    first_day = datetime.today().replace(day=1).strftime('%Y-%m-%d')
    # This increments month by 1 and sets day to 1, End is exclusive
    last_day = (datetime.today()+relativedelta(days=1)).strftime('%Y-%m-%d')
    #last_day = (datetime.today()+relativedelta(months=1, day=1)).strftime('%Y-%m-%d')

    # Basic auth
    auth = (account_name, password)

    # Typical header
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }

    # First retrieve our account balance
    x = requests.get(f'{endpoint}/balance', headers=headers, auth=auth)
    if not x.ok:
        raise Exception(f'failed to retreive balance {x}')
    js = json.loads(x.text)
    balance = f'{js['balance']} USD'

    
    # Query parameters, filter by what we want
    # our first request we want nothing returned, we simply want the total count that our query returns
    params = {
        'time__gt': first_day,
        'time__lt': last_day,
        'limit': 0
    }

    # Do the thing
    x = requests.get(f'{endpoint}/ledger', headers=headers, auth=auth, params=params)
    if not x.ok:
        raise Exception(f'failed to retreive monthly usage {x}')
    js = json.loads(x.text)

    # Set the limit for our next request, grab everything
    params['limit'] = js['meta']['total_count']

    # Do the thing
    x = requests.get(f'{endpoint}/ledger', headers=headers, auth=auth, params=params)
    if not x.ok:
        raise Exception(f'failed to retreive monthly usage {x}')
    js = json.loads(x.text)

    
    # Loop through the returned itemized JSON and total
    total = float(0)
    # We only care about > 0 amounts for this since negative are us adding to the balance
    # List comprehension is great
    [total := total + (float(i['amount']) if float(i['amount']) > 0 else 0) for i in js['objects']]

    return [
        CostItem(
            total,
            first_day,
            last_day,
            balance
        )
    ]