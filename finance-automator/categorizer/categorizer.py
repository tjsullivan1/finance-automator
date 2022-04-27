import csv
import re
import json
import itertools

from importer.importer import import_amex_transactions, import_chase_transactions, import_wells_fargo_transactions

def get_categories_from_file(file) -> list:
    with open(file) as file:
        categories = json.load(file)
        
    return categories


def are_words_in_string(word_list, search_string):
    search_string = search_string.lower()
    
    for term in word_list:
        term = term.lower()
        result = re.search(r'{}'.format(term), search_string)
        if result:
            return True
    
    return False


def match_category(category: dict, description: str):
    if are_words_in_string(category.get('match_strings', []), description):
        return category.get('name')
    return None


def set_category(trans: dict, categories: list):
    current_description = trans.get('Description')

    for category in categories:
        trans['Category'] = match_category(category, current_description)
        if trans['Category']:
            break
            
    return trans



def loop_to_set_category(transaction_rows, income_categories: list, expense_categories: list):
    for trans in transaction_rows:
        # print(type(trans))
        # Check to ensure that we have a key called category and that the value is not None
        if 'Category' in trans.keys() and trans.get('Category'):
            pass
        else:
            #print('Need category')
            if float(trans.get('Amount', 0)) > 0.0:
                set_category(trans, income_categories)
                # Check to see if something is a refund. If it is, we'll put it into the expense category as a positive number
                if not trans['Category']:
                    set_category(trans, expense_categories)
            else:
                set_category(trans, expense_categories)
            
            if not trans['Category']:
                print(trans)
            else:
                # print(f"Successfully categorized: {trans}")
                pass


