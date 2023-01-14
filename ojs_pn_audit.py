###############################################################################
# Desc: compare the list of OJS Journal issues with the Preservation Network
#       list of preserved journal issues and highlight failures
# Usage: python2 ojs_pn_audit.py --journal_list ${path_to_OJS_journal_list} --output_file data/pn_audit_`date +"%Y-%m-%d"`.csv
# license: CC0 1.0 Universal (CC0 1.0) Public Domain Dedication
# date: January 09, 2023
##############################################################################################

# Proof-of-concept only

from getpass import getpass
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import argparse
import csv
import json
import logging
import requests
import pandas
import shutil
import tempfile
import time

# OJS PK PN journal list status
# https://docs.pkp.sfu.ca/pkp-pn/en/#checking-status-on-pkp-pn-journal-list (January 2023)
# file is of the form:
#     Generated,2023-01-09
#     ISSN,Title,Publisher,Url,Vol,No,Published,Deposited
#     1715-720X,"Evidence Based Library and Information Practice","University of Alberta Library",https://journals.library.ualberta.ca/eblip/index.php/EBLIP,1,4,2006-12-13,2022-11-26
#     ...
#PN_JOURNAL_LIST_STATUS = 'http://web.archive.org/web/20220706192952/http://pkp.sfu.ca/files/pkppn/onix.csv'
PN_JOURNAL_LIST_STATUS = 'http://pkp.sfu.ca/files/pkppn/onix.csv'


#
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--journal_list', required=True, help='List of OJS Journal urls (one per line).')
    parser.add_argument('--output_file', required=True, help='CSV output file listing journal issue Preservation Network status.')
    return parser.parse_args()

# Get the PKP OJS Preservation Network status file
# https://docs.pkp.sfu.ca/pkp-pn/en/#checking-status-on-pkp-pn-journal-list (January 2023)
def download_file(tmp_file, url=PN_JOURNAL_LIST_STATUS, ):
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        tmp_file.write(r.text)
        generated_date = r.text.partition('\n')[0].replace(',',' ')
        print(f"PN file date: {generated_date}")
        print("------------")

# Filter larger Preservation Network list to only those of interest as defined in the input
def get_relevant_pn_journal_info(journal_list):
    df_filtered = []
    with tempfile.NamedTemporaryFile(mode="wt") as tmp_file:
        download_file(tmp_file, PN_JOURNAL_LIST_STATUS)
        # read the CSV from PN (without first line: "Generated,2022-12-15")
        df = pandas.read_csv(tmp_file.name, skiprows=[0], low_memory=False)
        # filter larger PN Journal List
        df_filtered = df[df['Url'].isin(journal_list)]
        #df_filtered = df_filtered.astype(dtype={'Url':'string', 'Deposited':'string', 'Vol':'string', 'No':'string'})
        # Todo: not sure if Pandas automatically assign a numeric datatype causes a problem; will explicitly set the datatype
        df_filtered = df_filtered.astype(dtype={'Vol':'object', 'No':'object'})
    return df_filtered

#
def read_journal_list(journal_list_file):
    data = []
    with open(journal_list_file, "r") as f:
        data = [line.rstrip() for line in f]
        return data

# Start a session with a given OJS instance
def ojs_session(url, username, password):
    try:
        session = requests.Session()

        # first request: get CSRF token
        tmp = url.strip('/') + "/login"
        response = session.get(tmp)
        soup = BeautifulSoup(response.text, "lxml")
        csrf_token = soup.find('input', {'name':'csrfToken'})['value']

        # sencond request: signIn and load cookie into session
        tmp = url.strip('/') + "/login/signIn"
        data = {
            "csrfToken": csrf_token,
            "username": username,
            "password": password,
            "remember": '1'
        }
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        response = session.post(tmp, data=data, headers=headers)
        response.raise_for_status() # HTTP status for OJS 3 is 200 even if password fails
    except requests.exceptions.HTTPError as error:
        logging.warning(response.content, exc_info=False)
        session.close()
        session = None
    finally:
        return session

# filter the PN journal list to find corresponding OJS journal issue and if not found then not OJS journal issue not preserved
def filter_pn_journal_list(url, issue, pn_df):
    # Sometimes the volume or number are blank, represented as "None" in the JSON datastructure import from the OJS API
    # The 'None" value fails to match an empty cell value in the Pandas dataframe when filtering PN network journal list
    # thus resulting in the following the ugly if/else loop
    # Todo: learn a better approach to filter Pandas
    date_published = issue['datePublished'][:10] # only the YYYY-MM-DD; sometimes the OJS /issue api returns date and time
    if (issue["volume"] == None and issue["number"] == None):
        pn_status = pn_df.loc[
            (pn_df['Url'] == url) &
            (pn_df['Published'] == date_published)
            ]
    elif (issue["volume"] == None):
        pn_status = pn_df.loc[
            (pn_df['Url'] == url) &
            (pn_df['No'] == issue['number']) &
            (pn_df['Published'] == date_published)
            ]
    elif (issue["number"] == None):
        pn_status = pn_df.loc[
            (pn_df['Url'] == url) &
            (pn_df['Vol'] == issue['volume']) &
            (pn_df['Published'] == date_published)
            ]
    else:
        pn_status = pn_df.loc[
            (pn_df['Url'] == url) &
            (pn_df['Vol'] == issue['volume']) &
            (pn_df['No'] == issue['number']) &
            (pn_df['Published'] == date_published)
            ]
    return pn_status


# For each journal issue found on an OJS server, lookup the preservation network equivalent and conbine into an audit report
def process_issue_list(journal_issues, pn_df, url, pn_status_csv):

    if (journal_issues['itemsMax'] == 0):
        # if no journal issues then fill in the url colume only for the row
        pn_status_csv.writerow({'url': url})

    for issue in journal_issues['items']:

        # lookup jounal issue in PN status report
        # Note: title is not always available via the OJS API
        # Note: the Url + Vol + No should produce a unique row in the OJS PKP PN status rows
        logging.info(f"Checking Vol. {issue['volume']} No. {issue['number']} - Title: {issue['identification']} - (OJS issue id: {issue['id']})")
        logging.debug(pn_df.dtypes)
        pn_status = pandas.DataFrame()
        # ignore if no published date
        if (issue['datePublished'] != None):
            pn_status = filter_pn_journal_list(url, issue, pn_df)
        if pn_status.empty:
            logging.debug(f"Status: not found in OJS PKP PN")
            status_dict = {
                'Journal Url': url,
                'Issue OJS ID': issue['id'],
                'Issue Title': issue['identification'],
                'Issue Volume': issue['volume'],
                'Issue Number': issue['number'],
                'Issue Year': issue['year'],
                'Issue Date Published': issue['datePublished'],
            }
        else:
            if pn_status.count()[0] > 1:
                # sometimes the PN status file has multiple rows for the same volume number
                logging.warning(
                    f"Warning: multiple PN status records - this should not happen - url {url} issue id:{issue['id']} vol: {issue['volume']} no: {issue['number']} deposited: {pn_status['Deposited'].values[0]}"
                    )
                pn_status = pn_status.sort_values(by=['Deposited'], ascending=[False])
            logging.info(f"Status: OJS PKP PN Deposited: {pn_status['Deposited'].values[0]}")
            status_dict = {
                'Journal Url': url,
                'Issue OJS ID': issue['id'],
                'Issue Title': issue['identification'],
                'Issue Volume': issue['volume'],
                'Issue Number': issue['number'],
                'Issue Year': issue['year'],
                'Issue Date Published': issue['datePublished'],
                'PN ISSN': pn_status['ISSN'].values[0],
                'PN Title': pn_status['Title'].values[0],
                'PN Published': pn_status['Published'].values[0],
                'PN Deposited': pn_status['Deposited'].values[0]
            }
        pn_status_csv.writerow(status_dict)


#
def get_journal_issues(session, base_url, res_count, res_offset):
    # get list of issues from OJS by pages of items
    # https://docs.pkp.sfu.ca/dev/api/ojs/3.2#tag/Issues
    try:
        url = base_url.strip('/') + "/api/v1/issues"
        # ToDo: verify that only return "isPublished" issues as the PKP PN only records published items
        # https://mrujs.mtroyal.ca/index.php/bsuj, issueId: 11, Vol. 2 No. 1 (2014): appears was published, preserved and then unpublished?
        # payload = { "count": res_count, "offset": res_offset, "isPublished": "true" }
        payload = { "count": res_count, "offset": res_offset }
        response = session.get(url, params=payload)
        response.raise_for_status()
        ret = json.loads(response.text)
    except requests.exceptions.HTTPError as error:
        print(url)
        logging.exception(response.content, exc_info=False)
        ret = None
    finally:
        return ret

#
def process(args, username, password, pn_status_csv):
    journal_list = read_journal_list(args.journal_list)
    logging.debug(journal_list)
    print("------------")

    pn_df = get_relevant_pn_journal_info(journal_list)
    logging.debug(pn_df)

    for i in journal_list:
        print(f"Journal URL: {i}")
        session = ojs_session(i, username, password)
        if (session == None):
            break;

        try:
            res_count = 20
            res_offset = 0
            while True:
                journal_issues = get_journal_issues(session, i, res_count, res_offset)

                if journal_issues is None:
                    break

                process_issue_list(journal_issues, pn_df, i, pn_status_csv)

                logging.info(f"itemsMax: {journal_issues['itemsMax']} res_offset: {res_offset} count: {res_count}" )
                if journal_issues["itemsMax"] <= (res_count + res_offset):
                    break;
                else:
                    res_offset = res_offset + res_count

        except Exception as e:
            logging.exception("Failed to match OJS journal issue to PN row")
        finally:
            session.close()

        # sleep between journals to reduce server load
        time.sleep(5)
        print("------------")


#
def main():
    args = parse_args()

    # Todo: allow setting via the CLI or config file
    #logging.basicConfig(level=logging.INFO)
    logging.basicConfig(level=logging.WARNING)

    username = input('Username:')
    password = getpass('Password:')

    with open(args.output_file, 'wt', encoding="utf-8", newline='') as output_file:
        pn_status_csv = csv.DictWriter(output_file, fieldnames=[
            'Journal Url',
            'Issue OJS ID',
            'Issue Title',
            'Issue Volume',
            'Issue Number',
            'Issue Year',
            'Issue Date Published',
            'PN ISSN',
            'PN Title',
            'PN Published',
            'PN Deposited'
        ])
        pn_status_csv.writeheader()

        process(args, username, password, pn_status_csv)


if __name__ == "__main__":
    main()
