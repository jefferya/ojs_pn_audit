###############################################################################
# Desc: given an journal issue id, export each article in the issue to help test PN 
# Usage: python3 ojs_export_articles_in_issue.py --journal_issue_id 23 --journal_url https://demo.publicknowledgeproject.org/ojs3/testdrive/index.php/testdrive-journal/
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
import requests
import pandas
import shutil
import tempfile
import time

#
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--journal_issue_id', required=True, help='OJS ID for a given journal issue.')
    parser.add_argument('--journal_url', required=True, help='OJS base journal URL.')
    return parser.parse_args()

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
        # print(f"{response.content}")
        response.raise_for_status()
    except requests.exceptions.HTTPError as error:
        print(response.content)

    return session

def get_journal_issue_articles(session, base_url, res_count, res_offset, issue_id):
    # get list of issues from OJS by pages of items
    # https://docs.pkp.sfu.ca/dev/api/ojs/3.2#tag/Issues
    try:
        url = base_url.strip('/') + "/api/v1/submissions"
        # payload = { "count": res_count, "offset": res_offset, "isPublished": "true" }
        payload = { "count": res_count, "offset": res_offset, "issueIds": issue_id }
        response = session.get(url, params=payload) 
        response.raise_for_status()
        ret = json.loads(response.text)
    except requests.exceptions.HTTPError as error:
        print(f" Error: {url}")
        print(response.content)
        ret = None 
    
    return ret 

def export_article(session, base_url, article_id):
    try:
        url = base_url.strip('/') + "/management/importexport/plugin/NativeImportExportPlugin/exportSubmissions"
        payload = { "selectedSubmissions": article_id}
        response = session.post(url, params=payload) 
        print(response.headers)
        response.raise_for_status()
        print(f"articleId: {article_id} - ok")
    except requests.exceptions.HTTPError as error:
        print(f" Error: {url}")
        print(f"articleId: {article_id} - ERROR")
        print(response.content)
        ret = None 
    
#
def process_article_list(session, args, article_list):
    for article in article_list["items"]:
        export_article(session, args.journal_url, article['id'])

#
def process(args, username, password):

        print(f"Journal URL: {args.journal_url}")
        session = ojs_session(args.journal_url, username, password)

        try:
            res_count = 20
            res_offset = 0
            while True:
                journal_issue_articles = get_journal_issue_articles(session, args.journal_url, res_count, res_offset, args.journal_issue_id)
                
                if journal_issue_articles is None:
                    break 

                process_article_list(session, args, journal_issue_articles)

                #print(f"itemsMax: {journal_issues['itemsMax']} res_offset: {res_offset} count: {res_count}" )
                if journal_issue_articles["itemsMax"] <= (res_count + res_offset):
                    break;
                else:
                    res_offset = res_offset + res_count

        except Exception as e:
            print(e)
        finally:
            session.close()

        # sleep between journals to reduce server load
        time.sleep(5)
        print("------------")

#
def main():
    args = parse_args()

    username = input('Username:')
    password = getpass('Password:')

    process(args, username, password)


if __name__ == "__main__":
    main()   
