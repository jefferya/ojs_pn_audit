# PKP OJS Preservation Network (PN) Audit Helpers

The goal of this repository is to provide scripts to help identify and diagnose preservation problems of OJS journals with the PKP PN (Preservation Network) plugin enabled

## Requirements

* Python 3
* Pandas

## Audit local OJS instances against the PN journal list (ojs_pn_audit)

Audit the preservation status of multiple OJS Journal sites against the PKP Preservation Network (PN). The pain point this repository solves is the ability to log in to multiple OJS sites and via the API, gather a list of all the journal issues and compare them against the OJS PKP Preservation Network journal list to audit the preservation status of each journal issue.

Note: verification is based on the journal URL, journal volume, journal number, and publication date (unless blank). However, I've found serval instances circa February 2023 where the publication date differs.

### Usage

``` bash
ojs_pn_audit.py --journal_list ${path_to_OJS_journal_list} --output_file data/pn_audit_`date +"%Y-%m-%d"`.csv
```

Where:

* journal_lists: a file listing the URL of each journal, one per line
* output_file: stores the results of the audit in a CSV format

### Notes

* Preservation Network OJS Plugin notes on how to check status: <https://docs.pkp.sfu.ca/pkp-pn/en/#checking-status-in-ojs> and a link to the PN journal list used by the script. The list is updated nightly according to the website but might be less often in practice.
* OJS API <https://docs.pkp.sfu.ca/dev/api/ojs/3.3#tag/Issues>

### Todo

* Python usage is rough as this is a quick proof-of-concept quality script (e.g., no tests)
* Not fully tested
* Confusion occurs when the PN journal list doesn't contain enough information to differentiate rows
* Other Todo's mentioned in the scripts

### Debugging PN error notes

* https://forum.pkp.sfu.ca/t/why-pkp-pn-locks-status-not-change/63129
* https://pkp.sfu.ca/pkp-pn/
* https://github.com/pkp/pln
* https://github.com/pkp

## Test Preservation Problems (ojs_export_articles_in_issue)

For items failing preservation, one tip for OJS 3.3 is to use the XML export on the impacted issue and if the export fails then the type of failure provides insight into why the preservation plugin (PKP PN plugin) fails for that particular journal issue. This script provides the ability to export individual issue articles to determine which article(s) in the journal issue are impacting the preservation of the journal issue.

### Usage

```bash
python3 ojs_export_articles_in_issue.py --journal_issue_id 23 --journal_url https://demo.publicknowledgeproject.org/ojs3/testdrive/index.php/testdrive-journal/
```

The output assumes that OJS 3.3 return a header content type different than normal operation (e.g., HTML as opposed to application/XML) and displays what the export reports as a problem in the HTML response. Note: this may fail in OJS versions above or below 3.3 as the script uses assumptions tied to the Web UI (e.g., article export is not available in the API).

## Produce a list of unique journal URLs from the PN journal list (ojs_pn_list_urls)

The goal is to help gather the list of URLs to use with ojs_pn_audit. The script downloads the PN journal list and finds all the unique URLs.

### Usage

``` bash
python3 ojs_pn_list_urls.py
```
