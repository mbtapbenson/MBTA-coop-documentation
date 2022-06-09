# Trello to CSV
# Takes a JSON file (downloaded from a Trello Board) and converts it to a pandas dataframe
# This is a transliteration from a Tableau Prep Flow
# For questions, email pbenson@mbta.com or staing@mbta.com

import pandas as pd
import json
import os
import numpy as np
import pickle
import datetime
import copy

#trello_json_path_local = '/Volumes/commons/PP-PROLOG/VENDOR_MANAGEMENT/Data_Analytics/Data_Files/Procurement_Data/Sourcing_Pipeline/Rays Trello Board.json'
trello_json_path = '/O_drive_mnt_pt/VENDOR_MANAGEMENT/Data_Analytics/Data_Files/Procurement_Data/Sourcing_Pipeline/Rays Trello Board.json'

with open(trello_json_path, 'r') as f:
    trello_json = json.load(f)

members = trello_json['members']
lists = trello_json['lists']

members_dict = {}
lists_dict = {}

# rename keys so that it is easier to access
for i in range(len(members)):
    members_dict[members[i]['id']] = members[i] 

for i in range(len(lists)):
    lists_dict[lists[i]['id']] = lists[i]

def get_card_labels(card):
    # Card object 
    label_list = []
    
    labels = card['labels']
    
    for label in labels:
        label_list.append(label['name'])
    
    return label_list

def get_list_by_id(listID):
    return lists_dict[listID]['name']
    
def get_members_by_ids(member_ids):
    member_list = []
    
    correct_members_dict = {
        '5932cdf4d9946250ed83d611': 'Nick Easley',
        '593814b1ffff50d61a6ffefe': 'Tracey Dionne',
        '5938514c586d6db6eb1192a0': 'Joe Flynn',
        '5b0d7bd52cfb836ed06e2ce9': 'Ray Wise',
        '5b44af42f3ef6c258e7e8351': 'Eric Welsh',
        '5b7c3f05d0cca32135661211': 'Rob Weiner',
        '5bc74b04a9932625bd29bde7': 'John DeLalla',
        '5c1153ead418da18936b8c54': 'Jimmy Moynihan',
        '5c11839181a2ee0bf9cf4608': 'Kiana Hall',
        '5dadb5d0e3f9797ccc768e91': 'Iya Kazekevich',
        '5dcd7c49dab6682f4d3b9684': 'Arlyn Zuniga',
        '5fb55f187751218a60a048d7': 'Michael Pillemer'
    }
    
    if len(member_ids) == 0:
        member_list.append('Unassigned')
    elif len(member_ids) == 1:
        member_list.append(correct_members_dict[member_ids[0]])
    else:
        for member_id in member_ids:
            member_list.append(correct_members_dict[member_id])

    return member_list

def format_activity(activity_date):
    # Get Datetime object
    # 2022-01-31T16:32:29.984Z
    # Desired format:
    # DD-[Month name]-YY
    activity_date = activity_date[:len(activity_date) - 5]
    activity_datetime = datetime.datetime.strptime(activity_date, '%Y-%m-%dT%H:%M:%S')
    
    return activity_datetime.strftime('%-m/%-d/%Y')

def format_due_date(due_date):
    # Get Datetime object
    # 2022-01-31T16:32:29.984Z
    # Desired format:
    # DD-[Month name]-YY
    due_date = due_date[:len(due_date) - 5]
    due_datetime = datetime.datetime.strptime(due_date, '%Y-%m-%dT%H:%M:%S')
    
    return due_datetime.strftime('%-m/%-d/%Y')
    
def format_archival(archived_status):
    if archived_status:
        return 'Yes'
    else:
        return 'No'
    
def format_closed(closed_status):
    if closed_status:
        return 'Closed'
    else:
        return 'Open'

def get_status_by_list(list_id):
    procurement_status_dict = {
        '5935fd2a32d6de7c51454b64' :  'Pipeline',
        '5bc9db91fb62c1685a51d7ef' :  'Pipeline',
        '5935fd3423c4cedaedf011ab' :  'Solicitation',
        '593d3e265758fdb44be5a8fb' :  'Solicitation',
        '5935fd3b01374ff1af03c73c' :  'Solicitation',
        '5935fd418c23c980874a7998' :  'Solicitation',
        '5b3b83aa1bbe3f205aba9997' :  'Solicitation',
        '5935fd4566bf9d5a68e1f8d3' :  'Contract',
        '5935fd4d15f59251a1a678b0' :  'Contract',
        '5937dbb9fbf481f047aa4198' :  'Contract',
        '5937db640d1123a81cf03bd3' :  'Closed',
        '5cac95843ce3f744def010b2' :  'Closed',
        '593a94f408ed531f8b4019ba' :  'On Hold',
        '593a94f605f7adbfabad8162' :  'On Hold',
        '59807ef4e05533b498c69f10' :  'On Hold',
        '5d7a5481c818437c522ed6c9' :  'On Hold'}
    
    # Translate list ID to procurement status
    
    return procurement_status_dict[list_id]

def get_stage_by_list(list_id):
    procuremnent_stage_dict = {
        '5935fd2a32d6de7c51454b64' : 'PIPELINE',
        '5935fd3423c4cedaedf011ab' : '1. PREPARE RFP',
        '5935fd3b01374ff1af03c73c' : '2. SOURCING ACTIVITIES',
        '5935fd418c23c980874a7998' : '3. EVALUATE RESPONSE',
        '5935fd4566bf9d5a68e1f8d3' : '4. FINALIZE CONTRACT',
        '5935fd4d15f59251a1a678b0' : 'MAINTAIN CONTRACT (Archived)',
        '5937db640d1123a81cf03bd3' : 'COMPLETE FOR THE WEEK',
        '5937dbb9fbf481f047aa4198' : 'MAINTAIN CONTRACT',
        '593a94f408ed531f8b4019ba' : 'FOR CPO REVIEW',
        '593a94f605f7adbfabad8162' : '** LEGAL ISSUE **',
        '593d3e265758fdb44be5a8fb' : '1. PREPARE RFP (Archived)',
        '59807ef4e05533b498c69f10' : '** INSURANCE DELAY **',
        '5b3b83aa1bbe3f205aba9997' : 'LIVE VEHICLE PROCUREMENTS',
        '5bc9db91fb62c1685a51d7ef' : 'PIPELINE (Archived)',
        '5cac95843ce3f744def010b2' : 'CANCELLED INITIATIVES',
        '5d7a5481c818437c522ed6c9' : 'SPECIFICATION HOLD',
        '5f0489b9c31675327f2c7558' : 'VEH PROC IN WARRANTY'
    }
    
    return procuremnent_stage_dict[list_id]


### ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
### FUNCTIONS DONE, RUN THE FLOW
### ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––

card_list = []
id_set = set()

for card in trello_json['cards']:
    id_set.add(card['id'])
    
    labels = get_card_labels(card)
    
    procurement_step = get_stage_by_list(card['idList'])
    members = get_members_by_ids(card['idMembers'])
    
    last_updated = format_activity(card['dateLastActivity'])
    archived = format_archival(card['closed'])
    closed = format_closed(card['closed'])
    
    if card['due'] is not None:
        due_date = format_due_date(card['due'])
    else:
        due_date = np.nan
    
    status = get_status_by_list(card['idList'])
    
    if len(labels) == 0:
        labels = ['']
        
    for label in labels:
        if len(members) > 1:
            for member in members:
                card_dict = {'Procurement Stage': procurement_step, 
                    'Project Title': card['name'],
                    'Label Name': label,
                    'Due Date': due_date, 
                    'Last Updated': last_updated, 
                    'Project ID': card['id'], 
                    'Assigned To': member,
                    'Closed Project': closed, 
                    'Procurement Status': status, 
                    'Url (Cards)': card['url'], 
                    'Archived': archived}

                card_list.append(card_dict)

        else:
            card_dict = {'Procurement Stage': procurement_step, 
                        'Project Title': card['name'],
                        'Label Name': label,
                        'Due Date': due_date, 
                        'Last Updated': last_updated, 
                        'Project ID': card['id'], 
                        'Assigned To': members[0],
                        'Closed Project': closed, 
                        'Procurement Status': status, 
                        'Url (Cards)': card['url'], 
                        'Archived': archived}

            card_list.append(card_dict)

full_trello_df = pd.DataFrame(card_list)

project_id_dict = {}

for project_id in list(full_trello_df['Project ID'].unique()):
    filtered_df = full_trello_df.loc[full_trello_df['Project ID'] == project_id]
    
    project_id_dict[project_id] = list(filtered_df['Label Name'])

### Label Processing

label_transformation_dict = {
    'SAFETY': 'Safety',
    'INCLUDES DEI EVALUATION': 'Includes DEI Evaluation',
    'high effort': 'High Effort',
    'medium effort': 'Medium Effort',
    'low effort': 'Low Effort',
    'federal funding': 'Federal Funding',
    'no requisition yet': 'No Requistion Yet',
    'operations funded': 'Operations Funded',
    'capital funded': 'Capital Funded',
    'Review by SDT - Potential Candidate': 'Reviewed by SDT - Potential Candidate'
}

fund_source_labels = ['Operations Funded', 'Capital Funded', 'Federal Funding']
effort_level_labels = ['High Effort', 'Medium Effort', 'Low Effort']
sdt_review_labels = ['Reviewed by SDT - Potential Candidate', 
                     'Reviewed by SDT - Not a Candidate']
spend_thresh_labels = ['>$250k Spend', '<$250k']

def construct_label_df(project_id_dict):
    # For each label, make a new row (dictionary)
    # row should contain project ID, and all label names 
    
    default_label_dict = {'TRLO - Fund Source': np.nan,
                         'TRLO - Level of Effort': np.nan,
                         'TRLO - Proj In FMIS': np.nan,
                         'TRLO - Safety Related': np.nan,
                         'TRLO - DEI Related': np.nan,
                         'TRLO - SDT Review': np.nan,
                         'TRLO - Spend Threshold': np.nan}
    
    label_row_list = []
    
    for project_id in project_id_dict:
        project_labels = project_id_dict[project_id]
        
        label_dict = copy.deepcopy(default_label_dict)
        label_dict['TRLO - Project ID'] = project_id
        
        for label in project_labels:
            if label in label_transformation_dict:
                formatted_label = label_transformation_dict[label]
            else:
                formatted_label = label
            #print(formatted_label)

            # if label is in each thing, then add it to its respective column
            if formatted_label in fund_source_labels:
                label_dict['TRLO - Fund Source'] = formatted_label

            elif formatted_label in effort_level_labels:
                label_dict['TRLO - Level of Effort'] = formatted_label

            elif formatted_label in sdt_review_labels:
                label_dict['TRLO - SDT Review'] = formatted_label

            elif formatted_label in spend_thresh_labels:
                #print(formatted_label)
                label_dict['TRLO - Spend Threshold'] = formatted_label

            elif formatted_label == 'Safety':
                #print('Safety')
                label_dict['TRLO - Safety Related'] = formatted_label
            elif formatted_label == 'Includes DEI Evaluation':
                #print('DEI Eval')
                label_dict['TRLO - DEI Related'] = formatted_label
            elif formatted_label == 'No Requistion Yet':
                #print('No Req')
                label_dict['TRLO - Proj In FMIS'] = formatted_label
        
        label_row_list.append(label_dict)
        
    return pd.DataFrame(label_row_list)

label_df = construct_label_df(project_id_dict)

trello_no_labels = full_trello_df.drop('Label Name', axis=1).astype('str').drop_duplicates().reset_index()

trello_no_labels.rename(columns={'Project ID': 'TRLO - Project ID'}, inplace=True)

trello_with_labels = trello_no_labels.merge(label_df, on='TRLO - Project ID', how='left')
trello_with_labels.drop('index', axis=1, inplace=True)

# Rename Columns
trello_rename_key = {
    'Assigned To': 'TRLO - Assigned To',
    'Archived': 'TRLO - Archived',
    'Closed Project': 'TRLO - Closed Project',
    'Due Date': 'TRLO - Due Date',
    'Last Updated (Cards)': 'TRLO - Last Updated (Cards)',
    'Procurement Stage': 'TRLO - Procurement Stage',
    'Procurement Status': 'TRLO - Procurement Status',
    'Project ID': 'TRLO - Project ID',
    'Project Title': 'TRLO - Project Title',
    'Url (Cards)': 'TRLO - Url Cards',
}

trello_with_labels.rename(columns = trello_rename_key, inplace=True)

# Buyer calculations

buyer_dict = {
    'Arlyn Zuniga': 'AZUNIGA',
    'Jimmy Moynihan': 'JMOYNIHAN',
    'John DeLalla': 'JDELALLA',
    'Joe Flynn': 'AFLYNN',
    'Kiana Hall': 'KHALL',
    'Ray Wise': 'RWISE',
    'Rob Weiner': 'RWEINER',
    'Tracey Dionne': 'TDIONNE',
    'Eric Welsh': 'EWELSH',
    'Nicholas Easley': 'NEASLEY',
    'Nick Easley': 'NEASLEY',
    'Unassigned': 'UNASSIGNED',
    'Michael Pillemer': 'MPILLEMER'
}

trello_with_labels['TRLO - Buyer'] = 'no buyer'

for buyer in buyer_dict:
    trello_with_labels.loc[trello_with_labels['TRLO - Assigned To'] == buyer, 'TRLO - Buyer'] = buyer_dict[buyer]

trello_with_labels['TRLO - Project Create Date'] = trello_with_labels.apply(lambda x: datetime.datetime.fromtimestamp(int(x['TRLO - Project ID'][0:8],16)).strftime('%-m/%-d/%Y'), axis=1)


trello_with_labels.rename(columns = {'TRLO - Url Cards': 'TRLO - Url (Cards)',
                                    'Last Updated': 'TRLO - Last Updated (Cards)',
                                    'TRLO - Proj in FMIS': 'TRLO - Proj In FMIS'}, inplace=True)

trello_with_labels_right_order = trello_with_labels[['TRLO - Project Create Date', 'TRLO - Buyer', 'TRLO - Project ID',
       'TRLO - Project Title', 'TRLO - Assigned To',
       'TRLO - Procurement Stage', 'TRLO - Procurement Status',
       'TRLO - Closed Project', 'TRLO - Url (Cards)',
       'TRLO - Last Updated (Cards)', 'TRLO - Due Date', 'TRLO - Fund Source',
       'TRLO - Level of Effort', 'TRLO - Proj In FMIS',
       'TRLO - Safety Related', 'TRLO - DEI Related', 'TRLO - SDT Review',
       'TRLO - Spend Threshold']]

# Make sure 'nan' is actually np.nan
trello_with_labels_right_order.loc[trello_with_labels_right_order['TRLO - Due Date'] == 'nan', 'TRLO - Due Date'] = np.nan

right_dates = pd.to_datetime(trello_with_labels_right_order['TRLO - Project Create Date'])# + datetime.timedelta(days = 2)
trello_with_labels_right_order['TRLO - Project Create Date'] = right_dates.dt.strftime('%-m/%-d/%Y')

# The difference between the test data and this calculated data is:
# - Calculated data create date is 2-3 days before the test data
# - Calculated data has no duplicate levels for label categories (eg. no cards with multiple levels of effort)

# Filter out to just No Requisition yet and not closed
trello_filtered = trello_with_labels_right_order.loc[(trello_with_labels_right_order['TRLO - Proj in FMIS'] == 'No Requisition Yet') & (trello_with_labels_right_order['TRLO - Closed Proj'] != 'Closed')]

# output: staging folder
output_path = 'O_drive_mnt_pt/VENDOR_MANAGEMENT/Data_Analytics/Data_Files/Staging_Area_for_Testing/tableau_translit'
trello_with_labels_right_order.to_csv(output_path, index=False)