from pathlib import Path
from download_pdfiles import certified_producers_rtrs #add companies col after
from extract_data_from_pdf import DictTags, Search
from lists_and_dicts import *

ROOT_FOLDER = Path(__file__).parent

row, _ = certified_producers_rtrs.shape 

dict_tags = DictTags(companies, variables)

#dict_tags for RegTag
dict_tags.Reg_Tags(regtags, "RegTag")

#search obj
search_engine = Search()

#define empty lists

"""
Remember!

    test_list -- List to test the automate 
    reg_result -- Here will be the tags captured
    company_classify  -- enterprise name classification 

"""
search_engine.row_length = row
search_engine.dict_companies = dict_tags 

search_engine.insert_kwargs(test_list = list(), 
                            reg_result = list(), 
                            company_classify = list(),
                            reports_to_fix = None)

search_engine.variable_target = "RegTag"

#Now we automate...

for n_report in range(1, row):

    file_str = 'audit_report_rtrs' + str(n_report) + ".pdf"
    path_reports = ROOT_FOLDER / 'audit_reports' / file_str
                        
    search_engine.report_pages = dict_tags.extract_pages(path_reports) 

    for companies_names, variable in dict_tags.dict_companies.items():

       tag_found = search_engine.findall(variable.get(search_engine.variable_target))    
       
       if bool(tag_found) is True:
            search_engine.add_tag(tag_found, company_name = companies_names)

       else:
            search_engine.add_tag(no_iterator = n_report)

search_engine.test_findall()
search_engine.fix_length()
search_engine.fix_value = 'C868389AGR-01.2020'
search_engine.add_values_to_df_and_export(certified_producers_rtrs, ROOT_FOLDER)