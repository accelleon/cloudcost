from providers.base import CostItem
from providers.common import jelastic

endpoint = "https://app.env2.paas.ruh.cloudsigma.com"

def cost(account_name, api_key) -> "list[CostItem]":
    return jelastic.cost(endpoint, 'USD', account_name, api_key)