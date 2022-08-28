import pandas as pd
import xml.etree.ElementTree as ET
import re
import csv

def get_ortszusatz() -> set:
    """
    extracts and cleans all city additions from the stammdaten.xml 
    and creates a list
    """
    ortszusatz = []
    stammdaten = ET.parse("./protokolle_wp_1-12/other/MDB_STAMMDATEN.XML").getroot()

    for city in stammdaten.iter("ORTSZUSATZ"):
        ortszusatz.append(city.text)

    ortszusatz = list(set(ortszusatz))
    ortszusatz = [elem[1:-1] for elem in ortszusatz if pd.isnull(elem) == False]

    return ortszusatz

def clean_dfs(RB_df: pd.DataFrame, KO_df: pd.DataFrame, ortszusatz: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    cleans the entries. calls other functions to extract important parts
    """
    # some comments get catched because they stretch over multiple lines
    # cut off from the previous part by a newline, they get filtered here
    RB_df = RB_df[~RB_df["RB_Name"].str.contains("\[")]

    # the positive look behind didn't work, this is the alternative
    KO_df["KO_Name"] = KO_df["KO_Name"].str[1:]

    # extracts parts like dr titles and position
    RB_df, KO_df = extract_transform_df(RB_df, KO_df)      

    # extracting additions and political parties inside the brackets
    RB_df, KO_df = extract_brackets_df(RB_df, KO_df, ortszusatz)   

    # delete the bracket parts
    RB_df["RB_Name"] = RB_df["RB_Name"].str.split(pat=" \(", n=1).str[0]
    KO_df["KO_Name"] = KO_df["KO_Name"].str.split(pat=" \[", n=1).str[0]

    # clean of leading and trailing whitespace
    RB_df["RB_Name"] = RB_df["RB_Name"].str.strip()
    RB_df["RB_Name"] = RB_df["RB_Name"].str.rstrip(",") 
    KO_df["KO_Name"] = KO_df["KO_Name"].str.strip()
    KO_df["KO_Name"] = KO_df["KO_Name"].str.rstrip(",") 

    return RB_df, KO_df

def extract_transform_df(RB_df: pd.DataFrame, KO_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    extracts parts like titles (both academically and noble) and positions.
    splits KO on " — " to get all KO  
    """
    # extracts additional KO that are currently mushed together
    # splits and unpivots the data
    # to bypass split error - columns must be same lenght as key: save individually and concat
    # KO_df[["KO_Name", "KO_Name.1", "KO_Name.2","KO_Name.3"]] = KO_df["KO_Name"].str.split(" — ", n=3, expand=True)
    temp_KO_df = KO_df["KO_Name"].str.split(" — ", n=3, expand=True)
    temp_KO_df.columns = ["KO_Name_Nr{}".format(x+1) for x in temp_KO_df.columns]
    KO_df = pd.concat([KO_df, temp_KO_df], axis=1).reindex(KO_df.index).drop(columns=["KO_Name"])
    KO_df = KO_df.melt(id_vars=["RB_ID"], var_name="KO_Name_Nr", value_name="KO_Name").drop(columns=["KO_Name_Nr"])
    KO_df = KO_df[~KO_df["KO_Name"].isnull()]

    # cuts off everything after ":"
    KO_df["KO_Name"] = KO_df["KO_Name"].str.replace(r"(?<=.):.*", "", regex=True)

    re_dict = {
                "GESCHLECHT":r"(Frau(?= )|Abg.(?= ))",
                "FUNKTION":r"((?<=., ).*)",
                "POSITION":r"^(Alterspräsidenti?n?|Vizepräsidenti?n?|Präsidenti?n?)",
                "ANREDE_TITEL":r"(Prof\. Dr\. - Ing\.|Prof\. Dr\.|Prof\.|Dr\. h\. c\.|Dr\. - Ing\.|Dr\.-Ing\.|D\. Dr\.|Dr\.)",
                "PRAEFIX":r"((?<!\w)de(?= )|(?<!\w)van(?= )|(?<!\w)vom(?= )|(?<!\w)von der(?= )|(?<!\w)von und zu(?= )|(?<!\w)von(?= )|(?<!\w)zu(?= ))",
                "ADEL":r"(Baron|Freiherr|Fürst zu|Fürst|Gräfin|Graf|Prinz zu|Prinz)"
            }

    # extract and cut off all of the defined parts
    for regex in re_dict:
        RB_df[regex] = RB_df["RB_Name"].str.extract(re_dict[regex])
        RB_df["RB_Name"] = RB_df["RB_Name"].str.replace(re_dict[regex], "", regex=True)

        KO_df[regex] = KO_df["KO_Name"].str.extract(re_dict[regex])
        KO_df["KO_Name"] = KO_df["KO_Name"].str.replace(re_dict[regex], "", regex=True)     

    RB_df["GESCHLECHT"] = RB_df["GESCHLECHT"].str.replace("Frau", "weiblich", regex=True)
    RB_df["GESCHLECHT"] = RB_df["GESCHLECHT"].str.replace("Abg.", "", regex=True)
    KO_df["GESCHLECHT"] = KO_df["GESCHLECHT"].str.replace("Frau", "weiblich", regex=True)
    KO_df["GESCHLECHT"] = KO_df["GESCHLECHT"].str.replace("Abg.", "", regex=True)

    # filter unpersonalized KO (applause, laugh, etc.)
    KO_df = KO_df[~KO_df["KO_Name"].str.contains("(Beifall|Lachen|Zustimmung|Widerspruch|Unruhe|Heiterkeit) bei", regex=True, na=False)]

    return RB_df, KO_df

def extract_brackets_df(RB_df: pd.DataFrame, KO_df: pd.DataFrame, ortszusatz: set) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    cleans and extracts political party and city inside brackets 
    """
    with open("protokolle_wp_1-12/other/austauschen.csv", encoding="utf-8-sig") as csv_file:
        change = csv.DictReader(csv_file, delimiter=";")
        
        for err in change:
            RB_df["RB_Name"] = RB_df["RB_Name"].str.replace(re.escape(err["round_f_partei"]), err["round_r_partei"], regex=True)
            KO_df["KO_Name"] = KO_df["KO_Name"].str.replace(re.escape(err["square_f_partei"]), err["square_r_partei"], regex=True)
        
        party_re = r"(BP|GB\/BHE|SRP|DP|DRP|SPD|CSUS|WAV|DSU|DIE LINKE\.|DPB|KPD|BÜNDNIS 90\/DIE GRÜNEN|FDP|DZP|CDU\/CSU|DPS|CVP|FU)"
        RB_df["PARTEI"] = RB_df["RB_Name"].str.extract(party_re)
        KO_df["PARTEI"] = KO_df["KO_Name"].str.extract(party_re)

        ortszusatz_str = "|".join([str(x) for x in ortszusatz])
        RB_df["ORTSZUSATZ"] = RB_df["RB_Name"].str.extract("(" + repr(ortszusatz_str) + ")")
        KO_df["ORTSZUSATZ"] = KO_df["KO_Name"].str.extract("(" + repr(ortszusatz_str) + ")")

    return RB_df, KO_df

