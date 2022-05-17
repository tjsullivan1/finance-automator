import ast
import csv
import datetime
import hashlib
import itertools
import json
import os
import re
import uuid

import jsonpickle

# import pandas as pd
from azure.core.exceptions import ResourceExistsError
from azure.data.tables import TableClient
from azure.storage.queue import (
    QueueClient,
)


def get_checksum_from_dict(transaction: dict) -> str:
    # TJS -- we are not using this for security, just for hashing for uniqueness.
    return hashlib.md5(  # nosec
        jsonpickle.encode(transaction).encode("utf-8")
    ).hexdigest()


def check_import_transaction_existed(checksum: str, checksum_list: list) -> bool:
    return checksum in checksum_list


def standardize_transaction(
    date_str: str, amount: float, description: str, bank: str
) -> dict:
    return {
        "Date": datetime.datetime.strptime(date_str, "%m/%d/%Y"),
        "Amount": amount,
        "Description": description,
        "Bank": bank,
    }


def import_wells_fargo_transactions(statement_csv, checksum_list) -> list:
    # initializing the titles and rows list
    rows = []

    # reading csv file
    with open(statement_csv, "r", encoding="utf-8") as csvfile:
        # creating a csv reader object
        csvreader = csv.reader(csvfile)

        # extracting each data row one by one
        for row in csvreader:
            original_transaction_checksum = get_checksum_from_dict(row)
            if check_import_transaction_existed(
                original_transaction_checksum, checksum_list
            ):
                print(f"{original_transaction_checksum} existed")
            else:
                transact_dict = standardize_transaction(
                    date_str=row[0],
                    amount=float(row[1]),
                    description=row[4],
                    bank="Wells Fargo",
                )
                standardized_transaction_checksum = get_checksum_from_dict(
                    transact_dict
                )

                transact_dict["OriginalChecksum"] = original_transaction_checksum
                transact_dict[
                    "StandardizedChecksum"
                ] = standardized_transaction_checksum
                rows.append(transact_dict)

    return rows


def import_amex_transactions(statement_csv, checksum_list) -> list:
    """
    Amex is formatted with a header, so we can import this as a dictionary
    """
    rows = []

    with open(statement_csv, "r", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile, skipinitialspace=True)
        for row in reader:
            original_transaction_checksum = get_checksum_from_dict(row)
            if check_import_transaction_existed(
                original_transaction_checksum, checksum_list
            ):
                print(f"{original_transaction_checksum} existed")
            else:
                transact_dict = standardize_transaction(
                    date_str=row.get("Date"),
                    amount=-(float(row.get("Amount"))),
                    description=row.get("Description"),
                    bank="American Express",
                )
                standardized_transaction_checksum = get_checksum_from_dict(
                    transact_dict
                )

                transact_dict["OriginalChecksum"] = original_transaction_checksum
                transact_dict[
                    "StandardizedChecksum"
                ] = standardized_transaction_checksum
                rows.append(transact_dict)

    return rows


def import_chase_transactions(statement_csv, checksum_list) -> list:
    rows = []

    with open(statement_csv, "r", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile, skipinitialspace=True)
        for row in reader:
            original_transaction_checksum = get_checksum_from_dict(row)
            if check_import_transaction_existed(
                original_transaction_checksum, checksum_list
            ):
                print(f"{original_transaction_checksum} existed")
            else:
                transact_dict = standardize_transaction(
                    date_str=row.get("Transaction Date"),
                    amount=(float(row.get("Amount"))),
                    description=row.get("Description"),
                    bank="Chase Visa",
                )
                standardized_transaction_checksum = get_checksum_from_dict(
                    transact_dict
                )

                transact_dict["OriginalChecksum"] = original_transaction_checksum
                transact_dict[
                    "StandardizedChecksum"
                ] = standardized_transaction_checksum
                rows.append(transact_dict)

    return rows


def get_categories_from_file(file) -> list:
    with open(file, encoding="utf-8") as file:
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
        else:
            print(f"{user_defined_category} not in {names}")

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


def convert_row_to_entity(row_dict: dict) -> dict:
    row_dict["PartitionKey"] = row_dict.get("Bank", "manual")
    row_dict["RowKey"] = row_dict.get("StandardizedChecksum")
    row_dict["Id"] = uuid.uuid4()

    return row_dict


def insert_into_table(
    transactions: list,
    table_name: str,
    connection_string=os.getenv("AZURE_STORAGE_CXN"),
):
    with TableClient.from_connection_string(
        connection_string, table_name
    ) as table_client:
        # Create a table in case it does not already exist
        try:
            table_client.create_table()
        except ResourceExistsError:
            print("Table already exists")

        for row in transactions:
            # [START create_entity]
            try:
                ent = convert_row_to_entity(row)
                resp = table_client.create_entity(ent)
                print(resp)
            except ResourceExistsError:
                # TODO: Should probably log these, but I don't want to print these out.
                print("Entity already exists")
                # pass
            # except:
            #     print(f"Got an erorr with {ent}")


def insert_into_queue(
    transaction: list,
    queue_name: str,
    connection_string=os.getenv("AZURE_STORAGE_CXN"),
):
    # print(transaction)

    # Instantiate a QueueClient object which will
    # be used to create and manipulate the queue
    print("Creating queue: " + queue_name)
    with QueueClient.from_connection_string(
        connection_string, queue_name
    ) as queue_client:
        try:
            # Create the queue
            queue_client.create_queue()
        except ResourceExistsError:
            print("Queue already exists")

        try:
            queue_client.send_message(transaction)
        except ResourceExistsError:
            print("Transaction already exists in queue")


def add_transaction_manually(
    queue_name: str,
    categories: list,
    connection_string=os.getenv("AZURE_STORAGE_CXN"),
):
    manually_categorized = []

    with QueueClient.from_connection_string(
        connection_string, queue_name
    ) as queue_client:
        messages = queue_client.receive_messages()

        for message in messages:
            transaction = message.get("content")
            parsed = ast.parse(transaction, mode="eval")
            fixed = ast.fix_missing_locations(parsed)
            compiled = compile(fixed, "<string>", "eval")
            # TODO: this needs to be fixed.
            # I put this in place because the string that comes out of the queue doesn't reformat correctly as a dict.
            # Ideally, I would determine how to do this with ast.literal_eval or just figure out why a dict doesn't convert.
            # Both of those gave me options on 20220510
            evaluated_message = eval(compiled)  # nosec

            evaluated_message["Category"] = get_category_from_user(
                evaluated_message, categories
            )
            manually_categorized.append(evaluated_message)
            print("Dequeueing message: " + message.content)
            queue_client.delete_message(message.id, message.pop_receipt)

    return manually_categorized


def get_existing_checksums(
    table_name: str,
    connection_string=os.getenv("AZURE_STORAGE_CXN"),
) -> list:
    checksums = []
    with TableClient.from_connection_string(
        connection_string, table_name
    ) as table_client:

        entities = table_client.list_entities()

        for item in entities:
            checksums.append(item.get("OriginalChecksum"))

    return checksums


def main():
    existing_checksums = get_existing_checksums("transactions")

    delta_rows = import_amex_transactions(
        "/home/tjs/finance-automator/data/amexdeltaytd.csv", existing_checksums
    )
    plat_rows = import_amex_transactions(
        "/home/tjs/finance-automator/data/amexplatytd.csv", existing_checksums
    )
    chase_rows = import_chase_transactions(
        "/home/tjs/finance-automator/data/chaseytd.CSV", existing_checksums
    )
    wells_rows = import_wells_fargo_transactions(
        "/home/tjs/finance-automator/data/wfytd.csv", existing_checksums
    )

    transactions = list(itertools.chain(delta_rows, plat_rows, chase_rows, wells_rows))

    categories = get_categories_from_file(
        "/home/tjs/finance-automator/data/categories.json"
    )

    categorized, uncategorized = loop_to_set_category(transactions, categories)

    for trans in uncategorized:
        if check_import_transaction_existed(
            trans.get("OriginalChecksum"), existing_checksums
        ):
            print("Transaction {trans} already existed")
        else:
            insert_into_queue(trans, "uncategorized-transactions")

    # Manually categorize the transactions
    category_names = [category.get("name") for category in categories]
    manually_categorized = add_transaction_manually(
        "uncategorized-transactions", category_names
    )

    fully_categorized = categorized + manually_categorized

    insert_into_table(fully_categorized, "transactions")

    # dfItem = pd.DataFrame.from_records(categorized)
    # dfItem["Date"] = pd.to_datetime(dfItem["Date"])
    # GroupItem = dfItem.groupby([pd.Grouper(key="Date", freq="M"), "Category"]).sum()
    # print(GroupItem)


if __name__ == "__main__":
    main()
