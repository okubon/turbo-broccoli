import xml.etree.ElementTree as ET
import pandas as pd
import os
import time
import glob
import logging

from extraction import *
from transformation import *

# alternative to spamming your terminal, used to check on performance and errors
logging.basicConfig(
    format="%(asctime)s: %(message)s", 
    datefmt="%d/%m/%Y %I:%M:%S", 
    filename="scripts/_filetime.log", 
    filemode="w", 
    encoding="utf-8", 
    level=logging.INFO
)

def main() -> None:
    """
    Walks through the entire process of extracting, assigning, 
    cleaning and saving the data.
    """
    rb_ID = 0
    dir = "protokolle_wp_1-12/"

    filenumber, total_time, wp = 0, 0, 0

    # get all possible city additions
    ortszusatz = get_ortszusatz()

    # empty dfs to store results for RB and KO
    RB_df = pd.DataFrame(columns=["RB_ID","RB_Name","WAHLPERIODE","NR","DATUM"])
    KO_df = pd.DataFrame(columns=["RB_ID","KO_Name"])

    # iterate through folders and files
    for root, dirs, files in os.walk(dir):  

        if (RB_df.shape[0] != 0) and (KO_df.shape[0] != 0):
            
            # final cleaning and extracting before saving
            RB_df, KO_df = clean_dfs(RB_df, KO_df, ortszusatz)

            KO_df = KO_df.sort_values(by=["RB_ID"])

            # export to csv
            RB_df.to_csv(rf"output/rb/rb{wp}.csv",encoding="utf-8-sig", index = False)
            KO_df.to_csv(rf"output/ko/ko{wp}.csv",encoding="utf-8-sig", index = False) 
                        
            logging.info(f" WP{wp} - {filenumber} files - {RB_df.shape[0]} RB - {KO_df.shape[0]} KO - {round(total_time,2)} sec.")
            filenumber, total_time = 0, 0    
            
            # empty out dfs for next loop
            RB_df = RB_df.iloc[0:0]
            KO_df = KO_df.iloc[0:0]

        for name in files:

            filenumber += 1
            t0 = time.time()

            filename =  os.path.join(root, name)
            file = ET.parse(filename).getroot()

            # extracts RB and KO from the protocols
            part_rb_df, part_ko_df, rb_ID, wp = extract_from_protocol(file, rb_ID)
            
            # appends them to the priorly empty dfs
            RB_df = pd.concat([RB_df, part_rb_df])
            KO_df = pd.concat([KO_df, part_ko_df])

            t1 = time.time()
            total_time += t1 - t0 

def merge_all_csv() -> None:
    """
    For performance reasons every period has its seperate csv. 
    This function merges all of them. Note: the output csv might be
    too big for some pcs or tools to handle.
    """
    rb_path = "output/rb/"
    rb_all_files = glob.glob(os.path.join(rb_path, "*.csv"))
    rb_df_from_each_file = (pd.read_csv(f, sep=",") for f in rb_all_files)
    rb_df_merged = pd.concat(rb_df_from_each_file, ignore_index=True)
    rb_df_merged.to_csv("output/rb_merged.csv")

    ko_path = "output/ko/"
    ko_all_files = glob.glob(os.path.join(ko_path, "*.csv"))
    ko_df_from_each_file = (pd.read_csv(f, sep=",") for f in ko_all_files)
    ko_df_merged = pd.concat(ko_df_from_each_file, ignore_index=True)
    ko_df_merged.to_csv("output/ko_merged.csv")

main()
# commented out because the merged file tends to kill (me and) the data 
# transformation process inside PowerQuery and Excel
# merge_all_csv()