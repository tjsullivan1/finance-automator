#!/usr/bin/env python

import json
import click


# TODO: update to accept filename as input
with open('expense_categories.json') as file:
    categories = json.load(file)

# TODO: update to accept cmdline input for the category name
cat_index = next((i for i, item in enumerate(categories) if item["name"] == "<category_name>"), None)


# TODO: add logic to make allow this to inplace edit
if cat_index:
    strings = categories[cat_index].get('match_strings')
    print(strings)