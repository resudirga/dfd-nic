# -*- coding: utf-8 -*-
"""
Process INIDE's Area by Municipality Table and link it with municipalities in the GADM table.
Original Area by Municipality Table was taken from http://www.inide.gob.ni/compendio/pdf/inec112.pdf

1) Create a table KEYS_INIDE_GADM: For each municipality in the INIDE table, find the corresponding key (OBJECTID) in the GADM's NIC_ADM2 table (municipality shapefiles)
2)  Create GADM_Area table : Municipality area in sqkm 
"""

import os, sys
import pandas as pd
import difflib

DATADIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data/") 
INIDE_FPATH = DATADIR + "Area/INIDE_Area_by_Municipality.csv"
GADM_FPATH = DATADIR + "NIC_adm/NIC_adm2.csv"

inide_df = pd.read_csv(INIDE_FPATH, delimiter = ',', header=0, encoding='utf-8', 
                      dtype = {'Muni_ID' : str, 'Department' : str, 'Municipality' : str, 'Area_km2' : float})
     
gadm_df = pd.read_csv(GADM_FPATH, delimiter = ',', header=0, encoding='utf-8')
                      
inide_gadm_df = pd.DataFrame(data = {'Municipality' : gadm_df['NAME_2'].astype(str),
                                     'GADM_OBJECTID' : gadm_df['OBJECTID'].astype(str), 
                                     'INIDE_muniID' : None})
                                     
gadm_area_df = pd.DataFrame(data = {'Municipality' : gadm_df['NAME_2'].astype(str),
                                     'GADM_OBJECTID' : gadm_df['OBJECTID'].astype(str), 
                                     'INIDE_Area' : None})

del gadm_df

inide_names = inide_df['Municipality'].tolist()

def get_inide_muni(gadm_muni_name):
    """
    Return the name of a municipality from the INIDE table given its GADM municipality name
    """
    name = None
    if gadm_muni_name:
        name = difflib.get_close_matches(gadm_muni_name, inide_names, n=1, cutoff=0.6)
        name = name[0] if name else None
    return name

def get_inide_muniID(gadm_muni_name):
    """
    Return the INIDE muniID given its GADM municipality name
    """
    inideID = None
    if gadm_muni_name:
        inide_name = get_inide_muni(gadm_muni_name)
        if inide_name:
            inideID = inide_df.loc[inide_df['Municipality'] == inide_name, 'Muni_ID'].values[0] 
    return str(inideID)
    
def get_inide_area(inide_id):
    """
    Return the area of a municipality given its id from the INIDE table
    """
    area = inide_df.loc[inide_df['Muni_ID'] == inide_id, 'Area_km2'].values
    area = float(area[0]) if area else None
    return area
    
inide_gadm_df['INIDE_muniID'] = inide_gadm_df['Municipality'].map(lambda x: get_inide_muniID(x))

gadm_area_df['INIDE_ID'] = gadm_area_df['Municipality'].map(lambda x: get_inide_muniID(x))
gadm_area_df['INIDE_Area'] = gadm_area_df['INIDE_ID'].map(lambda x: get_inide_area(x))
 
del gadm_area_df['INIDE_ID']

# KEYS_GADM_INIDE table
output_fname = "Area/" + "TEMP_KEYS_GADM_INIDE.csv"
inide_gadm_df.to_csv(DATADIR + output_fname, delimiter = ',', header=True, quotechar='"', encoding='utf-8', index=False)

# GADM_Area table
output_fname = "Area/" + "TEMP_GADM_Area.csv"
gadm_area_df.to_csv(DATADIR + output_fname, delimiter = ',', header=True, quotechar='"', encoding='utf-8', index=False)

                      


