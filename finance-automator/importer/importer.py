import csv
import hashlib
import jsonpickle

from datetime import datetime


def get_checksum_from_dict(transaction: dict) -> str:
    return hashlib.md5(jsonpickle.encode(transaction).encode("utf-8")).hexdigest()


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
