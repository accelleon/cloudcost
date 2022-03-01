from datetime import datetime
from dateutil.relativedelta import relativedelta
import json

# OVH does some unique shit like signing API requests so cave to their SDK
import ovh

if __name__ != '__main__':
    from providers.base import CostItem
else:
    from base import CostItem

def cost(account_name, endpoint, app_key, app_secret, consumer_key):
    first_day = datetime.today().replace(day=1,hour=0,minute=0,second=0,microsecond=0).isoformat()
    last_day = (datetime.today()+relativedelta(months=1, day=1)).replace(hour=0,minute=0,second=0,microsecond=0).isoformat()
    
    client = ovh.Client(
        endpoint=endpoint,
        application_key=app_key,
        application_secret=app_secret,
        consumer_key=consumer_key)
    
    # Test to ensure our credentials are correct. this call should always succeed if so
    if not client.get('/me'):
        raise Exception(f'Authorization failed, check credentials')

    usage = client.get('/me/consumption/usage/forecast',
                       beginDate=first_day,
                       endDate=last_day)
    # Called failed if returned none
    if usage is None:
        raise Exception(f'/me/consumption/usage/forecast failed')
    # If its an empty array we've got no expected cost
    try:
        nextBilling = usage[0]['price']['value']
    except TypeError:
        return [
            CostItem(
                0,
                None,
                datetime.today().isoformat()
            )
        ]
    except Exception:
        raise
    
    # OVH will return this in a bloody RANDOM order
    # and has no endpoint for the latest bill
    # loop through all of them and compare the dates
    bills = client.get('/me/bill')
    
    if bills is None:
        raise Exception(f'/me/bill failed')
    
    prevBilling = None
    billDate = None
    
    for billid in bills:
        bill = client.get(f'/me/bill/{billid}')
        ptime = datetime.fromisoformat(bill['date'])
        if billDate is None or ptime > billDate:
            billDate = ptime
            prevBilling = bill

    # This should result in estimated total for the current billing cycle
    ret = [
        CostItem(
            nextBilling,
            first_day,
            last_day,
        ),
    ]
    
    # Append our previous invoice if we have one
    if prevBilling:
        ret.append(CostItem(
            prevBilling['priceWithTax']['value'],
            '',
            prevBilling['date']
        ))
    
    return ret