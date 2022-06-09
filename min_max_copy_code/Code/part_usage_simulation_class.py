import pandas as pd
import numpy as np
import os
import datetime
import bisect

class item_current_qoh_model:
    def __init__(self, item_dict) -> None:
        self.current_qoh_dict = item_dict
        # Item : base : qoh

        # Average QOH
        self.average_qoh = {}
        # item : average qoh
        # calculated by summing, then dividing at the end of the simulation by how many days passed. 
        
        # Stockouts at Central:
        self.central_stockouts = {}
        # item : stockouts

        print('Created Model.')

    def run_simulation(self, full_transaction_df, leadtime_df, min_roq_df, start_date, end_date):
        # Don't iterate thourgh each day. Run each item separately. 
        self.min_roq_df = min_roq_df
        self.leadtime_df = leadtime_df

        # Rename full_transaction_df columns
        renamed_txn_df = full_transaction_df.rename(columns={'TXN - Unit': 'Base', 'TXN - Qty':'Qty', 'TXN - Transaction Date':'Date'})

        print(renamed_txn_df)
            
        # Create events list for each item.
        for item in self.current_qoh_dict:
            # Create event list, then iterate through it

            item_event_list = self.create_event_list(item, renamed_txn_df, start_date, end_date)
            # leadtime events are added later
            #print(item_event_list)

            self.run_item_simulation(item, item_event_list)

    
    def run_item_simulation(self, item, item_event_list):
        # This kind of iteration will probably through a bug 
        i = 0
        while i < len(item_event_list):
            
            
            # Calculate average QoH
            if i > 0:
                days_difference = item_event_list[i]['Date'] - item_event_list[i-1]['Date']
                
                if days_difference.days > 0:
                    if item in self.average_qoh:
                        self.average_qoh[item] += sum(self.current_qoh_dict[item].values()) / days_difference.days
                    else:
                        self.average_qoh[item] = sum(self.current_qoh_dict[item].values()) / days_difference.days
            
            item_event_to_process = item_event_list[i]
            temp_length = len(item_event_list)
    
            self.process_item_event(item, item_event_to_process, item_event_list) 
            # This function is adding a duplicate to the item event list
            
            #print(i, item_event_list[i], len(item_event_list))
            #print('\n')
            #print(item_event_list)
            
            i += 1

    def create_event_list(self, item, txn_df, start_date, end_date):
        # Gets only the transactions for the specified item, in the right timeframe.
        temp_txn_df = txn_df.loc[(txn_df['TXN - Item ID'] == item) & (txn_df['Date'] >= start_date) & (txn_df['Date'] <= end_date)]

        # Convert to records, sort by transaction date
        final_list = sorted(temp_txn_df.to_dict('records'), key=lambda txn:txn['Date'])
        # This is a dict of out transactions, which includes Item ID, Base, Quantity (out qty), and date

        # Go through final_list and flip the sign of the quantity
        for entry in final_list:
            entry['Qty'] = -1 * entry['Qty']

        return final_list
    
    def process_item_event(self, item, item_event, item_event_list):
        self.current_qoh_dict[item][item_event['Base']] += item_event['Qty']

        # Check for stockouts, check for reorders
        # Also check for base replenishment
        if self.current_qoh_dict[item][item_event['Base']] < 0:
            self.current_qoh_dict[item][item_event['Base']] = 0
        
        
        if item_event['Base'] != 'CS004':
            if self.current_qoh_dict[item][item_event['Base']] <= self.get_base_min(item_event['Base'], item):
                #print('Base reorder at: ')
                #print(self.current_qoh_dict[item][item_event['Base']])
                # reorder from base 
                self.base_transfer(item_event['Base'], item, self.get_base_roq(item_event['Base'], item), item_event['Date'], item_event_list)
        else:
            if self.current_qoh_dict[item]['CS004'] <= self.get_central_min(item):
                self.order_parts(item, item_event['Date'], item_event_list)
        
    def add_item_event(self, item_event, item_event_list):
        # Add the item event in the proper place
        for i in range(len(item_event_list)):
            if item_event_list[i]['Date'] > item_event['Date']:
                item_event_list.insert(i, item_event)
                break

    def get_most_recent_leadtime(self, item, date):
        # Gets the leadtime to use for replenishment 
        
        # Filter leadtime df to just this item, and all transactions before min_reach_date
        
        temp_lt_df = self.leadtime_df.loc[(self.leadtime_df['TXN - Item ID'] == item) & (self.leadtime_df['PO Date'] < date)]
        
        if len(list(temp_lt_df.sort_values(by='PO Date', ascending = False)['Lead Time'])) > 0:
            leadtime_to_use = list(temp_lt_df.sort_values(by='PO Date', ascending = False)['Lead Time'])[0]
        else:
            # heuristic: if leadtime isn't here, just use a month.
            leadtime_to_use = 30
        
        return leadtime_to_use
    
    def order_parts(self, item, date, item_event_list):
        leadtime = datetime.timedelta(days = self.get_most_recent_leadtime(item, date))

        # Insert into the item event list (inplace?)
        # Insert so that the item is sorted properly
        item_order_event = {'TXN - Item ID' : item,
                            'Base': 'CS004',
                            'Date': date + leadtime,
                            'Qty': self.get_central_roq(item)}

        # Add the order to the list of events
        #print('Item Order: ', item_order_event)
        self.add_item_event(item_order_event, item_event_list)
    
    def base_transfer(self, base, item, qty, date, item_event_list):
        # instantaneous base transfer

        if self.current_qoh_dict[item]['CS004'] <= qty:
            self.current_qoh_dict[item][base] += self.current_qoh_dict[item]['CS004']
            self.current_qoh_dict[item]['CS004'] = 0
            
            # log stockouts
            if item in self.central_stockouts:
                self.central_stockouts[item] += 1
            else:
                self.central_stockouts[item] = 1
        else:
            self.current_qoh_dict[item][base] += qty
            self.current_qoh_dict[item]['CS004'] -= qty

        if self.current_qoh_dict[item]['CS004'] <= self.get_central_min(item):
            # Trigger central reorder event
            self.order_parts(item, date, item_event_list)

    # Get min and roq for base/items
    def get_central_min(self, item):
        #print(item)
        return self.min_roq_df.loc[(self.min_roq_df['TXN - Item ID'] == item)].head(1)['central_min'].item()

    def get_central_roq(self, item):
        return self.min_roq_df.loc[(self.min_roq_df['TXN - Item ID'] == item)].head(1)['central_roq'].item()

    def get_base_min(self, base, item):
        return self.min_roq_df.loc[(self.min_roq_df['TXN - Item ID'] == item) & (self.min_roq_df['Base'] == base)]['base_min'].item()
    
    def get_base_roq(self, base, item):
        return self.min_roq_df.loc[(self.min_roq_df['TXN - Item ID'] == item) & (self.min_roq_df['Base'] == base)]['base_roq'].item()
        
    def __repr__(self) -> str:
        final_string = ''
        final_string += 'Average QOH:\n' + str(self.average_qoh)
        final_string += '\nCentral Stockouts:\n' + str(self.central_stockouts)
        return final_string