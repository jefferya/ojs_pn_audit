###############################################################################
# Desc: list the unique urls in the PN Journal list 
# Usage: python3 ojs_pn_list_urls.py
# license: CC0 1.0 Universal (CC0 1.0) Public Domain Dedication
# date: January 09, 2023
##############################################################################################

# Proof-of-concept only

from getpass import getpass
import argparse
import requests
import pandas
import shutil
import sys 
import tempfile

# OJS PK PN journal list status
# https://docs.pkp.sfu.ca/pkp-pn/en/#checking-status-on-pkp-pn-journal-list (January 2023)
#PN_JOURNAL_LIST_STATUS = 'http://web.archive.org/web/20220706192952/http://pkp.sfu.ca/files/pkppn/onix.csv'
PN_JOURNAL_LIST_STATUS = 'http://pkp.sfu.ca/files/pkppn/onix.csv'

#
def parse_args():
    parser = argparse.ArgumentParser()
    #parser.add_argument('--pn_list', required=True, help='List of OJS Journal urls (one per line).')
    return parser.parse_args()

# 
def download_file(tmp_file, url=PN_JOURNAL_LIST_STATUS ):
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        tmp_file.write(r.text)

#
def process(args):
    df_filtered = []
    with tempfile.NamedTemporaryFile(mode="wt") as tmp_file:
        download_file(tmp_file, PN_JOURNAL_LIST_STATUS)
        # read the CSV from PN (without first line: "Generated,2022-12-15")
        df = pandas.read_csv(tmp_file.name, skiprows=[0], low_memory=False)        
        # filter larger PN Journal List 
        df_filtered = df.Url.unique()
    
    for item in df_filtered:
        print(item)


#
def main():
    args = parse_args()

    process(args)


if __name__ == "__main__":
    main()   