# Key Assumptions 
By Peter Benson.
email: peterb2470@gmail.com

**Min/Max Analysis**
- The majority of our inventory is stored at central store (CS004). 
- When a base reaches its min quanity of a SKU, it requests more (equal to it's reorder quantity, or ROQ) from CS004.
- When CS004 reaches its min quantity, it generates a Requsition, which is turned into a Purchase Order (PO). The buyers then act on these purchase orders and contact the vendors for the appropriate quantity. 

The formula for the min and Reorder Quantity is as follows: 

Let $m$ be average monthly usage and $l$ be padded leadtime. 

Min = $m * l$; ROQ = $6 * m$. 

- Reorder Quantity is 6 months of reordering because that lines up with our rough ideal buying frequency. 
  - Ideally, we would optimize this by balancing storage cost and buyer cost. If we buy too often, the buyers always have to be buying, which increases buyer cost. If we don't buy enough, then we have to store huge amounts of parts in the warehouse, which drives up storage costs. 
- We chose 1 month as a leadtime padding to be extra safe, and to give time for the buyers to fulfill purchase requests. 
Leadtime is only calculated from the date of the purchase order to the arrival date, so it fails to account for buying time. 
- To calculate leadtime, we took the average of the 5 most recent leadtimes. This is to get a realistic picture of the current trends in the supply-chain environment. 
- To calculate monthly usage, we took the average monthly usage over the last 2 years. Again, this is to get a realistic and recent picture of our current part usage.
- To get usage, we used the '030' transaction code (not 031, as 031 would result in double-counting).  

The parts we did the most analysis on for this project were carefully chosen from a subset of all of our active parts. 
First, the parts had to have at least 5 usages in the last 2 years. (Not one usage with a quantity of 5, 5 distinct usage instances). 
This was to get the subset of parts that were truly "active" and had enough transactions that we could actually analyze them. 
Next, the parts had to cost less than $500. This was a limitation imposed by Frank and Takary in order to limit the scope of analysis to low-impact parts.
Finally, there were a number of item groups we exluded from the analysis.
Specifically: '93', '94', '58', '71', '51', '70', '73', '75', '72', '77', '74', '76', '78', '52', '53', '54', '55', '57', '64', '79'. 
93 and 94 are obsolete item groups that hadn't been captured in earlier analysis, while the other groups are rail parts. 
Takary and Frank wanted to concentrate on high-turn bus parts rather than the slower-moving rail parts. 

**Stockouts**
To filter out "real" stockouts from the full stockout query (WH_STOCKOUTS), there are several filter conditions. 

1. Is an active part (doesn't have the Discontinue flag)
2. Is a replenished part (Doesn't have the No Repl flag)
3. Has Min/Max/ROQ (min/max/roq are all greater than 0)
4. Has been used recently (In the last 5 years)
5. (Optional) Is not a consumable part (filter out item group 00). This can be used to filter down to "critical" parts, which Jeff wants to target. 

The last 5 years filter was decided because it was practically identical to a 10-year filter. We have only used ~13,000 unique SKUs in the last 5 years. 
In addition, 2 years excluded a few parts (~200 SKUs), so 5 years was used. 
