import pandas as pd
import re

def type_of_speech(sentence: str) -> tuple[str, str]:
    """
    Checks if the part contains a RB or KO.
    """
    # RegEx for the different formats of RB
    rb_regex = {
        "base": "([a-zA-ZÄäÜüÖöß]+\s\([^)]*\)\s\([^)]*\).*?(?=:)|[a-zA-ZÄäÜüÖöß]+\s\([^)]*\).*?(?=:))",
        "title": "^(Alterspräsidenti?n?|Präsidenti?n?|Vizepräsidenti?n?|Abg\.|Frau|D\. Dr\.|Dr\.?)\s[a-zA-ZÄäÜüÖöß]+.*?(?=:)"
    }

    # RegEx for the different formats of KO
    # for whatever reason the positive lookbehind for "(" doesn't work
    ko_regex = {
        "base": "\([a-zA-Z]+.*\[.*\](?=:)"
    }
    
    if re.match(rb_regex["base"], sentence):
        match = re.match(rb_regex["base"], sentence)
        dtype = "rb"    
    elif re.match(rb_regex["title"], sentence):
        match = re.match(rb_regex["title"], sentence)
        dtype = "rb" 
    elif re.match(ko_regex["base"], sentence):
        match = re.match(ko_regex["base"], sentence)
        dtype = "ko"
    else:
        match = ["Null"]
        dtype = "Null"
    
    return dtype, match[0]

def extract_from_protocol(file, rb_ID:int) -> tuple[pd.DataFrame, pd.DataFrame, int, int]:
    """
    Cuts a singular given protocol into parts and extracts the RB and KO.
    Saves those extractions into dictionaries and creates a df out of those.
    """
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

        if type == "rb":
            rb_ID += 1
            rb_dict[str(rb_ID)] = match
        elif type == "ko":
            ko_dict[str(rb_ID)] = match
    
    # create rb df
    rb_df = pd.DataFrame.from_dict(rb_dict, orient = "index").reset_index()
    rb_df = rb_df.rename(columns={"index":"RB_ID", 0:"RB_Name"})

    # add the rest of imformation to df
    rb_df["WAHLPERIODE"] = wahlperiode
    rb_df["NR"] = nr
    rb_df["DATUM"] = datum

    # create ko df
    ko_df = pd.DataFrame.from_dict(ko_dict, orient = "index").reset_index()
    ko_df = ko_df.rename(columns={"index":"RB_ID", 0:"KO_Name"})

    return rb_df, ko_df, rb_ID, wahlperiode

