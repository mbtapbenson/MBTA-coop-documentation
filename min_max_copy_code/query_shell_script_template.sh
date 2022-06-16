#!/bin/bash

# query script template.sh
# Created by Peter Benson , template as of June 2022

#echo -e "Routing to [ \e[1m$1\e[0m ] DB(s). Routing to [ \e[1m$2\e[0m ] machine(s)."
d=$(date +%m%d%Y-%H%M%S)

# Per-script variable definition
setname="pl_po_encumb_line_level"
querybasename="PL_PO_ENCUMB_LINE_LEVEL"

# Go to the right place and create the correct directory
cd $RUBIXTAPEDATAPATH
mkdir -p $RUBIXTAPEDATAPATH/$setname/$d

# Run the actual query
python3 $RUBIXTAPEBASEPATH/selenium-$setname.py $d

# Rename to include the date
mv $RUBIXTAPEDATAPATH/$setname/$d/$querybasename\_*.xlsx $RUBIXTAPEDATAPATH/$setname/$d/$querybasename-$d.xlsx

# Store to O drive using rm_head.py
echo "Storing to O drive..."
python3 $RUBIXTAPEBASEPATH/'rm_head'.py $RUBIXTAPEDATAPATH/$setname/$d/$querybasename-$d.xlsx $RUBIXTAPEDATAFILEPATH/$querybasename.xlsx 