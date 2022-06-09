# MBTA-coop-documentation
documentation for all of my work with the MBTA in the spring semester

# IOH by Date project
Most of these run on a directory of CSV files. These files are taken from Excel files (.xlsx files) that have been converted to CSV's. Each of these files represents 1 quarter of transactions at the MBTA. 

Notesbooks:
- Running Total by SKU: gets the final quantity on hand of each SKU, and checks this against a validated dataframe of SKU:quantity.
- IOHbyDate: similar to Running Total by SKU, but for cost instead of quantity. 
- Value of IOH on hand: This file is key. This is what calculates the value of the inventory on hand by month since 2004. 

Python files:
- get_inventory_by_date.py: Prints the value on hand at the specified date. The date can be changed from within the file. This runs on CSV files, which can be 
- get_full_dataframe.py: processes and assembles all of the CSV files into one transaction dataframe, and outputs it as full_dataframe.tsv
- Value of IOH.py: the same thing as Value of IOH on hand, but as a python script.
- Running Total by SKU.py: same thing as Running Total by SKU, but as a python script. 
- get_sku_quantity.py: a stub. This doesn't appear to do anything meaningful. 

This calculation is key to understanding this:

Qty Offset on total transaction =Start Qty + 041 + 022 + 024 - 031 + 050 - (051 + 054) + 010 + 020 - 030 - End Qty

Each transaction type has its own sign to use when calculating the end quantity, and this gives it. Essentially, you want to subtract outgoing transactions and add incoming transactions. 

# Min/Max Project

# Stockouts Project

# Tableau Translit Project

Only what is in "Trello API Analysis" is actually workable. The other files are stubs.

trello_to_csv.py contains a finalized version of the trello->csv code. The notebooks (Trello To CSV.ipynb and Trello To CSV New.ipynb) were just used for development. 

Rays Trello Board.json is the raw data, and the two csv files in this directory are simply outputs of the trello to csv script. 

# Ducktape Rewrite (aborted due to selenium bug)
