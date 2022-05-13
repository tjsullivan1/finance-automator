# from typing import Optional

import typer
import datetime
import uuid
import json
import os

from azure.core.exceptions import ResourceExistsError
from azure.data.tables import TableClient

# TODO: I need to refactor these functions to make them more useful.

app = typer.Typer()


def get_categories_from_file(file) -> list:
    with open(file) as file:
        categories = json.load(file)

    return categories


def get_category_from_user(trans, names):
    category_undefined = True
    while category_undefined:
        user_defined_category = input(f"Please classify this transaction:\n{trans}\n")

        if user_defined_category in names:
            category_undefined = False
        else:
            print(f"{user_defined_category} not in {names}")

    return user_defined_category


def set_manual_transaction(
    date_str: str, amount: float, description: str, bank: str, category: str
) -> dict:
    return {
        "Date": datetime.datetime.strptime(date_str, "%m/%d/%Y"),
        "Amount": amount,
        "Description": description,
        "Bank": bank,
        "Category": category,
    }


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


@app.command("insert")
def get_transaction_properties(
    date: str = typer.Option(
        ..., help="Please enter the transaction date formatted MM/DD/YYYY."
    ),
    amount: float = typer.Option(
        0.0,
        help="Please enter the transaction amount in USD, make it negative if it is an expense.",
    ),
    description: str = typer.Option(
        ..., help="Please enter a description for this transaction."
    ),
    bank: str = typer.Option(
        "Manually Added", help="Please enter a bank for this transaction."
    ),
    category: str = typer.Option(
        ..., help="Please enter a category for this transaction."
    ),
):
    categories = get_categories_from_file(
        "/home/tjs/finance-automator/data/categories.json"
    )

    category_names = [tmp_category.get("name") for tmp_category in categories]
    transaction = set_manual_transaction(date, amount, description, bank, category)

    if category not in category_names:
        transaction["Category"] = get_category_from_user(transaction, category_names)


if __name__ == "__main__":
    app()
