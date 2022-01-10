from collections import namedtuple

# This is the namedtupled that is expected as return from cost()
# Generate cost, startDate, and endDate as members
CostItem = namedtuple("CostItem", "cost startDate endDate")

# All providers *must* implement a single entry method cost()
# This method cost *must* have at least 1 parameter account_name
# This method must return a list of CostItems defined above
# Ex:
"""
def cost(account_name) -> "list[CostItem]":
    return [CostItem("0.15", "YYYY-MM-DD", "YYYY-MM-DD")]
"""