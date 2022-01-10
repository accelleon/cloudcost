import requests
import json
from datetime import datetime

from providers.base import CostItem

def cost(account_name, api_key) -> "list[CostItem]":

    api_url = "https://api.heroku.com/account/invoices"

    headers = {
        'Authorization':f'Bearer {api_key}',
        'Accept':'application/vnd.heroku+json; version=3'
    }

    # The month we're looking for
    month = datetime.today().strftime('%Y-%m')

    # We need to loop through all of Heroku's invoices and find the one
    # that is for our current month
    for i in json.loads(requests.get(api_url, headers=headers).text):
        if month in i['period_start']:
            # For some damn reason heroku returns this * 100
            ret = [
                CostItem(
                    i['total'] / 100,
                    i['period_start'],
                    i['period_end']
                )
            ]
            return ret