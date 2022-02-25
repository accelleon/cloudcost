# Cloudcost Automation

Sick and tired of *manually* checking the costs you incurred for a given reporting period for *all* of your supported providers?
I present you THIS.

This script provided the required authentication credentials will generate an Excel spreadsheet and upload it to a Mattermost channel.

## Preparing the environment

There is a convenient setup.sh script to automatically setup the required environment if you are targeting a local database.
This script will install the required packages, python requirements and set up the database.
A config file will be generated in /etc/cloudcost/ you will need to modify the [mattermost] section with the required settings. Optionally you can modify [database] if you are connecting to a remote database.
The Mattermost API token will be acquired when you create a new token for an existing bot or a new bot following the instructions here: [Bot Accounts](https://developers.mattermost.com/integrate/admin-guide/admin-bot-accounts/)
The channel ID required by the config can be found in channel information.
You must make sure you add the bot to the channel you want it to post in.

## Working with the script

```bash
python3 cloudcost.py --help
usage: cloudcost.py [-h] [--nopost] {cost,life,list,update,add,remove,order,install} ...

positional arguments:
  {cost,life,list,update,add,remove,order,install}
                        sub-commands, type <command> --help to get more information
    cost                runs the cost function and posts to MM
    life                runs a check on the previous invoice and alerts for things alive longer than a time
    list                list accounts or providers
    update              update an exist account's credentials
    add                 add a new account
    remove              remove an account
    order               set the ordering of accounts

optional arguments:
  -h, --help            show this help message and exit
  --nopost              do not post to MM
```

### Running costs

Running without any arguments will execute the script. An excel sheet will be generated and uploaded to the channel specified in the config file. The life sub command (if implemented for a provider) is also triggered if today is the first day of a new billing cycle. Alternatively you may invoke the script for a single provider `python3 cloudcost.py cost --iaas <provider>` or account `python3 cloudcost.py --iaas <provider> --account <account_name>`

### Life

The script has functionality to report to the Mattermost channel any items you were billed for that existed longer than 7 days. Currently this is only implemented for Rackspace, as we've noticed a tendency for billing of non-existent nodes.

### Managing accounts

Accounts are managed through the `list`, `update`, `add`, `remove` and `order` commands. You can invoke any of these sub-commands with the `--help` option to retrieve more information.
The only non-self-explanatory one would be `order`; This command will allow you to order the accounts in the generated spreadsheet. The system's default text editor will be opened with a list of all accounts, simply move the lines to the desired order and save the changes.
