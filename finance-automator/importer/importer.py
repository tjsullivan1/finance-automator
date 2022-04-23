import csv

def import_wells_fargo_transactions(statement_csv) -> list:
    # initializing the titles and rows list
    rows = []

    # reading csv file
    with open(statement_csv, 'r') as csvfile:
        # creating a csv reader object
        csvreader = csv.reader(csvfile)

        # extracting each data row one by one
        for row in csvreader:
            rows.append({
                'Date': row[0], 
                'Amount': row[1], 
                'Description': row[4]
            })
            
    return rows


def import_amex_transactions(statement_csv) -> list:
    '''
    Amex is formatted with a header, so we can import this as a dictionary
    '''
    rows = []
    
    with open(statement_csv, 'r') as csvfile:
        reader = csv.DictReader(csvfile, skipinitialspace=True)
        for row in reader:
            # TODO: There's got to be a more pythonic way to do this. 
            rows.append({
                'Date': row.get('Date'), 
                'Amount': row.get('Amount'), 
                'Description': row.get('Description')
            })
            
    return rows


def import_chase_transactions(statement_csv) -> list:
    rows = []
    
    with open(statement_csv, 'r') as csvfile:
        reader = csv.DictReader(csvfile, skipinitialspace=True)
        for row in reader:
            # TODO: There's got to be a more pythonic way to do this. 
            rows.append({
                'Date': row.get('Transaction Date'), 
                'Amount': row.get('Amount'), 
                'Description': row.get('Description')
            })
            
    return rows
