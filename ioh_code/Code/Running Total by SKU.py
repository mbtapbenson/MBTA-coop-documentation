#!/usr/bin/env python
# coding: utf-8

from lib2to3.pytree import convert
import pandas
import numpy as np
import datetime
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
"""

full_dataframe_path = "Data/full_dataframe.tsv"

# Tab-separated is a better bet than csv.
print("Reading Dataframe")
dataframe = pandas.read_csv(full_dataframe_path, converters=txn_converter, sep="\t")

print(dataframe.head(10))
"""

# NOTE: this program seems to work fine when building the dataframe from scratch (using the csv files). 
# However, it fails when trying to build from the exported version of the same dataframe (full_dataframe.tsv). 
# I suspect there is slight deviation during export/import

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

print("Dumping SKU counts to dataframe")
sku_counts.to_csv("Data/unique_sku_counts.tsv", sep = "\t")