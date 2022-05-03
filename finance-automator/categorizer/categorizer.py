import csv
import re
import json
import itertools

from importer.importer import (
    import_amex_transactions,
    import_chase_transactions,
    import_wells_fargo_transactions,
)


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
