"""
This script create tables with Primary Keys to introduce SQL concept

"""

import pandas as pd
from pathlib import Path

path = Path(__file__).parent
csv_originals = path.parent / '1_DataSource' / 'csv_files'
sql_dir = path / 'sql'

name_id_map = csv_originals / "NameIDMap.csv"
org_id_map = csv_originals / "OrgIDMap.csv"

if not name_id_map.exists() and not org_id_map.exists():

    #Acess dataframe master Brazil RTRS
    brazil_rtrs = pd.read_csv(csv_originals / 'brazil_rtrs.csv')
    
    #Extract unique values
    name = brazil_rtrs['Name'].unique()
    org = brazil_rtrs['Organization'].unique()

    name_df = {'Name': name, 'NameID': range(1, len(name) + 1)}
    name_df = pd.DataFrame(name_df)

    org_df = {'Organization': org, 'OrgID': range(1, len(org) + 1)}
    org_df = pd.DataFrame(org_df)

    name_df.to_csv(sql_dir / 'NameIDMap.csv', index=False)
    org_df.to_csv(sql_dir / 'OrgIDMap.csv', index=False)









