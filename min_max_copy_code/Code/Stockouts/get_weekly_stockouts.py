import pandas as pd
import numpy as np
import datetime

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
    
def filter_stockouts(stockout_df, usage_column, exclude_groups):
    temp_stock_df = stockout_df.copy(deep=True)
        
    temp_stock_df['filter'] = temp_stock_df.apply(stockout_filter, args=(usage_column, exclude_groups), axis=1)
    
    filtered_df = temp_stock_df.loc[temp_stock_df['filter'] == True]
    filtered_df.drop('filter', axis=1, inplace=True)
    
    return filtered_df

stockout_df_path = '/Users/pbenson/Documents/Min_Max_Project/Data/Stockouts/weekly_stockouts/WH_STOCKOUTS.csv'
usage_df_path = '/Users/pbenson/Documents/Min_Max_Project/Data/Stockouts/full_usage_df.csv'

stockout_df = pd.read_csv(stockout_df_path, converters={'Item': str})
usage_df = pd.read_csv(usage_df_path, index_col = 0, converters={'TXN - Item ID': str})

filtered_stockouts = stockout_df[['Item', 'Item Group', 'Status Current', 'No Repl', 'Reorder Pt', 'Max Qty', 'Reord Qty', 'Trans Date']]
stockouts_with_usage = filtered_stockouts.merge(usage_df, how='left', left_on='Item', right_on='TXN - Item ID')

stockouts_with_usage.drop('TXN - Item ID', axis=1, inplace=True)

stockouts_with_usage = stockouts_with_usage.fillna(0)

# Filter step
week_real_stockouts = filter_stockouts(stockouts_with_usage, 'usage_5_years', [])

week_real_stockouts.reset_index(inplace=True)
week_report = week_real_stockouts[['Item', 'Item Group', 'Trans Date']].drop_duplicates().reset_index().drop('index', axis=1)
# Note: dropping duplicates here makes it so that each item can only stock out once per day at max.

today = datetime.date.today().strftime("%m%d%Y")

week_report.to_csv('/Users/pbenson/Documents/Min_Max_Project/Data/Stockouts/weekly_stockouts/report_' + today + '.csv')