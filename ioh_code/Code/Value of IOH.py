#!/usr/bin/env python
# coding: utf-8




#!/usr/bin/env python
# coding: utf-8

from lib2to3.pytree import convert
import pandas
import numpy as np
from datetime import datetime
import os

#from tqdm import tqdm

os.chdir("/Users/pbenson/Documents/IOH project/")

txn_dirPath = 'Data/'


txn_converter = {'TXN - Transaction Type': str,
                 'TXN - Transaction Date': str,
                 'TXN - Item ID': str,
                 'TXN - Qty': float,
                 'TXN - Total Cost': float}

transaction_col = ['TXN - Transaction Type', 'TXN - Transaction Date',
                   'TXN - Item ID', 'TXN - Qty', 'TXN - Total Cost', 'TXN - Adjust Type']

out_types = ('051', '054', '030', '031')
positive_types = (41, 22, 24, 50, 10, 20)
drop_types = ('060', '053', '052', '012', '001', '042')

#date = '2021-12-31 23:59:59'

def get_lof_csv(directory):
    lof = []
    for file in os.listdir(directory):
        if file.endswith('.csv'):
            lof.append(directory + file)
            print("Read file {}".format(file))
    return lof

def read_csv_to_df(lof, converter):
    print("Converting to pandas dataframe")

    dataframe = pandas.DataFrame()

    # More efficient way to do this: pd.concat
    next_txns = []
    for f in lof:
        next_txn = pandas.read_csv(f, converters=converter, encoding= 'unicode_escape')
        next_txns.append(next_txn)
        #dataframe = dataframe.append(next_txn, ignore_index=True)
        print(f + ' is appened')
    dataframe = pandas.concat(next_txns, ignore_index=True)
    return dataframe

def handle_I_D(txn_df):
    txn_df['TXN - Qty'] = np.where(txn_df['TXN - Adjust Type'] == 'D', 0 - abs(txn_df['TXN - Qty']),
                                   txn_df['TXN - Qty'])
    txn_df['TXN - Qty'] = np.where(txn_df['TXN - Adjust Type'] == 'M', 0 - abs(txn_df['TXN - Qty']),
                                   txn_df['TXN - Qty'])
    txn_df['TXN - Total Cost'] = np.where(txn_df['TXN - Adjust Type'] == 'D', 0 - abs(txn_df['TXN - Total Cost']),
                                          txn_df['TXN - Total Cost'])
    txn_df['TXN - Total Cost'] = np.where(txn_df['TXN - Adjust Type'] == 'M', 0 - abs(txn_df['TXN - Total Cost']),
                                          txn_df['TXN - Total Cost'])
    
    
    for t_type in out_types: 
        txn_df.loc[txn_df['TXN - Transaction Type'] == t_type, 'TXN - Qty'] = 0 - abs(txn_df['TXN - Qty'])
        txn_df.loc[txn_df['TXN - Transaction Type'] == t_type, 'TXN - Total Cost'] = 0 - abs(txn_df['TXN - Total Cost'])

    for t_type in drop_types:
        txn_df.loc[txn_df['TXN - Transaction Type'] == t_type, 'TXN - Qty'] = 0 
        txn_df.loc[txn_df['TXN - Transaction Type'] == t_type, 'TXN - Total Cost'] = 0
    
    # Trust Anni's Code – it has already been validated.

    # We don't want to drop columns.
    #txn_df = txn_df.drop(columns=['TXN - Transaction Type', 'TXN - Adjust Type'])
    return txn_df

def read_txn_by_date(txn_df, date):
    txn_df = txn_df.loc[txn_df['TXN - Transaction Date'] < date]
    #txn_df = txn_df.drop(columns=['TXN - Transaction Date'])
    # We don't want to drop the Transaction Date column.
    return txn_df

def sum_by_date(txn_df, date):
    txn_df = txn_df.loc[txn_df['TXN - Transaction Date'] < date]
    #txn_df = txn_df.drop(columns=['TXN - Transaction Date'])
    # We don't want to drop the Transaction Date column.
    return txn_df["TXN - Total Cost"].sum()

def sku_running_total(txn_df: pandas.DataFrame, item_sku: str) -> float:
    return txn_df.loc[txn_df['TXN - Item ID'] == item_sku, ('TXN - Qty', 'TXN - Transaction Type')]

def thousand_places(number):
    # Simple function for formatting large number outputs
    number = round(number, 2)
    return "{:,}".format(number)

def validate_skus(txn_df):
    # Process txn_df into sku_sum dataframe
    sku_sums = txn_df.groupby(['TXN - Item ID'])['TXN - Qty'].sum()
    
    # Read in and process valid SKU's
    valid_sku_sums_df = pandas.read_csv('Data/Valid_End_Quantities.csv')
    
    valid_sku_sums_df.columns = valid_sku_sums_df.iloc[0] 
    valid_sku_sums_df = valid_sku_sums_df[1:]
    
    valid_sku_sums_df["IOH - Qty On Hand"] = pandas.to_numeric(valid_sku_sums_df["IOH - Qty On Hand"])
    valid_sku_sums_df.rename(columns={'IOH - Item ID':'TXN - Item ID'}, inplace=True)
    
    valid_sku_sums = valid_sku_sums_df.groupby(['TXN - Item ID'])['IOH - Qty On Hand'].sum().to_frame()
    
    
    # Merge SKU sums dataframes
    merged_sku_sums = valid_sku_sums.join(other=sku_sums, on='TXN - Item ID')
    merged_sku_sums.reset_index(inplace=True)
    merged_sku_sums.rename(columns={'index':'TXN - Item ID'}, inplace=True)
    
    merged_sku_sums['TXN - Qty'].fillna(0, inplace=True)
    
    # Calculate difference
    merged_sku_sums['Qty Difference'] = merged_sku_sums['IOH - Qty On Hand'] - merged_sku_sums['TXN - Qty']
    
    return merged_sku_sums

def get_valid_percent(merged_skus):
    return (len(merged_skus) - len(merged_skus.loc[merged_skus['Qty Difference'] != 0])) / len(merged_skus)





txn_df = read_csv_to_df(get_lof_csv(txn_dirPath + "CSV_Files/"), txn_converter)


dataframe = txn_df.copy(deep = True) 

# # drop duplication
dataframe = dataframe.drop_duplicates()
# # filter dataframe
dataframe = dataframe.loc[dataframe['TXN - Transaction Type'].isin(['010', '020', '022', '024', '030', '031', '041', '050', '051', '054'])]
#dataframe

#print("Filtering by date")
#dataframe = read_txn_by_date(dataframe,date)
#print(dataframe.loc[dataframe['TXN - Transaction Type'] == '031', 'TXN - Qty'])
print("Handling ID")

dataframe = handle_I_D(dataframe)
#print(dataframe.loc[dataframe['TXN - Transaction Type'] == '031', 'TXN - Qty'])
#dataframe.loc[dataframe['TXN - Transaction Type'] == '031', 'TXN - Qty'] = 0 - abs(dataframe['TXN - Qty'])
#print(dataframe.loc[dataframe['TXN - Transaction Type'] == '031', 'TXN - Qty'])


print("Balance for 00250052:")
print("Sum:", sku_running_total(dataframe, "00250052")['TXN - Qty'].sum())

print("Balance for 42082077:", sku_running_total(dataframe, "42082077")['TXN - Qty'].sum())

print("Balance for 00250066:", sku_running_total(dataframe, "00250066")['TXN - Qty'].sum())


# Process: 
# - load all csv's 
# - Deep copy/drop duplicates
# - Run new handle_I_D function, don't filter by date
# - Run sku_running_total\['TXN-Qty'\].sum()

### Dump SKU Quantities to csv

# TODO for 1/28/22: Get end quantities for every SKU.

sku_counts = dataframe.groupby(['TXN - Item ID'])['TXN - Qty'].sum()

print("Validating SKU Counts")
print(get_valid_percent(validate_skus(dataframe)))

# This line is very important. This is the actual calculation for Total Cost.
dataframe['Updated_Total_Cost'] = dataframe['TXN - Qty'] * dataframe['TXN - Avg Matl Cost']

#dataframe.groupby('TXN - Item ID')['TXN - Qty'].sum().min()

print('Total Value of Inventory On Hand: (Updated Cost)', thousand_places(sum(dataframe.groupby('TXN - Item ID')['Updated_Total_Cost'].sum())))





# This script uses the old Total Cost
print('Total Value of Inventory On Hand: (Old Cost)', thousand_places(sum(dataframe.groupby('TXN - Item ID')['TXN - Total Cost'].sum())))


# Helper functions for processing the Total Value
def total_ioh_value(txn_df):
    txn_df = handle_I_D(txn_df)
    
    txn_df['Updated_Total_Cost'] = txn_df['TXN - Qty'] * txn_df['TXN - Avg Matl Cost']
    return sum(txn_df.groupby('TXN - Item ID')['Updated_Total_Cost'].sum())


def get_ioh_by_date(txn_df, filter_date):
    # Assume date is in format 'm d Y'
    filter_date_formatted = datetime.strptime(filter_date, '%m/%d/%Y')
    
    # Filter by date. Convert txn_df['TXN - Transaction Date'] and 'filter_date' to a usable date format
    txn_df['TXN - Transaction Date'] = pandas.to_datetime(txn_df['TXN - Transaction Date'])
    
    txn_df_filtered = txn_df.loc[txn_df['TXN - Transaction Date'] < filter_date_formatted]
    
    # Call total_ioh_value
    
    return total_ioh_value(txn_df_filtered)

# txn_df is the dataframe, date_list is a list of strings in m/d/Y date format
def get_ioh_multiple_dates(txn_df, date_list):
    ioh_by_day = {}
    
    for i in range(len(date_list)):
        date_list[i] = datetime.strptime(date_list[i], '%m/%d/%Y')
        #print(type(date))
    # Sort date_list
    start_date = datetime.strptime('1/1/2004', '%m/%d/%Y')
    
    date_list.sort()
    
    # Convert dataframe date column to datetime.
    txn_df['TXN - Transaction Date'] = pandas.to_datetime(txn_df['TXN - Transaction Date'])
    
    # Calculate IOH for the first date. This will become the basis for the subsequent calculations.
    txn_df_filtered = txn_df.loc[txn_df['TXN - Transaction Date'] < date_list[0]]
    
    # Call total_ioh_value
    ioh_by_day[date_list[0].strftime('%m/%d/%Y')] = total_ioh_value(txn_df_filtered)
    
    # Iterate through the rest of the dates
    for i in range(1, len(date_list)):
        #print(date_list[i], date_list[i-1])
        filtered_df = txn_df.loc[(txn_df['TXN - Transaction Date'] < date_list[i]) & (txn_df['TXN - Transaction Date'] >= date_list[i-1])]
        
        ioh_by_day[date_list[i].strftime('%m/%d/%Y')] = ioh_by_day[date_list[i-1].strftime('%m/%d/%Y')] + total_ioh_value(filtered_df)
    
    return ioh_by_day

print(get_ioh_multiple_dates(dataframe, ['1/1/2005', '1/1/2006', '1/1/2009']))

print(get_ioh_multiple_dates(dataframe, ['1/1/2005', '10/1/2006']))

print(get_ioh_multiple_dates(dataframe, ['1/1/2005', '1/1/2006', '1/1/2009', '3/1/2020', '1/1/2021']))

print(get_ioh_by_date(dataframe, '3/1/2020'))

print(get_ioh_by_date(dataframe, '1/1/2021'))


# David wants a list of the numbers by the end of the month since 2004 (Use 1st of every month because it's exclusive). Dump this to txt file.

months_since_2004 = []

for i in range(2004, 2021):
    for j in range(1, 13):
        months_since_2004.append("{}/1/{}".format(j, i))

months_since_2004.append('1/1/2021')
    
all_months_dict = get_ioh_multiple_dates(dataframe, months_since_2004)

months_df = pandas.DataFrame.from_dict({'date': all_months_dict.keys(), 'Inventory On Hand value': all_months_dict.values()})

months_df.loc[months_df['date'] == '03/01/2020']

months_df = months_df.round(decimals=3)
#list(months_df['Inventory On Hand value'])

months_df.to_csv('/Users/pbenson/Documents/IOH project/IOH_by_month.csv')