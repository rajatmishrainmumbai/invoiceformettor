from dataprojects import *
import fitz
import pandas as pd
import json

fixtures = None
with open("./dataprojects/configs/fixtures.json", "rb") as td:
    fixtures = json.loads(td.read())
obj = Wallmart(
    "./dataprojects/pdfs/",
    fitz,
    configpath="./dataprojects/configs/veriations.json",
    indexmap=indexmap,
    jsonencoder=json,
)
dataobj = obj.get_records()
rowdf = pd.DataFrame.from_records(dataobj)

sorting = Validation(rowdf, validation1, errortypes=errortypes)
data = sorting.get_formetted_data()
template = TemplateFormettor(obj, sorting, configs=fixtures, dataframe=[data, rowdf])
sorteddata = Validation(
    template.get_sorted_and_errors()[0], sotingregex=validation1, errortypes=errortypes
)

finaldfdata = template.drop_duplicates_using_subsets(
    subset=subset, validation=sorteddata, errortypes=errortypes
)
finaldfdata = template.get_final_data_missing_files(sorteddata, finaldfdata)
df, missing = finaldfdata
df.to_csv("final.csv")
