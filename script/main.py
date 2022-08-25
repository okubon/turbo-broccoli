import xml.etree.ElementTree as ET
import pandas as pd
import re
import os
import time
import glob
import logging

# alternative to spamming your terminal, used to check on performance and errors
logging.basicConfig(
    format='%(asctime)s: %(message)s', 
    datefmt='%I:%M:%S', 
    filename='filetime.log', 
    filemode="w", 
    encoding='utf-8', 
    level=logging.INFO
)

def type_of_speech(str):
    '''
    Checks if the part contains a RB or KO.
    '''
    # RegEx for the different formats of RB
    rb_regex = {
        'base': "([a-zA-ZÄäÜüÖöß]+\s\([^)]*\)\s\([^)]*\):|[a-zA-ZÄäÜüÖöß]+\s\([^)]*\).*?:)",
        'title': "Dr\..*[a-zA-ZÄäÜüÖöß]+.*:"
    }

    # RegEx for the different formats of KO
    ko_regex = {
        "base": "[a-zA-Z]+.*\[.*\]:"
    }
    
    if re.match(rb_regex["base"], str):
        match = re.match(rb_regex["base"], str)
        type = 'rb'    
    elif re.match(rb_regex["title"], str):
        match = re.match(rb_regex["title"], str)
        type = 'rb'    
    elif re.match(ko_regex["base"], str):
        match = re.match(ko_regex["base"], str)
        type = 'ko'
    else:
        match = ["Null"]
        type = "Null"

    return type, match[0]

def clean_rb_df(df):
    '''
    The RegEx match some other patterns that this function gets rid of.
    '''
    # key words in rb to skip
    discard = [
        "Drucksache",  
        "Geschäftsordnung", 
        "Tagesordnungspunkt",
        "Verordnung",
        "Ausschuss","ausschusses","schusses","ses \(",
        "gie \(",
        "Schriftlicher",
        "§",
        "Ratsdok",
        "Ergänzung",
        "btr.",
        "Fortsetzung",
        "Fragen",
        "Haushaltsführung",
        "folgenabschätzung", "abschätzung"
    ]

    # check if sentence is needed
    for item in discard:
        df = df[~df.RB_Name.str.contains('|'.join(discard))]
    return df

def clean_rb_item(input):
    '''
    The RegEx sometimes match a bit too much. This cuts off some of the excess.
    '''
    step1 = input.split(':')
    step2 = step1[0].split(',')
    step3 = step2[0].split(' . ')
    step4 = re.split(r'\d', step3[0], maxsplit=1)
    output = step4[0].strip()
    return output

def clean_ko_item(input):
    '''
    The RegEx sometimes match a bit too much. 
    This cuts off some of the excess and other additional parts.
    '''
    # Cleans the item in a list from colons.
    l = len(input)
    input = input[:l-1]

    # Splits after '— '
    if '— ' in input:
        input = input.split(sep='— ', maxsplit=1)[1]
    if input[0] == '—':
        input = input[1:]
    if ':' in input:
        input = input.split(sep=':', maxsplit=1)[1]
    if 'Abg.' in input:
        input = input.split(sep='Abg.', maxsplit=1)[1]
    
    return input

def extract_from_protocol(file, rb_ID, rb_dict, ko_dict):
    '''
    Cuts a singular given protocol into parts and extracts the RB and KO.
    Saves those extractions into dictionaries and creates a df out of those.
    '''
    # get meta data and content from xml file
    wahlperiode = file[0].text
    nr = file[2].text
    datum = file[3].text
    protocol = file[5].text

    # split the text in single sentences
    text = protocol.split("\n")

    # iteration through sentences
    for sentence in text:
        type, match = type_of_speech(sentence)
        # match = clean_rb_item(check[1])

        if type == 'rb':
            rb_ID += 1
            rb_dict[str(rb_ID)] = match
        elif type == 'ko':
            ko_dict[str(rb_ID)] = match
    
    # create rb df
    rb_df = pd.DataFrame.from_dict(rb_dict, orient = 'index').reset_index()
    rb_df = rb_df.rename(columns={'index':'RB_ID', 0:'RB_Name'})

    # add the rest of imformation to df
    rb_df['WAHLPERIODE'] = wahlperiode
    rb_df['NR'] = nr
    rb_df['DATUM'] = datum
    #rb_df = clean_rb_df(rb_df) #TODO 

    # create ko df
    ko_df = pd.DataFrame.from_dict(ko_dict, orient = 'index').reset_index()
    ko_df = ko_df.rename(columns={'index':'RB_ID', 0:'KO_Name'})

    return rb_df, ko_df, rb_ID, wahlperiode

def main(dir, rb_ID):
    '''
    Walks through the entire process of extracting, assigning, 
    cleaning and saving the data.
    '''
    # empty dfs to store results for RB and KO
    RB_df = pd.DataFrame()
    KO_df = pd.DataFrame()

    # empty dicts to store the results
    rb_dict = {}
    ko_dict = {}

    dir = 'protokolle_wp_1-12/'

    filenumber, total_time, wp = 0, 0, 0

    # iterate through folders and files
    for root, dirs, files in os.walk(dir):  

        logging.info(f' WP{wp} - {filenumber} files - {round(total_time,2)} sec.')
        filenumber, total_time, wp = 0, 0, 0

        for name in files:

            filenumber += 1
            t0 = time.time()

            filename =  os.path.join(root, name)
            file = ET.parse(filename).getroot()

            part_rb_df, part_ko_df, rb_ID, wp = extract_from_protocol(file, rb_ID, rb_dict, ko_dict)
            
            #Clean_rb_df = clean_rb_df() #TODO 

            RB_df = pd.concat([RB_df,part_rb_df])
            KO_df = pd.concat([KO_df,part_ko_df])

            # adjust RB_id per period
            RB_df['RB_ID'] = "WP" + str(wp) + "_RB" + RB_df['RB_ID'].astype(str)
            KO_df['RB_ID'] = "WP" + str(wp) + "_RB" + KO_df['RB_ID'].astype(str)

            # export to csv
            RB_df.to_csv(rf'output/rb/{wp}.csv',encoding='utf-8-sig', index = False)
            KO_df.to_csv(rf'output/ko/{wp}.csv',encoding='utf-8-sig', index = False)
            
            # empty out dfs for next loop
            RB_df = RB_df.iloc[0:0]
            KO_df = KO_df.iloc[0:0]

            t1 = time.time()
            total_time += t1 - t0 

def merge_all_csv():
    '''
    For performance reasons every period has its seperate csv. 
    This function merges all of them. Note: the output csv might be
    to big for some pcs or tools to handle.
    '''
    rb_path = "output/rb/"
    rb_all_files = glob.glob(os.path.join(rb_path, "*.csv"))
    rb_df_from_each_file = (pd.read_csv(f, sep=',') for f in rb_all_files)
    rb_df_merged = pd.concat(rb_df_from_each_file, ignore_index=True)
    rb_df_merged.to_csv("output/rb_merged.csv")

    ko_path = "output/ko/"
    ko_all_files = glob.glob(os.path.join(ko_path, "*.csv"))
    ko_df_from_each_file = (pd.read_csv(f, sep=',') for f in ko_all_files)
    ko_df_merged = pd.concat(ko_df_from_each_file, ignore_index=True)
    ko_df_merged.to_csv("output/ko_merged.csv")

main(dir, 0)
# commented out because the merged file tends to kill (me and) the data 
# transformation process inside PowerQuery
# merge_all_csv()