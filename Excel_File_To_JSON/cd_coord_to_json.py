import os
import pandas as pd
import json

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)


def read_excel_file(excel_file_path):
    # Read the Excel file
    df = pd.read_excel(excel_file_path, sheet_name='CD Coordinate', header=None, usecols=None)
    return df

    
def cd_coordinates_worksheet_to_dict(df):

    # Get the patterns as column names
    main_row = {}
    for keys in ['Device','Layer','Tool']:
        row = df[df[1] == keys].index[0]
        main_row.update({keys : str(df.loc[row, 2])})
    start_row = df[df[1] == 'Information'].index[0]
    start_col = df.columns.get_loc(1)
    patterns = list(df.iloc[start_row, start_col+2:])
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
        
    new_pattern = []
    for pat in patterns:
        new_pattern.append(pat+'##X')
        new_pattern.append(pat+'##Y')
            
    # Define column names
    column_names = new_pattern
    
    # Slice the table from the start row and column
    table = df.iloc[start_row:, start_col+2:]
    
    # Drop the first row of the table : pattern names
    table = table.iloc[1:].reset_index(drop=True)
    # Drop the first row of the table : x y names
    table = table.iloc[1:].reset_index(drop=True)
    

    # Rename columns
    table.columns = column_names

    # Reset the index to ensure all values are unique
    table = table.reset_index(drop=True)

    new_row = {}
    for pat in patterns:
        x_col = pat + '##X'
        y_col = pat + '##Y'
        x = table[x_col].dropna()
        y = table[y_col].dropna()
        xy_list = list(zip(x, y))
        new_row[pat] = xy_list
    
    new_row.update(main_row)
    
    # Return the JSON object
    return new_row


def main(excel_file_path, json_file_path):
    # Normalize input file path
    excel_file = os.path.normpath(excel_file_path)

    # Read Excel file and create category tables
    df = read_excel_file(excel_file)
    json_data = cd_coordinates_worksheet_to_dict(df)
    # Save JSON data to file
    with open(json_file_path, 'w') as f:
        json.dump(json_data, f , indent=4)
    
    print(f"JSON_OUTPUT={json_file_path}")
