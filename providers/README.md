# Implementing new providers

Implementing new providers *must* follow the below:

* Filename must be named after the provider's name
* Provider must implement 1 function: `cost()`
* This function `cost()` can accept any number of parameters but one of them must be `account_name`
* `cost()` should only accept parameters required to work with the provider
* `cost()` must return `list[CostItem]`, `CostItem` it is provided in `providers.base`
* Formatting dates and amounts is not necessary, this is handled in `cloudcost.py`, however dates should be in ISO8601

```python
from providers.base import CostItem

def cost(account_name) -> "list[CostItem]":
    return [CostItem("0.15", "YYYY-MM-DD", "YYYY-MM-DD")]
```
