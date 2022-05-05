import csv
import hashlib
import itertools
import json
import re
import uuid
from datetime import datetime

import jsonpickle
import pandas as pd
from azure.core.exceptions import HttpResponseError, ResourceExistsError
from azure.data.tables import TableClient


def get_checksum_from_dict(transaction: dict) -> str:
    # TJS -- we are not using this for security, just for hashing for uniqueness.
    return hashlib.md5(
        jsonpickle.encode(transaction).encode("utf-8")
    ).hexdigest()  # nosec


def check_import_transaction_existed(checksum: str, checksum_list: list) -> bool:
    return checksum in checksum_list


def standardize_transaction(
    date_str: str, amount: float, description: str, bank: str
) -> dict:
    return {
        "Date": datetime.strptime(date_str, "%m/%d/%Y"),
        "Amount": amount,
        "Description": description,
        "Bank": bank,
    }


def import_wells_fargo_transactions(statement_csv) -> list:
    # initializing the titles and rows list
    rows = []

    # reading csv file
    with open(statement_csv, "r") as csvfile:
        # creating a csv reader object
        csvreader = csv.reader(csvfile)

        # extracting each data row one by one
        for row in csvreader:
            original_transaction_checksum = get_checksum_from_dict(row)
            transact_dict = standardize_transaction(
                date_str=row[0],
                amount=float(row[1]),
                description=row[4],
                bank="Wells Fargo",
            )
            standardized_transaction_checksum = get_checksum_from_dict(transact_dict)

            transact_dict["OriginalChecksum"] = original_transaction_checksum
            transact_dict["StandardizedChecksum"] = standardized_transaction_checksum
            rows.append(transact_dict)

    return rows


def import_amex_transactions(statement_csv) -> list:
    """
    Amex is formatted with a header, so we can import this as a dictionary
    """
    rows = []

    with open(statement_csv, "r") as csvfile:
        reader = csv.DictReader(csvfile, skipinitialspace=True)
        for row in reader:
            original_transaction_checksum = get_checksum_from_dict(row)
            transact_dict = standardize_transaction(
                date_str=row.get("Date"),
                amount=-(float(row.get("Amount"))),
                description=row.get("Description"),
                bank="American Express",
            )
            standardized_transaction_checksum = get_checksum_from_dict(transact_dict)

            transact_dict["OriginalChecksum"] = original_transaction_checksum
            transact_dict["StandardizedChecksum"] = standardized_transaction_checksum
            rows.append(transact_dict)

    return rows


def import_chase_transactions(statement_csv) -> list:
    rows = []

    with open(statement_csv, "r") as csvfile:
        reader = csv.DictReader(csvfile, skipinitialspace=True)
        for row in reader:
            original_transaction_checksum = get_checksum_from_dict(row)
            transact_dict = standardize_transaction(
                date_str=row.get("Transaction Date"),
                amount=(float(row.get("Amount"))),
                description=row.get("Description"),
                bank="Chase Visa",
            )
            standardized_transaction_checksum = get_checksum_from_dict(transact_dict)

            transact_dict["OriginalChecksum"] = original_transaction_checksum
            transact_dict["StandardizedChecksum"] = standardized_transaction_checksum
            rows.append(transact_dict)

    return rows


def get_categories_from_file(file) -> list:
    with open(file) as file:
        categories = json.load(file)

    return categories


def are_words_in_string(word_list, search_string):
    search_string = search_string.lower()

    for term in word_list:
        term = term.lower()
        result = re.search(r"{}".format(term), search_string)
        if result:
            return True

    return False


def match_category(category: dict, description: str):
    if are_words_in_string(category.get("match_strings", []), description):
        return category.get("name")
    return None


def set_category(trans: dict, categories: list):
    current_description = trans.get("Description")

    for category in categories:
        trans["Category"] = match_category(category, current_description)
        if trans["Category"]:
            break

    return trans


def get_category_from_user(trans, names):
    category_undefined = True
    while category_undefined:
        user_defined_category = input(f"Please classify this transaction:\n{trans}\n")

        if user_defined_category in names:
            category_undefined = False

    return user_defined_category


def loop_to_set_category(transaction_rows, categories: list):
    categorized_transactions = []
    uncategorized_transactions = []
    for trans in transaction_rows:
        # print(type(trans))
        # Check to ensure that we have a key called category and that the value is not None
        if "Category" in trans.keys() and trans.get("Category"):
            pass
        else:
            set_category(trans, categories)

            if trans.get("Category"):
                categorized_transactions.append(trans)
            else:
                uncategorized_transactions.append(trans)
            #     category_names = [name.get('name') for name in categories]
            #     trans["Category"] = get_category_from_user(trans, category_names)

    return categorized_transactions, uncategorized_transactions


def main():
    delta_rows = import_amex_transactions(
        "/home/tjs/finance-automator/data/amexdeltaytd.csv"
    )
    plat_rows = import_amex_transactions(
        "/home/tjs/finance-automator/data/amexplatytd.csv"
    )
    chase_rows = import_chase_transactions(
        "/home/tjs/finance-automator/data/chaseytd.CSV"
    )
    wells_rows = import_wells_fargo_transactions(
        "/home/tjs/finance-automator/data/wfytd.csv"
    )

    transactions = list(itertools.chain(delta_rows, plat_rows, chase_rows, wells_rows))

    categories = get_categories_from_file(
        "/home/tjs/finance-automator/data/categories.json"
    )

    categorized, uncategorized = loop_to_set_category(transactions, categories)

    # TODO: write uncategorized to file/queue.

    # dfItem = pd.DataFrame.from_records(categorized)
    # dfItem["Date"] = pd.to_datetime(dfItem["Date"])
    # GroupItem = dfItem.groupby([pd.Grouper(key="Date", freq="M"), "Category"]).sum()
    # print(GroupItem)


if __name__ == "__main__":
    main()
