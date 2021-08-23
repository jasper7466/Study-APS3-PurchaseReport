import csv
from datetime import datetime
import locale
from collections import defaultdict

# config
LOCALE = "ru_RU.UTF-8"
INPUT_DATE_FORMAT = "%Y-%m-%d"
OUTPUT_DATE_FORMAT = "%b %Y"
NUM_OF_DECIMALS = 2
DATA_NESTING_SEQUENCE = ['type', 'shop', 'category', 'name']
PRICE_KEY = 'price'
AMOUNT_KEY = 'amount'
TOTAL_KEY = '!!total'
MONTHLY_KEY = '!!monthly'
METADATA_KEY = "!!meta"
RECORD_ALIASES = {
    'type': {
        'sale': 'Продажи',
        'buy': 'Покупки',
    },
}
RECORD_PLACEHOLDERS = {
    'category': 'Без категории',
}
COLUMN_WIDTH_ASIDE = 4
COLUMN_WIDTH_ASIDE_MAX = 60
COLUMN_WIDTH_BASE = 12


# utils/helpers
def append_placeholders(record, placeholders_dict):
    for key in record:
        if not record[key]:
            record[key] = placeholders_dict[key]


def append_aliases(record, aliases_dict):
    for key, aliases in aliases_dict.items():
        if key in record:
            record[key] = aliases[record[key]]


def subtotal(record):
    result = int(record[AMOUNT_KEY]) * float(record[PRICE_KEY])
    return round(result, NUM_OF_DECIMALS)


def get_nested_paths(source, record, sequence):
    layer = source
    result = []

    for key in sequence:
        if key not in record:
            break
        layer = layer[record[key]]
        result.append(layer)

    return result


def update_nested_totals(value, date_stamp, targets):
    for target in targets:
        target[METADATA_KEY][TOTAL_KEY] = target[METADATA_KEY].get(TOTAL_KEY, 0) + value
        target[METADATA_KEY][MONTHLY_KEY][date_stamp] = target[METADATA_KEY][MONTHLY_KEY].get(date_stamp, 0) + value


def date_formatter(date_string, input_format, output_format="%d-%m-%Y"):
    parsed = datetime.strptime(date_string, input_format)
    return parsed.strftime(output_format)


def init_nested_dict():
    return defaultdict(init_nested_dict)


def side_print(value, shift_index=1):
    depth = len(DATA_NESTING_SEQUENCE)

    for i in range(depth):
        if i != shift_index:
            print(f'{"":<{COLUMN_WIDTH_ASIDE}}', end='')
        else:
            print(f'{value :<{COLUMN_WIDTH_ASIDE_MAX}}', end='')


def new_line():
    print("")


# init
locale.setlocale(locale.LC_TIME, LOCALE)
storage = init_nested_dict()
dates = set()

# data processing
with open('table.csv') as file:
    transactions = csv.DictReader(file)
    for transaction in transactions:
        append_placeholders(transaction, RECORD_PLACEHOLDERS)
        append_aliases(transaction, RECORD_ALIASES)

        date = date_formatter(transaction['date'], INPUT_DATE_FORMAT, OUTPUT_DATE_FORMAT)
        dates.add(date)

        transaction_subtotal = subtotal(transaction)

        targets_to_update = get_nested_paths(storage, transaction, DATA_NESTING_SEQUENCE)

        update_nested_totals(transaction_subtotal, date, targets_to_update)

        # operation = storage[transaction['type']]
        # shop = operation[transaction['shop']]
        # category = shop[transaction['category']]
        # purchase = category[transaction['name']]
        #
        # operation[METADATA_KEY][MONTHLY_KEY][date] = round(
        #     operation[METADATA_KEY][MONTHLY_KEY].get(date, 0) + transaction_subtotal, NUM_OF_DECIMALS)
        # shop[METADATA_KEY][MONTHLY_KEY][date] = round(
        #     shop[METADATA_KEY][MONTHLY_KEY].get(date, 0) + transaction_subtotal, NUM_OF_DECIMALS)
        # category[METADATA_KEY][MONTHLY_KEY][date] = round(
        #     category[METADATA_KEY][MONTHLY_KEY].get(date, 0) + transaction_subtotal, NUM_OF_DECIMALS)
        # purchase[METADATA_KEY][MONTHLY_KEY][date] = round(
        #     purchase[METADATA_KEY][MONTHLY_KEY].get(date, 0) + transaction_subtotal, NUM_OF_DECIMALS)
        #
        # operation[METADATA_KEY][TOTAL_KEY] = round(operation[METADATA_KEY].get(TOTAL_KEY, 0) + transaction_subtotal,
        #                                            NUM_OF_DECIMALS)
        # shop[METADATA_KEY][TOTAL_KEY] = round(shop[METADATA_KEY].get(TOTAL_KEY, 0) + transaction_subtotal,
        #                                       NUM_OF_DECIMALS)
        # category[METADATA_KEY][TOTAL_KEY] = round(category[METADATA_KEY].get(TOTAL_KEY, 0) + transaction_subtotal,
        #                                           NUM_OF_DECIMALS)
        # purchase[METADATA_KEY][TOTAL_KEY] = round(purchase[METADATA_KEY].get(TOTAL_KEY, 0) + transaction_subtotal,
        #                                           NUM_OF_DECIMALS)

dates = sorted(dates, key=lambda date: datetime.strptime(date, OUTPUT_DATE_FORMAT))


# print
def print_report_header():
    side_print("")

    for date in dates:
        print(f'{date:>{COLUMN_WIDTH_BASE}}', end='')

    print(f'{"итог":>{COLUMN_WIDTH_BASE}}', end='')


def dict_deep_print(dictionary, level=0):
    for key in dictionary:
        if key == METADATA_KEY:
            continue

        side_print(key, level)

        for date in dates:
            print(f'{dictionary[key][METADATA_KEY][MONTHLY_KEY].get(date, 0):>{COLUMN_WIDTH_BASE}.{NUM_OF_DECIMALS}f}', end='')
        print(f'{dictionary[key][METADATA_KEY].get(TOTAL_KEY, 0):>{COLUMN_WIDTH_BASE}.{NUM_OF_DECIMALS}f}', end='')
        new_line()

        if isinstance(dictionary[key], dict):
            dict_deep_print(dictionary[key], level + 1)
        else:
            print(dictionary[key])


print_report_header()
new_line()
dict_deep_print(storage)
