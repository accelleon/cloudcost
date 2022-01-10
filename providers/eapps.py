import requests
import json
from datetime import datetime
from dateutil.relativedelta import relativedelta

from providers.base import CostItem

billing_endpoint = "https://app.jelastic.eapps.com/1.0/billing/account/rest/getaccountbillinghistorybyperiod"

def cost(account_name, api_key) -> "list[CostItem]":
    headers = {
        'Content-Type':'application/json',
    }

    # Some date magic
    # Just first of this month, Start is inclusive
    first_day = datetime.today().replace(day=1).strftime('%Y-%m-%d 00:00:00')
    # This increments month by 1 and sets day to 1, End is exclusive
    last_day = (datetime.today()+relativedelta(months=1, day=1)).strftime('%Y-%m-%d 00:00:00')

    data = {
        # This is a generic appid for all jelastic apps, use global or "no" environment
        'appid': '1dd8d191d38fff45e62564fcf67fdcd6',
        'session': api_key,
        'starttime': first_day,
        'endtime': last_day,
        'period': 'MONTH',
    }

    # Grab the extensive billing report
    x = requests.get(billing_endpoint, headers=headers, params=data)
    js = json.loads(x.text)

    # Alright now we need to sum it all into a single number
    # We need to add together cost for each item
    total = 0
    [total := total + i['cost'] for i in js['array']]

    # Generate our return list
    ret = [
        CostItem(
            total,
            first_day,
            last_day
        )
    ]
    return ret
