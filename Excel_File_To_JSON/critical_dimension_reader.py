#!/usr/bin/env python
# coding: utf-8
# Cristopher Magalang - April 18 2023.
# Reading an excel file report in a formatted worksheet.


import os
import pandas as pd
import json

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)


def read_excel_file(excel_file_path):
    # Read the Excel file
    df = pd.read_excel(excel_file_path, sheet_name='Critical Dimension', header=None, usecols=None)
    return df

def combine_details_row(table, patterns):
    # Initialize the new row dictionary with default values
    new_row = {"Categories": "Detail", "SubCategory": "DetailsList"}

    try:
        # Filter the table to get only rows with "Categories" == "Detail"
        detail_rows = table[table['Categories'] == 'Detail']

        # Loop through the given patterns and extract the values for each
        for pat in patterns:
            # Use pandas Series.dropna() to remove any NaN values in the column
            foo_values = detail_rows[pat].dropna().values.tolist()

            # Update the new row dictionary with the extracted values for the pattern
            new_row.update({pat: foo_values})
    except Exception as e:
        # Handle any exceptions that may occur during the function execution
        print(f"Error occurred while combining detail rows: {e}")
        new_row = {}  # Return an empty dictionary if an error occurs

    return new_row


def combine_results_rows(table):
    pattern = 'Result'
    df = table[table['Categories'] == pattern]
    result_row = table[table['Categories'] == pattern]
    new_row = {"Categories": "Result", "SubCategory": "ResultsJson"}
    for col in df.columns[2:]:
        subcats = df['SubCategory'].unique()
        new_json = {}
        for subcat in subcats:
            val = df.loc[df['SubCategory'] ==subcat , col].iloc[0]
            new_json.update({subcat : val})
        new_row.update({col: json.dumps(new_json)})
    return new_row


def combine_specifications_rows(table):
    pattern = 'Specification'
    df = table[table['Categories'] == pattern]
    result_row = table[table['Categories'] == pattern]
    new_row = {"Categories": "Specification", "SubCategory": "SpecificationJson"}
    for col in df.columns[2:]:
        subcats = df['SubCategory'].unique()
        new_json = {}
        for subcat in subcats:
            val = df.loc[df['SubCategory'] ==subcat , col].iloc[0]
            new_json.update({subcat : val})
        new_row.update({col: json.dumps(new_json)})
    return new_row


def create_category_tables(df):

    # Get the patterns as column names
    main_row = {}
    for keys in ['Device','Layer','Tool']:
        row = df[df[1] == keys].index[0]
        main_row.update({keys : str(df.loc[row][2])})

    start_row = df[df[1] == 'Information'].index[0]
    start_col = df.columns.get_loc(1)
    patterns = list(df.iloc[start_row-1, start_col+1:])
    patterns = [x for x in patterns if str(x) != 'nan']
    if patterns[0] == 'No.':
        patterns.pop(0)

    item_count={}
    # Count the occurrences of each pattern item in the list
    for item in patterns:
        if item in item_count:
            item_count[item] += 1
        else:
            item_count[item] = 1

    # Append suffix to duplicates
    for i in range(len(patterns)):
        item = patterns[i]
        if item_count[item] > 1:
            suffix = '_#DUP_' + str(item_count[item] -1)
            patterns[i] = str(item) + suffix
            item_count[item] += 1

    # Define column names
    column_names = ['Categories', 'SubCategory'] + patterns

    # Slice the table from the start row and column
    table = df.iloc[start_row-1:, start_col:]

    # Drop the first row of the table
    table = table.iloc[1:].reset_index(drop=True)

    # Rename columns
    table.columns = column_names

    # Replace NaN values in Categories with the category name
    table['Categories'] = table['Categories'].fillna(method='ffill')

    # Reset the index to ensure all values are unique
    table = table.reset_index(drop=True)

    new_table = table
    # create a new dataframe with rows where Categories does not equal Detail, Result, or Specification
    for cat in ['Detail','Result','Specification']:
        new_table = new_table[new_table['Categories'] != cat].copy()
        

    # combine the "Detail" rows
    try:
        new_detail_row = combine_details_row(table,patterns)
        new_table = pd.concat([new_table, pd.DataFrame([new_detail_row])], ignore_index=True)
    except Exception as e:
        print(f"Detail Row Error: {str(e)}")

    # combine the "Result" rows
    try:
        new_result_row = combine_results_rows(table)
        new_table = pd.concat([new_table, pd.DataFrame([new_result_row])], ignore_index=True)
    except Exception as e:
        print(f"Result Row Error: {str(e)}")
        
    # combine the "Specifications" rows
    try:
        new_spec_row = combine_specifications_rows(table)
        new_table = pd.concat([new_table, pd.DataFrame([new_spec_row])], ignore_index=True)
    except Exception as e:
        print(f"Specifications Row Error: {str(e)}")
        
    return main_row,new_table
    
    
def generate_json_data(main_row,df):
    # Transpose the DataFrame
    dft = df.transpose()

    # Set the column names to the values in the second row
    column_names = list(dft.iloc[1])
    dft.columns = column_names

    # Remove the second row
    dft = dft.iloc[2:]

    # Reset the index
    dft = dft.reset_index(drop=True)

    # Convert the DataFrame to a dictionary
    d = dft.to_dict(orient='records')

    # Convert nested JSON data to dictionaries
    for row in d:
        for key, value in row.items():
            if isinstance(value, str):
                try:
                    row[key] = json.loads(value)
                except ValueError:
                    row[key] = value

    # Create the JSON object
    json_data = {row['Pattern']: row for row in d}
    json_data.update(main_row)

    # Return the JSON object
    return json_data


def main(excel_file_path, json_file_path):
    # Normalize input file path
    excel_file = os.path.normpath(excel_file_path)

    # Read Excel file and create category tables
    df = read_excel_file(excel_file)
    main_row , table = create_category_tables(df)
    
    # Generate JSON data from category tables
    json_data = generate_json_data(main_row, table)
    

    # Save JSON data to file
    with open(json_file_path, 'w') as f:
        json.dump(json_data, f , indent=4)

    print(f"JSON_OUTPUT={json_file_path}")
