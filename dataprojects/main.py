import pandas as pd
import fitz
import json
from typing import List, Dict

from . import *


class TemplateFormettor:
    def __init__(
        self,
        wallmart: object,
        validation: object,
        configs: List[Dict[str, str]],
        dataframe: [object, object],
    ) -> None:
        self.wallmart = wallmart
        self.validation = validation
        self.config = configs
        self.data = dataframe[0]
        self.rowdf = dataframe[1]

    def get_sorted_and_errors(self):
        errors = []
        maindf = []
        if self.config != []:
            for i in self.config:
                if self.validation.validate_po_wise_transections(
                    self.data, i["PoNo"], validationlength=i["validationlength"]
                ):
                    maindf.append(i)
                else:
                    errors.append(i)
        df_list2 = []
        for fd in maindf:
            rslt_df = self.rowdf[
                self.rowdf["PURCHASE ORDER NO"].str.contains(fd["PoNo"])
            ]
            df_list2.append(rslt_df)
        df_list = []
        for fd in errors:
            rslt_df = self.rowdf[
                self.rowdf["PURCHASE ORDER NO"].str.contains(fd["PoNo"])
            ]
            df_list.append(rslt_df)
        newdf = pd.concat(df_list)
        maindf = pd.concat(df_list2)
        return newdf, maindf

    def get_final_errors_data(self, validation: object, errortypes):
        sorteddata = validation
        maindf = pd.concat(
            [
                pd.DataFrame.from_records(sorteddata.get_sorted_data()[0]),
                self.get_sorted_and_errors()[1],
            ]
        )
        newdf = pd.DataFrame.from_records(sorteddata.get_sorted_data()[1])
        maindf = pd.DataFrame.from_records(sorteddata.get_sorted_data()[0])
        missingdatadf = []
        maindfdata = []
        for jh in self.config:
            if sorteddata.validate_po_wise_transections(
                maindf, jh["PoNo"], validationlength=jh["validationlength"]
            ):
                rslt_df = maindf[maindf["PURCHASE ORDER NO"].str.contains(jh["PoNo"])]
                maindfdata.append(rslt_df)
            else:
                datadict = {}
                rslt_df = maindf[maindf["PURCHASE ORDER NO"].str.contains(jh["PoNo"])]
                existingdata = [int(x) for x in rslt_df["Sr.No"].to_list()]
                missing = [x + 1 for x in range(jh["validationlength"])]
                finalmissingdata = []
                for x in missing:
                    if x not in existingdata:
                        finalmissingdata.append(x)
                    missingdatadf.append([rslt_df, finalmissingdata])
        missingdata = sorteddata.fillmissingdata(
            self.wallmart, missingdatadf, self.config
        )
        missingdf = [pd.DataFrame.from_records(x) for x in list(missingdata)]
        finaldf = []
        for x in missingdatadf:
            for y in missingdf:
                srno = [int(r) for r in y["Sr.No"].to_list()]
                s = x[0]["PURCHASE ORDER NO"].to_list()
                sx = y["PURCHASE ORDER NO"].to_list()
                if s != []:
                    if s[0] in sx:
                        finaldfd = pd.concat([x[0], y])
                        finaldf.append(finaldfd)

        finalmissingdata = pd.concat(finaldf)
        finaldfdaat = pd.concat([finalmissingdata, maindf])
        return finaldfdaat

    def get_formetted_data(self, validation: object, errortypes):
        finaldfdaat = self.get_final_errors_data(validation, errortypes)
        for uyte, jhcfsdj in finaldfdaat.iterrows():
            total = jhcfsdj["Tax Details"].split("-")[-1]
            total = total.replace("0.00", "")
            linecostex = jhcfsdj["Line Cost Excl Tax"].split(" ")[0]
            texdetails = jhcfsdj["Tax Details"].split("-")[0] + "- 0.00"
            rowtax = " ".join(jhcfsdj["Line Cost Excl Tax"].split(" ")[1:])
            texdetails = "{} - {}".format(rowtax, texdetails)
            jhcfsdj["Line Cost Excl Tax"] = float(linecostex)
            jhcfsdj["Total Amount incl tax"] = float(total)
            jhcfsdj["Tax Details"] = texdetails
            yield jhcfsdj.to_dict()

    def drop_duplicates_using_subsets(self, subset, validation: object, errortypes):
        derst = pd.DataFrame.from_records(
            list(self.get_formetted_data(validation, errortypes))
        )
        df = derst.drop_duplicates(subset=subset)
        return df

    def get_final_data_missing_files(self, validation: object, df):
        sorteddata = validation
        dfew = []
        missingpos = []
        for jh in self.config:
            if sorteddata.validate_po_wise_transections(
                df, jh["PoNo"], validationlength=jh["validationlength"]
            ):
                rslt_df = df[df["PURCHASE ORDER NO"].str.contains(jh["PoNo"])]
                costwithoutax = rslt_df["Line Cost Excl Tax"].sum()
                costwithtax = rslt_df["Total Amount incl tax"].sum()
                totalgfd = []
                for k, v in rslt_df.iterrows():
                    v["Total Cost Without Tax"] = costwithoutax
                    v["Grand Total Amount incl tax"] = costwithtax
                    v["Total tax Amount"] = costwithtax - costwithoutax
                    v["Vendor Stock"] = ""
                    v["ORDER DATE"] = "".join(v["ORDER DATE"].split(":"))
                    v["PO CANCEL DATE"] = "".join(v["PO CANCEL DATE"].split(":"))
                    totalgfd.append(v.to_dict())
                    dfew.append(pd.DataFrame.from_records(totalgfd))
        else:
            missingpos.append(jh["PoNo"])
        return pd.concat(dfew), missingpos
