import requests
import json
import pandas as pd
import datetime as dt
import config
from dateutil.relativedelta import relativedelta


ARIA_ACCOUNTS = {
    10120066: 'Free',
    10120067: 'Silver',
    10131335: 'Bronze',
    10134266: 'Dedicated Node Service'
}


def get_exchange_rates(currency_list):
    r = requests.get('http://api.fixer.io/latest?base=USD')
    exchange_rates = json.loads(r.text).get('rates', {})
    exchange_rates['USD'] = 1.0
    return {currency: rate for currency, rate in exchange_rates.items() if currency.upper() in [curr.upper() for curr in currency_list]}


def convert_currency(df, *args, **kwargs):
    exchange_rate = kwargs['rates'].get(df.Currency.upper(), 1.0)
    df['ConvertedAmount'] = df.Amount / exchange_rate
    return df


def convert_country_to_region(df, *args, **kwargs):
    if df['Country'] in ['US', 'CA']:
        df['Region'] = 'NA'
    else:
        df['Region'] = 'EU'
    return df


def provide_plan_name(df, *args, **kwargs):
    df['PlanName'] = ARIA_ACCOUNTS.get(df['Plan No'], df['Plan No'])
    return df


def provide_display_name(df, *args, **kwargs):
    df['DisplayName'] = df['Company Name'] if df['Company Name'] is not pd.np.nan else '{0} {1}'.format(df['First Name'], df['Last Name'])
    return df


def extract_previous_month_data(invoice_file, account_file, export_file, num_months, max_records, sort='average'):
    invoices = pd.read_csv(invoice_file)
    accounts = pd.read_csv(account_file)

    # Clean up invoice data before merge
    invoices['Payment Date'] = pd.to_datetime(invoices['Payment Date'])  # Convert Payment Date into a usable format
    # Select only those invoices within the last 3 months and excluding current month
    invoices = invoices[(invoices['Payment Date'] >= (dt.date.today().replace(day=1) + relativedelta(months=-num_months)))
                        & (invoices['Payment Date'] < dt.date.today().replace(day=1))]
    invoices = invoices[invoices['Description'] == 'Approved']  # Filter out invoices that haven't been paid
    rates = get_exchange_rates(invoices.Currency.unique())  # Capture used currency values, and call out for rate
    invoices = invoices.apply(convert_currency, axis='columns', rates=rates)  # Convert amount values
    invoices['PaymentMonth'] = invoices['Payment Date'].map(lambda date: str(date.month) + '-' + str(date.year))
    payment_months_pivot = pd.pivot_table(invoices, index='Acct No', columns='PaymentMonth', values='ConvertedAmount',
                                          aggfunc='sum')  # Transform payment date based on the month to a column

    # Clean up account data before merge
    accounts = accounts.apply(provide_plan_name, axis='columns')  # Translate plan # into plan name
    accounts = accounts.apply(convert_country_to_region, axis='columns')  # Apply region code based on country ('US' & 'CA' -> 'NA)

    # Merge accounts with their invoices
    aria = accounts.merge(payment_months_pivot, left_on='Account', right_index=True)
    aria = aria.apply(provide_display_name, axis='columns')
    aria['Summary-Last_' + str(num_months) + '_months'] = aria[list(invoices['PaymentMonth'].unique())].sum(axis='columns')
    aria['Average'] = aria[list(invoices['PaymentMonth'].unique())].mean(axis='columns')

    # Provide cleaned and sorted data for export
    if sort == 'average':
        export = aria.sort_values('Average', ascending=False)
    elif sort == 'summary':
        export = aria.sort_values('Summary-Last_' + str(num_months) + '_months', ascending=False)
    export = export.iloc[:max_records]
    export = export[
        ['DisplayName', 'First Name', 'Last Name', 'Email', 'Country', 'Region', 'PlanName', 'Account'] + list(invoices['PaymentMonth'].unique()) + [
            'Summary-Last_' + str(num_months) + '_months', 'Average']]
    export.to_csv(export_file, index=False)


if __name__ == '__main__':
    extract_previous_month_data('all-payment-detail.csv', 'account-details.csv', 'export.csv',
                                config.PAST_MONTHS, config.TOTAL_RECORDS, config.SORT)
