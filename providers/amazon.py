# do the amazon thing
import json
import subprocess
from datetime import datetime
from dateutil.relativedelta import relativedelta

from providers.base import CostItem

def cost(account_name, access_key_id, secret_access_key) -> "list[CostItem]":
	# we can override AWS config file with environment variables
	envVar = {
		'AWS_ACCESS_KEY_ID': access_key_id,
		'AWS_SECRET_ACCESS_KEY': secret_access_key
	}

	# Some date magic
	# Just first of this month, Start is inclusive
	first_day = datetime.today().replace(day=1).strftime('%Y-%m-%d')
	# This increments month by 1 and sets day to 1, End is exclusive
	last_day = (datetime.today()+relativedelta(months=1, day=1)).strftime('%Y-%m-%d')

	# We're gonna use subprocess.run to do thissss
	# Requires arguments be passed in a list
	# list items are where we would typically separate by space
	cmd = [
		'/usr/local/bin/aws',
		'ce',
		'get-cost-and-usage',
		'--time-period',
		'Start={},End={}'.format(first_day,last_day),
		'--granularity',
		'MONTHLY',
		'--metrics',
		'BlendedCost',
	]

	# do the command, pass our environment variables, capture the output as text
	ret = subprocess.run(
			args = cmd,
			env = envVar,
			capture_output = True,
			text = True,
		)
 
	# Parse as json, makes my life easy
	js = json.loads(ret.stdout)
 
	if ret.returncode != 0:
		raise Exception(f'Amazon {account_name} process call get-cost-and-usage failed:\n\
      		{json.dumps(js, indent=4)}')

	ret = [
     CostItem(js['ResultsByTime'][0]['Total']['BlendedCost']['Amount'],
              first_day,
              last_day)
     ]
	return ret
