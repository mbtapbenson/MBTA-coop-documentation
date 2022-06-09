import pandas
import datetime
import numpy as np
from sqlalchemy import engine
from tqdm import tqdm
import numba

transaction_col = ['TXN - Transaction Type', 'TXN - Transaction Date',
                   'TXN - Item ID', 'TXN - Qty', 'TXN - Total Cost', 'TXN - Adjust Type']

out_types = (51, 54, 30, 31)
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
    
    txn_df.loc[txn_df['TXN - Transaction Type'].isin(out_types), 'TXN - Qty'] = 0 - abs(txn_df['TXN - Qty'])
    txn_df.loc[txn_df['TXN - Transaction Type'].isin(out_types), 'TXN - Total Cost'] = 0 - abs(txn_df['TXN - Total Cost'])

    txn_df.loc[txn_df['TXN - Transaction Type'].isin(drop_types), 'TXN - Qty'] = 0
    txn_df.loc[txn_df['TXN - Transaction Type'].isin(drop_types), 'TXN - Total Cost'] = 0

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

print("Filtering by date")
dataframe = read_txn_by_date(dataframe,date)
dataframe = handle_I_D(dataframe)

print("Testing SKU running totals:")
sku_df = dataframe.copy(deep=True) 
sku_df = sku_df[["TXN - Item ID", "TXN - Qty", "TXN - Total Cost"]]

sku_totals = sku_df.groupby(["TXN - Item ID"]).sum()

print("Done testing SKU totals.\n")

print("Qty Total by SKU:", sum(sku_totals["TXN - Qty"]))
print("Cost Total by SKU:", sum(sku_totals["TXN - Total Cost"]))
print("Number of unbalanced SKUs: ", len(sku_totals))


print('Date: ' + date)

print("Running total:",  thousand_places(round(dataframe["TXN - Total Cost"].sum(), 2)))
print("Running Qty total:",  thousand_places(round(dataframe["TXN - Qty"].sum(), 2)))
print("unique TXN types:", dataframe['TXN - Transaction Type'].unique())
#print("Minimum of 030:", min(dataframe.loc[dataframe['TXN - Transaction Type'] == 30, 'TXN - Qty']))

print ("\nUnique SKU's:")
print(dataframe["TXN - Item ID"].nunique())

txn_type_dict = {}

txn_types = (41, 22, 24, 31, 50, 51, 54, 10, 20, 30)
print("Total Value by Transaction Type:")
for type in txn_types:
    txn_type_dict[type] = dataframe.loc[dataframe['TXN - Transaction Type'] == type, 'TXN - Total Cost'].sum()
    print(type, thousand_places(round(dataframe.loc[dataframe['TXN - Transaction Type'] == type, 'TXN - Total Cost'].sum(), 2)))

print("020 + 010 + 030:", thousand_places(round(txn_type_dict[10] + txn_type_dict[20] + txn_type_dict[30], 2)))
print("22 + 31:", thousand_places(round(txn_type_dict[22] + txn_type_dict[31], 2)))

print("End balance:", thousand_places(round(dataframe['TXN - Qty'].sum(), 2)))