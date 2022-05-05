import csv
import hashlib
import json
from datetime import datetime


def import_wells_fargo_transactions(statement_csv) -> list:
    # initializing the titles and rows list
    rows = []

    # reading csv file
    with open(statement_csv, "r") as csvfile:
        # creating a csv reader object
        csvreader = csv.reader(csvfile)

        # extracting each data row one by one
        for row in csvreader:
            rows.append(
                {
                    "Date": datetime.strptime(row[0], '%m/%d/%Y'),
                    "Amount": float(row[1]),
                    "Description": row[4],
                    "Bank": "Wells Fargo",
                }
            )

    return rows


def import_amex_transactions(statement_csv) -> list:
    """
    Amex is formatted with a header, so we can import this as a dictionary
    """
    rows = []

    with open(statement_csv, "r") as csvfile:
        reader = csv.DictReader(csvfile, skipinitialspace=True)
        for row in reader:
            # TODO: There's got to be a more pythonic way to do this.
            rows.append(
                {
                    "Date": datetime.strptime(row.get("Date"), '%m/%d/%Y'),
                    "Amount": -(float(row.get("Amount"))),
                    "Description": row.get("Description"),
                    "Bank": "American Express",
                }
            )

    return rows


def import_chase_transactions(statement_csv) -> list:
    rows = []

    with open(statement_csv, "r") as csvfile:
        reader = csv.DictReader(csvfile, skipinitialspace=True)
        for row in reader:
            # TODO: There's got to be a more pythonic way to do this.
            rows.append(
                {
                    "Date": datetime.strptime(row.get("Transaction Date"), '%m/%d/%Y'),
                    "Amount": float(row.get("Amount")),
                    "Description": row.get("Description"),
                    "Bank": "Chase Visa",
                }
            )

    return rows


# TODO: Add Marcus.com statement parser
# TODO: Add paystub parser
# TODO: Add fidelity statement parser

def get_checksum_from_dict(transaction: dict) -> str:
     return hashlib.md5(json.dumps(transaction).encode('utf-8')).hexdigest()

def check_import_transaction_existed(checksum: str, checksum_list: list) -> bool:
    return checksum in checksum_list
