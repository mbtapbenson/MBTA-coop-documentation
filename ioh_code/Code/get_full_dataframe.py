
# coding: utf-8


from sqlite3 import converters
import pandas
import datetime
import numpy as np
import os
#import sys


out_types = ('051', '054', '030', '031')

d = '2021-11-01 00:00:00'

# From Anni's code, this is the directory that contains the txn (excel files)
#txn_dirPath = '/Users/ayuan2/Desktop/Discrepancy/txn_since_2004/'
os.chdir("/Users/pbenson/Documents/IOH project/")

txn_dirPath = 'Data/'


txn_converter = {'TXN - Transaction Type': str,
                 'TXN - Transaction Date': str,
                 'TXN - Item ID': str,
                 'TXN - Qty': float,
                 'TXN - Total Cost': float}

transaction_col = ['TXN - Transaction Type', 'TXN - Transaction Date',
                   'TXN - Item ID', 'TXN - Qty', 'TXN - Total Cost', 'TXN - Adjust Type']

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
    
    # Trust Anni's Code – it has already been validated.

    # We don't want to drop columns.
    #txn_df = txn_df.drop(columns=['TXN - Transaction Type', 'TXN - Adjust Type'])
    return txn_df

print("reading csv files")
#txn_df = read_txn_to_df(get_lof(txn_dirPath), txn_converter)
# Replace this with reading the csv's.

txn_df = read_csv_to_df(get_lof_csv(txn_dirPath + "CSV_Files/"), txn_converter)


dataframe = txn_df.copy(deep = True) 

# Select columns
dataframe = dataframe[transaction_col]
# # drop duplication
dataframe = dataframe.drop_duplicates()
# # filter dataframe
dataframe = dataframe.loc[dataframe['TXN - Transaction Type'].isin(['010', '020', '022', '024', '030', '031', '041', '050', '051', '054'])]
#dataframe

dataframe = handle_I_D(dataframe)

# Export the dataframe
dataframe.to_csv("Data/full_dataframe.tsv", sep="\t")

