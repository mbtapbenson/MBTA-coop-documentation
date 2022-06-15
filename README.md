# MBTA-coop-documentation
Hey! This is the documentation for all of my work with the MBTA in the spring semester of 2022. 
By Peter Benson
email: peterb2470@gmail.com

Feel free to shoot me an email if you have any questions! I'd be happy to help (or debug) one of my programs here! 

# IOH by Date project (https://github.com/mbtapbenson/IOHbyday.git)
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

This was by far my most expansive project while on Co-op. I was tasked with recalculating the warehouse min/maxes for our central storage location, CS004, and the bases. This was narrowed down to CS004, just for non-rail parts, and parts under $500. 

The basic formula is as such:

Let m = monthy usage and l = leadtime in months. 

$MIN = l * m$

$ROQ = 6 * m$. 

- Min_Max_notebook.ipynb: This was my first stab at this. At this point, the formula was more like $MIN = l * ((\alpha * \omega(m)) + m))$. The idea here was that the standard deviation of monthly usage would capture all of the exceptional scenarios that could be encountered. The $\alpha$ was a factor which I experimented with (around 1 or 2) to add more protection. In this notebook, I also developed the idea to only look at the past 2 years of usage. 
- Min Max with Lead Time.ipynb: This is when I folded in lead time. I also started binning transactions by quarters. At this point, I was also experimenting with adding in the leadtime standard deviation. This was extremely high for many parts, and often ballooned the min to unreasonable levels. This is also where I found that leadtimes are extremely left-skewed. I also tried a clumsy attempt at factoring in bases, before I realized I could achieve the same thing in one dataframe. 
- Compare to FMIS Min Max.ipynb: This is still from the first iteration of this project. In this notebook, I folded in the FMIS min/maxes for the first time. This is also when I was still using 031 codes, which is not right. 
- Base Dict.ipynb: Here, I converted from a dictionary to a dataframe for the bases. 
- 3_15_22_Base_analysis.ipynb: This was mainly an exploration of base-level data. Interesting tidbit from here - we transfer more parts to the bases than we actually use (031 > 030). 
- 3_22_22_Analysis_For_Takary.ipynb: This was great for a bunch of comparisons between the FMIS mins and my calculated ones. I also found that we aren't stocking many obsolete parts. 
- 6_7_cost_rail_filter.ipynb: This notebook just filtered out costs with a unit cost >$500 and parts that were rail parts. 
- full_pipeline.py: This condensed the full (old) min/roq calculation into one python file. 
- new_full_pipeline.py: This is empty, but was meant to capture the new min/roq calculation into one file. 
- Testing.ipynb: Not really sure what this was testing to be honest. 
- Part Usage Simulation.ipynb: this is where I developed the (now-defunct) part usage simulation. 
- part_usage_simulation_class.py: This contains a part simulation, which simulates real-world behavior of min/maxes and keeps track of average quantity on hand and number of stockouts. 
- Visualize Part Usage Simulation.ipynb: This visualizes the difference between different min/maxes that have run through the simulation. Ultimately, we didn't end up relying on the simulation as a source of truth.  

**IMPORTANT PART**
In these files, I refined the old calculation of min/max into what it is now. 
- New Min Max Calculation.ipynb: This is a super stripped down version of Min Max Calculation.ipynb, and is where I developed the new min/maxes. At this point, I was super familiar with the data, so this notebook flowed much smoother than the previous ones. An important note here is that instead of adding a min STD, I added 1 month onto the leadtime to compensate for buyer's time. In addition, since the buyers don't always purchase the exact ROQ, I added a 6 month ROQ as a proxy/placeholder. I also compared these values to the FMIS values. 
- New Min Max Uploads.ipynb: Takary wanted values for parts that weren't as active, as well as base-specific values. I used the same methodology as New Min Max Calculation, but applied it to those subsets of the data. 

# Stockouts Project

In the Stockouts folder (within the min max code folder):
- get_weekly_stockouts.py: This file is super straightforward. To run this, you must run a WH_STOCKOUTS query on the last week. This program then condenses that query into the absolute bare minimum for James O'Hara. It leaves a list of SKU's and the dates on which they experienced a stockout. 
- new_stockouts_analysis.ipynb: This is empty. 
- stockout_analysis.ipynb: This is where I did my exploration of the stockout data. In this file, I filtered out the stockouts by activity status (first by if they're discontinued or not, then by usage). I then performed some post-processing on the data. This allowed me to develop a systematic way of processing and filtering the stockout query. 

In min_max_copy_code/Code/:
- new_stockout_analysis.ipynb: This is the final iteration of the stockout analysis. Here, I experiment with different years_ago parameters to determine how far back we have to look at usage. At first, I was only experimenting with stockouts from the year to date. I also experimented with excluding the consumables from stockouts (group 00). I found out that group 00 makes up a fairly sizable portion of total stockouts (~1/3 to be exact). I also found that stockouts are confined to a select group of items – only 160 unique SKUs not counting consumables, 245 with consumables. In this notebook, I also investigate stockout counts by item to see if high stockout rates are caused by insufficient min/maxes. 
- 6_8_stockouts_for_jeff.ipynb: Based on new_stockout_analysis.ipynb. Here, I was experimenting with a stockout metric of stockouts per successful transfer from CS004 to the bases. This was ultimately not very informative - our stockout rates haven't changed much in the last 5 years that we've been tracking stockouts. 
- stockouts_with_qoh.ipynb: This was an attempt to merge my january QOH work with stockouts. Ultimately, we still don't have starting quantities of items, so this wasn't successful. 
- real_zeros_analysis.ipynb: For this project, I was exploring cases where the Central Min/Max/ROQ was all 0, but the base min/max/ROQ was not 0. I also explored the base mins and how high they are relative to central. 

# Tableau Translit Project

Only what is in "Trello API Analysis" is actually workable. The other files are stubs.

trello_to_csv.py contains a finalized version of the trello->csv code. The notebooks (Trello To CSV.ipynb and Trello To CSV New.ipynb) were just used for development. 

Rays Trello Board.json is the raw data, and the two csv files in this directory are simply outputs of the trello to csv script. 

# Query Work

If someone asks you to make a new query, there are two files you must create. The first is the shell script, which performs the "grunt work" of creating the proper output directories and running the python script. 

query_shell_script_template.sh is the template you should use for new query shell scripts. 

The other file is the python file. This is pretty straightforward – it is simply a call to ducktape with the correct query name. 

query_python_script_template.py is the template you should use for this. 

# Ducktape Rewrite (aborted due to selenium bug)
