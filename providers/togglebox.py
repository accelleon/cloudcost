from providers.base import CostItem
from providers.common import jelastic

endpoint = "https://app.togglebox.cloud"

def cost(account_name, api_key) -> "list[CostItem]":
    return jelastic.cost(endpoint, 'USD', account_name, api_key)