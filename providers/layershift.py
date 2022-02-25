from providers.base import CostItem
from providers.common import jelastic

endpoint = "https://app.j.layershift.co.uk"

def cost(account_name, api_key) -> "list[CostItem]":
    return jelastic.cost(endpoint, 'GBP', account_name, api_key)
