# PSQL stuff
import psycopg2
import psycopg2.extras
from psycopg2 import sql

# Python Standard stuff
import importlib
import argparse
import inspect
from datetime import datetime
from getpass import getpass
import configparser
import requests
from os import path
import json

# XLSX support
from openpyxl import Workbook

# Upload file to mattermost
def upload_file(file, server, channel_id, token):
    # Simple auth header
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type':'application/json'
    }

    # Payload for initiating the file upload
    payload = {
        'channel_id': channel_id,
        'filename': path.basename(file)
    }

    # File description
    files = {
        'file': open(file, 'rb'),
        'filename': path.basename(file)
    }

    # Create a new upload and grab the ID
    print("Uploading...")
    x = requests.post(f'{server}/api/v4/files', headers=headers, params=payload, data=open(file, 'rb'))
    js = json.loads(x.text)
    upload_id = js['file_infos'][0]['id']

    # Payload for post, attach the file we just uploaded
    payload = {
            'channel_id': channel_id,
            'message': 'Today\'s cloud cost!',
            'file_ids': [upload_id]
        }

    # Post the file
    print("Done.")
    response = requests.post(f'{server}/api/v4/posts', headers=headers, json=payload)

# Creates some headers for the excel sheet
def create_xlsx():
    # Workbook object
    wb = Workbook()

    # Grab active sheet, change title
    ws = wb.active
    ws.title = "Cloud Cost"

    # Reporting dates
    ws['A1'] = 'Report Made:'
    ws['B1'] = datetime.today().replace(day=1)
    ws['B1'].number_format = 'yyyy-mm-dd'

    # Headers
    ws['A3'] = 'Provider'
    ws['B3'] = 'Billing Start'
    ws['C3'] = 'Billing End'
    ws['D3'] = 'Account Name'
    ws['E3'] = 'Current Invoice'

    # Return workbook, worksheet, starting row index
    return wb, ws, 4

# Queries DB and runs cost against all accounts, all providers
def run_cost(cur):
    # Set up our workbook
    wb, ws, i = create_xlsx()

    # Grab a list of all tables in the DB (should be a list of provider names)
    # this is postgresql specific
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")

    # fetchall() will return us a dictionary of lists
    # we only want the first value of each list
    tables = cur.fetchall()
    providers = map(lambda a: a[0], tables)

    # Now we loop through each provider
    for provider in providers:
        try:
            # Import a module named with the provider from the providers directory
            module = importlib.import_module("providers.{}".format(provider))

            # This is why we chose a dict cursor
            # Simply read a row and pass the entire dict to the module.cost(**kwargs) function
            cur.execute("SELECT * FROM {}".format(provider))
            rows = cur.fetchall()

            for row in rows:
                # Make sure exceptions raised in cost() don't kill
                try:
                    # Call out to provider module's cost() function
                    costs = module.cost(**row)

                    # Spill to excel
                    # Since we now return a list of CostItems to accomodate for
                    # Bluemix and Softlayer returning both previous and current billing
                    # periods, loop through the list of CostItems returned
                    # TODO: Gotta be a neater way to do this
                    for cost in costs:
                        ws[f'A{i}'] = provider
                        # Split the string, if it contains more than a date, we only want the date
                        ws[f'B{i}'] = cost.startDate[:10]
                        ws[f'C{i}'] = cost.endDate[:10]
                        ws[f'D{i}'] = row['account_name']
                        ws[f'E{i}'] = round(float(cost.cost), 2)
                        i = i + 1

                    print("{} total cost to month is {}".format(row['account_name'], cost))
                except Exception as err:
                    print(err)

        # Two things can lead here, module import failing and sql query failure
        # Skip this provider in this case
        except BaseException as err:
            print(f"Unexpected {err=}, {type(err)=}")

    # Save to the workbook
    fname = "/tmp/cloudcost{}.xlsx".format(datetime.today().strftime("%Y-%m-%d"))
    wb.save(fname)

    # Return the filename so our MM uploader can do its thing
    return fname

def add_account(cur, provider):
    # First check if provider module exists
    # It doesn't we can't do anything
    try:
        module = importlib.import_module("providers.{}".format(provider))

        # Get argument names from module's run command
        argspec = inspect.getfullargspec(module.cost)
        # argspec[0] is a list of names of standard arguments
        cols = argspec[0]

        # Create the table if it doesn't exist
        # Build arbritary query to insert table with columns that match our function
        create = sql.SQL("create table if not exists {table} ({columns})").format(
                table = sql.Identifier(provider),
                # This one sucks, needs to nest to insert column datatype
                columns = sql.SQL(',').join(map(lambda a: sql.SQL("{name} text").format(name=sql.Identifier(a)), cols))
            )

        # do the thing
        cur.execute(create)

        # prompt user for each argument we'll need for cost
        vals = map(lambda a: input("{}: ".format(a)) if a == 'account_name' else getpass("{}: ".format(a)), cols)

        # Build arbritary insert using the psycopg2 sql extension
        # Need to convert everything into Identifier and Literal for this to work so map cols and vals
        insert = sql.SQL("insert into {table}({columns}) VALUES ({values})").format(
                table = sql.Identifier(provider),
                columns = sql.SQL(',').join(map(lambda a: sql.Identifier(a), cols)),
                values = sql.SQL(',').join(map(lambda a: sql.Literal(a), vals)))

        # Execute query and commit change
        cur.execute(insert)
        cur.connection.commit()

    # For now die here, need to find what exceptions can be thrown here
    except BaseException as err:
            print(f"Unexpected {err=}, {type(err)=}")
            raise


def main(args):
    # Connect to our postgres database
    conn = None
    try:
        # Read in our config file
        conf = configparser.ConfigParser()
        conf.read("/etc/cloudcost/cloudcost.conf")

        # Directly pass the config file as argument
        # ** formats it to pass the dictionary as named arguments
        conn = psycopg2.connect(**conf['database'])

        # Create a cursor, use this to interact with the DB
        # Cursor has support for "with" intrinsic (autocleanup outside of scope)
        # Read out results as a dictionary object
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            
            # Fork here depending on if we're running cost or adding a provider
            if args.add is not None:
                add_account(cur, args.add)
            else:
                fname = run_cost(cur)
                upload_file(fname, **conf['mattermost'])

    # Did we screw up connecting to database?
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)

    # Some other non-recoverable exception
    except BaseException as err:
        print(f"Unexpected {err=}, {type(err)=}")
        raise

    finally:
        # Need to clean up connection if made it
        if conn is not None:
            conn.close()

# Python standard, do nothing if imported
if __name__ == '__main__':
    # Check for arguments (these only exist if you want to add accounts)
    parser = argparse.ArgumentParser()
    parser.add_argument("--add", type=str, help="--add PROVIDER Add an account for PROVIDER to the database")

    args = parser.parse_args()

    main(args)
