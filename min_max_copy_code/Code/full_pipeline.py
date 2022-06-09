
import pandas as pd
import numpy as np
from tqdm import tqdm
import datetime
import os
import matplotlib.pyplot as plt

pd.options.display.float_format = '{:.2f}'.format

os.chdir("/Users/pbenson/Documents/Min_Max_project/")

txn_dirPath = 'Data/'

txn_converter = {'TXN - Transaction Type': str,
                 'TXN - Transaction Date': str,
                 'TXN - Item ID': str,
                 'TXN - Qty': float,
                 'TXN - Total Cost': float}

def get_lof_csv(directory):
    lof = []
    for file in os.listdir(directory):
        if file.endswith('.csv'):
            lof.append(directory + file)
            print("Read file {}".format(file))
    return lof

def read_csv_to_df(lof, converter):
    print("Converting to pandas dataframe")

    dataframe = pd.DataFrame()

    # More efficient way to do this: pd.concat
    next_txns = []
    for f in lof:
        next_txn = pd.read_csv(f, converters=converter, encoding= 'unicode_escape')
        next_txns.append(next_txn)
        #dataframe = dataframe.append(next_txn, ignore_index=True)
        print(f + ' is appened')
    dataframe = pd.concat(next_txns, ignore_index=True)
    return dataframe

### 
# GLOBAL VARIABLES
# recency: how far back should we look at usage?
recency = 60
###

### Parameterization: 
# - TXN df path as an argument
# - recency, safety, and quarters per purchase as arguments
# - active part thresholds (years ago and number of txns)

txn_df = read_csv_to_df(get_lof_csv(txn_dirPath + "CSV_Files/"), txn_converter)

out_df = txn_df.loc[txn_df['TXN - Transaction Type'] == '030']
out_df['TXN - Transaction Date'] = pd.to_datetime(out_df['TXN - Transaction Date'])
out_df.rename(columns = {'TXN - Unit':'Base'}, inplace=True)

today = datetime.date.today()

last_2_years = out_df.copy(deep=True)

last_2_years['Today'] = today
last_2_years['Today'] = pd.to_datetime(last_2_years['Today'])
last_2_years['Years Ago'] = (last_2_years['TXN - Transaction Date'] - last_2_years['Today']).astype('timedelta64[Y]').astype('int')

# Need to find the usage in the past 2 years.
last_2_years_df = last_2_years.copy(deep=True)

last_2_years_df = last_2_years_df.loc[last_2_years_df['Years Ago'] >= -2]

print(last_2_years_df['Years Ago'].min())

part_usages = last_2_years_df.groupby('TXN - Item ID').size()
part_filter = part_usages > 5
in_parts = set(part_usages[part_filter].index)
print(len(in_parts))

final_part_df = last_2_years.loc[last_2_years['TXN - Item ID'].isin(in_parts)]

months_df = final_part_df.copy(deep=True)

# Bin to 3 months
start_date = datetime.datetime(2004, 1, 1)

months_df['Quarters'] = ((months_df['TXN - Transaction Date'] - start_date).astype('timedelta64[M]').astype('int') - 1) // 3

summed_quarters_active_parts = months_df.groupby(['TXN - Item ID', 'Base', 'Quarters'])['TXN - Qty'].sum()
summed_quarters_active_parts.to_frame()
summed_quarters_active_parts = summed_quarters_active_parts.reset_index()

number_of_txns_active = months_df.groupby(['TXN - Item ID', 'Base'])['TXN - Qty'].size()
number_of_txns_active.rename('transactions', inplace=True)
number_of_txns_active.to_frame()
number_of_txns_group = number_of_txns_active.reset_index()

recent_parts = summed_quarters_active_parts.loc[summed_quarters_active_parts['Quarters'] >= recency]
    
usage_mean = recent_parts.groupby(['TXN - Item ID', 'Base'])['TXN - Qty'].mean()
usage_std = recent_parts.groupby(['TXN - Item ID', 'Base'])['TXN - Qty'].std(ddof=0)

usage_mean.rename('base_usage_mean', inplace=True)
usage_std.rename('base_usage_std', inplace=True)

part_df = pd.concat([usage_mean, usage_std], axis=1)
part_df.reset_index(inplace=True)
part_df.rename(columns={'TXN - Unit':'Base'})

# Folding in number of transactions
part_df = part_df.merge(number_of_txns_group, how='left', on=['TXN - Item ID', 'Base'])

## Lead Time
print('factoring in lead time.')
lead_time_df = pd.read_excel(txn_dirPath + 'PB_RECEIPTS_V3B_KATE_557.xlsx', header=1)

lead_time_df['Recv Date'] = pd.to_datetime(lead_time_df['Recv Date'])
lead_time_df['PO Date'] = pd.to_datetime(lead_time_df['PO Date'])
lead_time_df['Lead Time'] = (lead_time_df['Recv Date'] - lead_time_df['PO Date']).astype('timedelta64[D]').astype('int')

# Filter by column
pure_lead_time_df = lead_time_df[['Lead Time', 'Inv_Item', 'PO Date']]

# Sum by Part
historical_lead_time = pure_lead_time_df.copy(deep = True)
historical_lead_time.rename(columns={'Inv_Item':'TXN - Item ID'}, inplace=True)

historical_lead_time['PO Date'] = pd.to_datetime(historical_lead_time['PO Date'])

recent_five_times = historical_lead_time.sort_values(by='PO Date', ascending=False).groupby('TXN - Item ID').head(5)
# Gets a dataframe of the mean leadtime for each part
recent_lead_times_df = recent_five_times.groupby('TXN - Item ID')['Lead Time'].mean() / 91.25
recent_lead_times_df = recent_lead_times_df.rename('leadtime_mean').to_frame().reset_index()
 
# Save historical lead times
historical_lead_time.to_csv('Data/historical_lead_time.csv')

part_df_with_lt = part_df.merge(recent_lead_times_df, how='left', on='TXN - Item ID')
# this would give mean usage by base for all parts, with lead times.

full_part_df = part_df_with_lt.copy(deep=True)

### –––––––––––––––
### MIN MAX GLOBAL VARIABLES
# safety: how many standard deviations should we add to the mean (when calculating MIN)?
safety = 2
# Quarters per purchase: how often should we be making big purchases?
quarters_per_purchase = 2
### –––––––––––––––

# Helper function to sum STDs. 
def rms(values):
    return np.sqrt(sum(values**2)/len(values))

# Calculate Central Min/max
central_means = full_part_df.groupby('TXN - Item ID')['base_usage_mean'].sum()
central_stds = full_part_df.groupby('TXN - Item ID')['base_usage_std'].apply(rms)

central_means.rename('central_usage_mean', inplace=True)
central_stds.rename('central_usage_std', inplace=True)

central_df = pd.concat([central_means, central_stds], axis=1)
central_df.reset_index(inplace=True)

print('Merging central usage with base usage')
full_part_df_with_central = full_part_df.merge(central_df, how='left', on='TXN - Item ID')

print('Calculating Min/ROQ')
# This is where the calculation takes place:
full_part_df_with_central['central_min'] = full_part_df_with_central['leadtime_mean'] * \
                    (full_part_df_with_central['central_usage_mean'] + (safety * full_part_df_with_central['central_usage_std']))

# We don't necessarily need to restock the min usage. 
full_part_df_with_central['central_roq'] = (quarters_per_purchase * full_part_df_with_central['central_usage_mean'])

# Calculate base-specific min/max 
# BASE MIN = 3 days of usage = Base Quarterly usage / 30
# BASE ROQ = 1 month of usage = Base Quarterly Usage / 3
full_part_df_with_central['base_min'] = full_part_df_with_central['base_usage_mean'] / 30

full_part_df_with_central['base_roq'] = full_part_df_with_central['base_usage_mean'] / 3

print('Incorporating FMIS data')
# Incorporate FMIS data
fmis_parts = pd.read_csv('Data/KJ_INV_BY_BASE.csv', encoding='unicode_escape')

# Filter fmis_parts to only active parts, drop last Ann, Util Type, Descr, Descr.1, Descr.2, $LTM demand.
fmis_parts.drop(columns=['Last Ann', 'Util Type', '$ LTM Demand', 'Descr', 'Descr.1', 'Descr.2'], inplace=True)

fmis_parts_filtered = fmis_parts.loc[fmis_parts['Status Current'] == 'Active']
fmis_parts_filtered.drop(columns = 'Status Current', inplace=True)

fmis_parts_filtered.rename(columns={'Unit':'Base', 'Item':'TXN - Item ID', 'Reorder Pt':'fmis_min', 'Reord Qty':'fmis_roq'}, inplace=True)

full_base_part_df_with_fmis = full_part_df_with_central.merge(fmis_parts_filtered, on=['TXN - Item ID', 'Base'], how='left')

full_base_part_df_with_fmis['base_min'] = round(full_base_part_df_with_fmis['base_min'])
full_base_part_df_with_fmis['base_roq'] = round(full_base_part_df_with_fmis['base_roq'])
full_base_part_df_with_fmis['central_min'] = round(full_base_part_df_with_fmis['central_min'])
full_base_part_df_with_fmis['central_roq'] = round(full_base_part_df_with_fmis['central_roq'])

print('Done, exporting full dataframe.')
# At this point, full_base_part_df_with_fmis is complete. 

full_base_part_df_with_fmis.to_csv('Data/full_part_df_with_fmis.csv')