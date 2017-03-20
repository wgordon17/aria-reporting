# Aria Reporting

## Requirements

This has been tested on Python 3.5 and is confirmed to work. It
is not expected to work in Python 2.

## Installing Dependencies

`pip install -r requirements.txt`

## Using

Modify the values in `config.py`

+ PAST_MONTH: The number of past months to include in the output.
    + E.g., 1 would imply the previous month only. This script excludes
    the current month.
+ TOTAL_RECORDS: After all records have been processed, and sorted based
on `SORT` value, the first `TOTAL_RECORDS` values are then kept and all
others removed
+ SORT: Specify which column to sort on
    + `average` (default) - The average amount based on all month columns
    + `summary` - The sum amount based on all month columns

Provide 2 Aria exports. Based on internal report names, we've used
*account-details.csv* and *all-payment-detail.csv*. These should be
included in the top-level directory of this script.

`python parse_aria.py` will create an export.csv file.