# ojs_pn_audit

Audit the preservation status of multiple OJS Journal sites against the PKP Preservation Network (PN). The pain point this repository solves is the ability to login to multiple OJS sites and via the API gather a list of all the journal issues then compare against the OJS PKP Preservation Network journal list to audit the preservation status of each journal issue.

## Usage

``` bash
ojs_pn_audit.py --journal_list ${path_to_OJS_journal_list} --output_file data/pn_audit_`date +"%Y-%m-%d"`.csv
```

Where:
* journal_lists: a file with the url of each journal, one per line
* output_file: a CSV containing each journal issue found plus a Preservation Network (PN) deposit date (if deposited) plus some other metadata to help diagnos errors

## Requirements
* Python 3 (with Pandas)

## Notes
* Preservation Network OJS Plugin notes on how to check status: <https://docs.pkp.sfu.ca/pkp-pn/en/#checking-status-in-ojs> and a link to the PN journal list used by the scripts that is update nightly according to the website but might be less often in practice.
* OJS API <https://docs.pkp.sfu.ca/dev/api/ojs/3.3#tag/Issues>

## Todo
* Python usage is rough as this is a quick proof-of-concept quality script (e.g., no tests)
* Not fully tested
* Confusion occurs when the PN journal list doesn't contain enough information to differentiate rows
* Other Todo's mentioned in the scripts

## Debugging PN errors notes
* https://forum.pkp.sfu.ca/t/why-pkp-pn-locks-status-not-change/63129
* https://pkp.sfu.ca/pkp-pn/
* https://github.com/pkp/pln
* https://github.com/pkp


