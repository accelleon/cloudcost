import requests
import json

from providers.base import CostItem

# THE SOFTLAYER API ALSO RETURNS IBM BLUEMIX ITEMS WHY IBM FUCKING SEPARATE YOUR PRODUCTS
# I take this back, apparently IBM's own API doesn't report costs for bluemix correctly
# BUT SOFTLAYER DOES >.>

# Grab billing items on the next invoice
# *Note: These are top level items, top level items don't necessarily report full cost
# For example a service plan would be a top level item with 0 cost but would have a child
# item for usage costs
api_getNextInvoiceTopLevel = 'https://api.softlayer.com/rest/v3.1/SoftLayer_Account/getNextInvoiceTopLevelBillingItems.json'

# Grab child items of a billing item
# Returns only non-zero cost children of billing item id {id}
api_getChildren = 'https://api.softlayer.com/rest/v3.1/SoftLayer_Billing_Item/{id}/getNonZeroNextInvoiceChildren.json'

# Grab previous invoice object
api_getPrevInvoice = 'https://api.softlayer.com/rest/v3.1/SoftLayer_Account/getLatestRecurringInvoice.json'

# Grab top level items of indicated invoice
api_getInvoiceTopLevel = 'https://api.softlayer.com/rest/v3.1/SoftLayer_Billing_Invoice/{id}/getInvoiceTopLevelItems.json'

# Grab an invoices non-zero cost children
api_getInvoiceChildren = 'https://api.softlayer.com/rest/v3.1/SoftLayer_Billing_Invoice_Item/{id}/getNonZeroAssociatedChildren.json'

# Returns a CostItem representing the next billing cycle's expected costs
def NextBilling(account_name, api_key) -> CostItem:
    # Uses basic auth? lol
    auth = (account_name, api_key)

    # We filter everything that doesn't start with paas
    # Object filters suck https://sldn.softlayer.com/article/object-filters/
    objectFilter = {
        'nextInvoiceTopLevelBillingItems': {
            'categoryCode' : {'operation': '^=paas'}
        }
    }

    # These are the parameters we'll pass to the request
    # Include the object filter as a json dump, its neater to do it this way
    # Object masks are better than filters https://sldn.softlayer.com/article/object-masks/
    paramsTopLevel = {
        'objectMask': 'mask[id,categoryCode,recurringFee,cycleStartDate,nextBillDate]',
        'objectFilter': json.dumps(objectFilter)
    }

    x = requests.get(api_getNextInvoiceTopLevel, auth=auth, params=paramsTopLevel)
    topLevel = json.loads(x.text)
    if not x.ok:
        raise Exception(f'Bluemix {account_name}: getNextInvoiceTopLevel Failed:\n\
            {json.dumps(topLevel, indent=4)}')
    startDate = topLevel[0]['cycleStartDate']
    endDate = topLevel[0]['nextBillDate']

    # Mask for calls to getChildren
    paramsChildren = {
        'objectMask': 'mask[recurringFee]'
    }

    total = 0
    a = None

    # Loop through every top level item and pull the cost for its children
    for item in topLevel:
        total += float(item['recurringFee'])
        x = requests.get(api_getChildren.format(id=item['id']), auth=auth, params=paramsChildren)
        children = json.loads(x.text)
        if not x.ok:
            raise Exception(f'Bluemix {account_name}: getChildren Failed:\n\
                {json.dumps(children, indent=4)}')
        for child in children:
            total += float(child['recurringFee'])

    return CostItem(total, startDate, endDate)

# Return a CostItem representing the previous billing cycle
def PrevBilling(account_name, api_key) -> CostItem:
    # Uses basic auth
    auth = (account_name, api_key)
    
    # We filter everything that doesn't start with paas
    # Object filters suck https://sldn.softlayer.com/article/object-filters/
    objectFilter = {
        'invoiceTopLevelItems': {
            'categoryCode' : {'operation': '^=paas'}
        }
    }
    
    # These are the parameters we'll pass to the request
    # Include the object filter as a json dump, its neater to do it this way
    # Object masks are better than filters https://sldn.softlayer.com/article/object-masks/
    paramsTopLevel = {
        'objectMask': 'mask[id,categoryCode,recurringFee,billingItemId]',
        'objectFilter': json.dumps(objectFilter)
    }
    
    # Grab the previous invoice
    x = requests.get(api_getPrevInvoice, auth=auth)
    js = json.loads(x.text)
    if not x.ok:
        raise Exception(f'Bluemix {account_name}: getPrevInvoice Failed:\n\
            {json.dumps(js, indent=4)}')
    # Need id and invoice creation date (billing period end date)
    invoice = js['id']
    endDate = js['createDate']
    
    # Pull top level items for that invoice
    x = requests.get(api_getInvoiceTopLevel.format(id=invoice), auth=auth, params=paramsTopLevel)
    topLevel = json.loads(x.text)
    if not x.ok:
        raise Exception(f'Bluemix {account_name}: getInvoiceTopLevel Failed:\n\
            {json.dumps(topLevel, indent=4)}')

    # Mask for calls to getChildren
    paramsChildren = {
        'objectMask': 'mask[recurringFee]'
    }

    total = 0
    # Loop through every top level item and pull the cost for its children
    for item in topLevel:
        total += float(item['recurringFee'])
        x = requests.get(api_getInvoiceChildren.format(id=item['id']), auth=auth, params=paramsChildren)
        children = json.loads(x.text)
        if not x.ok:
            raise Exception(f'Bluemix {account_name}: getChildren Failed:\n\
                {json.dumps(children, indent=4)}')
        for child in children:
            total += float(child['recurringFee'])

    return CostItem(total, "", endDate)

# Do the cost thing
def cost(account_name, api_key) -> "list[CostItem]":
    ret = [
        NextBilling(account_name, api_key),
        PrevBilling(account_name, api_key)
    ]
    return ret