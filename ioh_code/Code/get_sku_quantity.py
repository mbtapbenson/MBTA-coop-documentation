import pandas
import datetime
import numpy as np
from sqlalchemy import engine
from tqdm import tqdm
import numba

transaction_col = ['TXN - Transaction Type', 'TXN - Transaction Date',
                   'TXN - Item ID', 'TXN - Qty', 'TXN - Total Cost', 'TXN - Adjust Type']

out_types = ('051', '054', '030', '031')
positive_types = (41, 22, 24, 50, 10, 20)
drop_types = (53, 12)

date = '2021-12-31 23:59:59'

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

def thousand_places(number):
    # Simple function for formatting large number outputs
    return "{:,}".format(number)

def sku_running_total(txn_df: pandas.DataFrame, item_sku: str) -> float:
    return txn_df.loc[txn_df['TXN - Item ID'] == item_sku, 'TXN - Qty'].to_numpy().sum()

full_dataframe_path = "Data/full_dataframe.tsv"

# Tab-separated is a better bet than csv.
print("Reading Dataframe")
dataframe = pandas.read_csv(full_dataframe_path, sep="\t")

print("Adjusting by Transaction Codes")

# We don't need to filter out by date right now.
#dataframe = read_txn_by_date(dataframe,date)
dataframe = handle_I_D(dataframe)



print("Done testing SKU totals.\n")

