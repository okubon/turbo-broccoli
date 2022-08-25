import xml.etree.ElementTree as ET
import pandas as pd
import re
import os
import time
import glob
import logging
from typing import Union

# alternative to spamming your terminal, used to check on performance and errors
logging.basicConfig(
    format='%(asctime)s: %(message)s', 
    datefmt='%d/%m/%Y %I:%M:%S', 
    filename='script/filetime.log', 
    filemode="w", 
    encoding='utf-8', 
    level=logging.INFO
)

def merge_all_csv() -> None:
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

def type_of_speech(sentence: str) -> tuple[str, str]:
    '''
    Checks if the part contains a RB or KO.
    '''
    # RegEx for the different formats of RB
    rb_regex = {
        'base': "([a-zA-ZÄäÜüÖöß]+\s\([^)]*\)\s\([^)]*\).*?(?=:)|[a-zA-ZÄäÜüÖöß]+\s\([^)]*\).*?(?=:))",
        'title': "^(Alterspräsidenti?n?|Präsidenti?n?|Vizepräsidenti?n?|Abg.|Frau|Dr?.)\s[a-zA-ZÄäÜüÖöß]+.*?(?=:)"
    }

    # RegEx for the different formats of KO
    # for whatever reason the positive lookbehind for '(' doesn't work
    ko_regex = {
        "base": "\([a-zA-Z]+.*\[.*\](?=:)"
    }
    
    if re.match(rb_regex["base"], sentence):
        match = re.match(rb_regex["base"], sentence)
        dtype = 'rb'    
    elif re.match(rb_regex["title"], sentence):
        match = re.match(rb_regex["title"], sentence)
        dtype = 'rb' 
    elif re.match(ko_regex["base"], sentence):
        match = re.match(ko_regex["base"], sentence)
        dtype = 'ko'
    else:
        match = ["Null"]
        dtype = "Null"
    
    return dtype, match[0]

def extract_from_protocol(file, rb_ID:int) -> tuple[pd.DataFrame, pd.DataFrame, int, int]:
    '''
    Cuts a singular given protocol into parts and extracts the RB and KO.
    Saves those extractions into dictionaries and creates a df out of those.
    '''
    # empty dicts to store the results
    rb_dict = {}
    ko_dict = {}

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

    # create ko df
    ko_df = pd.DataFrame.from_dict(ko_dict, orient = 'index').reset_index()
    ko_df = ko_df.rename(columns={'index':'RB_ID', 0:'KO_Name'})

    return rb_df, ko_df, rb_ID, wahlperiode

def main() -> None:
    '''
    Walks through the entire process of extracting, assigning, 
    cleaning and saving the data.
    '''
    rb_ID = 0
    dir = 'protokolle_wp_1-12/'

    filenumber, total_time, wp = 0, 0, 0

    # empty dfs to store results for RB and KO
    RB_df = pd.DataFrame(columns=["RB_ID","RB_Name","WAHLPERIODE","NR","DATUM"])
    KO_df = pd.DataFrame(columns=["RB_ID","KO_Name"])

    # iterate through folders and files
    for root, dirs, files in os.walk(dir):  

        if (RB_df.shape[0] != 0) and (KO_df.shape[0] != 0):
            
            # some comments get catched because they stretch over multiple lines
            # cut off from the previous part by a newline, they get filtered here
            RB_df = RB_df[~RB_df["RB_Name"].str.contains('\[')]

            # the positive look behind didn't work
            KO_df["KO_Name"] = KO_df["KO_Name"].str[1:]

            # export to csv
            RB_df.to_csv(rf'output/rb/rb{wp}.csv',encoding='utf-8-sig', index = False)
            KO_df.to_csv(rf'output/ko/ko{wp}.csv',encoding='utf-8-sig', index = False) 
                        
            logging.info(f' WP{wp} - {filenumber} files - {RB_df.shape[0]} RB - {KO_df.shape[0]} KO - {round(total_time,2)} sec.')
            filenumber, total_time = 0, 0    
            
            # empty out dfs for next loop
            RB_df = RB_df.iloc[0:0]
            KO_df = KO_df.iloc[0:0]

        for name in files:

            filenumber += 1
            t0 = time.time()

            filename =  os.path.join(root, name)
            file = ET.parse(filename).getroot()

            part_rb_df, part_ko_df, rb_ID, wp = extract_from_protocol(file, rb_ID)
            
            RB_df = pd.concat([RB_df, part_rb_df])
            KO_df = pd.concat([KO_df, part_ko_df])

            t1 = time.time()
            total_time += t1 - t0 


main()
# commented out because the merged file tends to kill (me and) the data 
# transformation process inside PowerQuery
# merge_all_csv()