import xml.etree.ElementTree as ET
import pandas as pd
import os
import time
import glob
import logging

from extraction import *
from transformation import *

# alternative to spamming your terminal, used to check 
# on performance and errors
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

main()
