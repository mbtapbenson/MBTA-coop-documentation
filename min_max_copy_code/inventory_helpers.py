### 
# This is a collection of various helper functions I've found myself using during my time working with
# Procurement and Logistics data at the MBTA.
# By: Peter Benson
# Email: peterb2470@gmail.com

import pandas as pd
import numpy as np
import os
import datetime


# This is the triple filter for filtering out parts that are truly discontinued.
# Any one of these conditions will flag the part as discontinued. 
def discontinued_sku(row):
    return (row['No Repl'] == 'Y') or (row['Status Current'] == 'Discontinue') or \
    (row['Reorder Pt'] == 0 and row['Max Qty'] == 0 and row['Reord Qty'] == 0)

# This is a more complete stockout filter that also includes a usage column and item groups to exclude. 
def stockout_filter(row, usage_column, exclude_groups):
    # Filter out by Status, No Repl, and Reorder stuff
    if (row['No Repl'] == 'Y') or (row['Status Current'] == 'Discontinue') or \
    (row['Reorder Pt'] == 0 and row['Max Qty'] == 0 and row['Reord Qty'] == 0):
        return False 
    
    else:
        if row[usage_column] == 0:
            return False
        else:
            if row['Item Group'] in exclude_groups:
                return False
            else:
                return True
    # Filter out by usage.
    # Usage column = which column to check for usage. 
    
# This function takes in a stockout dataframe (from WH_STOCKOUTS) that has a usage column 
# (merged from get_monthly_usage) and filters it using stockout_filter.
def filter_stockouts(stockout_df, usage_column, exclude_groups):
    temp_stock_df = stockout_df.copy(deep=True)
        
    temp_stock_df['filter'] = temp_stock_df.apply(stockout_filter, args=(usage_column, exclude_groups), axis=1)
    
    filtered_df = temp_stock_df.loc[temp_stock_df['filter'] == True]
    filtered_df.drop('filter', axis=1, inplace=True)
    
    return filtered_df

# This reads in a tranascation dataframe (in the form of a CSV.) 
# At the beginning of Co-op, I appended all of the transasction dataframes into one. 
# This function filters to only the usage transactions and only the essential columns. 
# It also adds a "years ago" column, which is helpful later on.
def read_txn_df(dir_path):
    txn_converter = {'TXN - Transaction Type': str,
                 'TXN - Transaction Date': str,
                 'TXN - Item ID': str,
                 'TXN - Qty': float,
                 'TXN - Total Cost': float}
    
    print('Reading dataframe')
    txn_df = pd.read_csv(dir_path, converters=txn_converter, index_col=0)
    
    print('Filtering to Out TXN\'s')
    
    out_txns = txn_df.loc[txn_df['TXN - Transaction Type'] == '030']
    
    small_df = out_txns[['TXN - Item ID', 'TXN - Unit', 'TXN - Transaction Date', 'TXN - Qty']]
    
    small_df['TXN - Transaction Date'] = pd.to_datetime(small_df['TXN - Transaction Date'])
    small_df.rename(columns = {'TXN - Unit':'Base'}, inplace=True)

    print('Calculating dates')
    today = datetime.date.today()
    small_df['today'] = today
    small_df['today'] = pd.to_datetime(small_df['today'])
    small_df['years_ago'] = (small_df['today'] - small_df['TXN - Transaction Date']).astype('timedelta64[Y]').astype('int')
    small_df.drop('today', axis=1, inplace=True)
    
    return small_df

# This is when the years_ago columns comes in handy. This function calculates average monthly 
# usage over the last x years. 
def get_monthly_usage(txn_df, years_ago):
    
    recent_txns = txn_df.loc[txn_df['years_ago'] <= years_ago]
    
    recent_txns['TXN - Qty'] = abs(recent_txns['TXN - Qty'])
    
    year_factor = ((years_ago + 1) * 12)
    
    print(years_ago, year_factor)

    monthly_demand = recent_txns.groupby(['TXN - Item ID', 'years_ago'])['TXN - Qty'].sum().groupby('TXN - Item ID').sum() / year_factor
    
    monthly_demand_df = monthly_demand.to_frame().reset_index()
    monthly_demand_df.rename(columns={'TXN - Qty': 'mean_monthly_usage'}, inplace=True)
    
    return monthly_demand_df

# This function turns a transaction dataframe into an item group key. This is useful 
# for getting the actual item group of an item, because some items don't store the item group as
# the second two numbers of the SKU.
def get_item_group_key(dir_path):
    txn_converter = {'TXN - Transaction Type': str,
                 'TXN - Transaction Date': str,
                 'TXN - Item ID': str,
                 'TXN - Qty': float,
                 'TXN - Total Cost': float}
    
    print('Reading dataframe')
    txn_df = pd.read_csv(dir_path, converters=txn_converter, index_col=0)
    
    item_group_key = txn_df[['TXN - Item ID', 'TXN - Item Group']].drop_duplicates()
    
    return item_group_key

