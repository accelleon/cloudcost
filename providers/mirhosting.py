from providers.base import CostItem
from providers.common import jelastic

endpoint = "https://app.mircloud.host"

def cost(account_name, api_key) -> "list[CostItem]":
    return jelastic.cost(endpoint, 'EUR', account_name, api_key)