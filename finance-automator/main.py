import csv
import json
import itertools

import pandas as pd

from importer.importer import (
    import_amex_transactions,
    import_chase_transactions,
    import_wells_fargo_transactions,
)
from categorizer.categorizer import get_categories_from_file, loop_to_set_category

delta_rows = import_amex_transactions(
    "/home/tjs/finance-automator/data/amexdeltaytd.csv"
)
plat_rows = import_amex_transactions("/home/tjs/finance-automator/data/amexplatytd.csv")
chase_rows = import_chase_transactions("/home/tjs/finance-automator/data/chaseytd.CSV")
wells_rows = import_wells_fargo_transactions(
    "/home/tjs/finance-automator/data/wfytd.csv"
)

transactions = list(itertools.chain(delta_rows, plat_rows, chase_rows, wells_rows))

categories = get_categories_from_file(
    "/home/tjs/finance-automator/data/categories.json"
)

categorized, uncategorized = loop_to_set_category(transactions, categories)

# TODO: write uncategorized to file/queue. 

dfItem = pd.DataFrame.from_records(categorized)
dfItem['Date']=pd.to_datetime(dfItem['Date'])
GroupItem = dfItem.groupby([pd.Grouper(key='Date', freq='M'), 'Category']).sum()
print(GroupItem)
