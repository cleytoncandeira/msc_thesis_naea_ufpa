from lists_and_dicts import *
import pandas as pd

database = pd.read_csv('/home/cleyton/ProjetosGit/msc_thesis_naea_ufpa/code_certified_producers_rtrs.csv')

def extract_range(data_base, companies, row):

        data_base['idx'] = [i for i  in range(1, row + 1)]

        #List
        data_base_list = [data_base[data_base["Companies"] == aud_comp] for aud_comp in companies]

        #Idx List
        idx_list = [i['idx'].tolist() for i in data_base_list]
            
        return idx_list

row, _ = database.shape

idx_list = extract_range(database, companies, row)

for k,j in enumerate(companies):
    idx_list[k].insert(0, j)

dictionary = {}

for i in range(len(idx_list)):
      dictionary[idx_list[i][0]] = idx_list[i][1:]

print(dictionary)
