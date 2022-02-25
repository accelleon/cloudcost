from providers.base import CostItem
from providers.common import softlayer

# Do the cost thing
def cost(account_name, api_key) -> "list[CostItem]":
    # Grab the cost of all items that begin with paas
    return softlayer.cost('!^=paas', account_name, api_key)