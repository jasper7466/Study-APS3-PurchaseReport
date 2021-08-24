import csv
import locale
from datetime import datetime
from collections import defaultdict, OrderedDict

# config
LOCALE = 'ru_RU.UTF-8'
INPUT_DATE_FORMAT = '%Y-%m-%d'
OUTPUT_DATE_FORMAT = '%b %Y'
NUM_OF_DECIMALS = 2
DATA_NESTING_SEQUENCE = ['type', 'shop', 'category', 'name']
PRICE_KEY = 'price'
AMOUNT_KEY = 'amount'
DATE_KEY = 'date'
TOTAL_KEY = '!!total'
MONTHLY_KEY = '!!monthly'
METADATA_KEY = '!!meta'
TOTAL_COLUMN_CAPTION = 'итог'
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
def init_nested_dict():
    return defaultdict(init_nested_dict)


def append_placeholders(record, placeholders_dict):
    for key in record:
        if not record[key]:
            record[key] = placeholders_dict[key]


def append_aliases(record, aliases_dict):
    for key, aliases in aliases_dict.items():
        if key in record:
            record[key] = aliases[record[key]]


def format_date(date_string, input_format, output_format='%d-%m-%Y'):
    parsed = datetime.strptime(date_string, input_format)
    return parsed.strftime(output_format)


def get_subtotal(record):
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


def update_nested_totals(value, datestamp, targets):
    for target in targets:
        target[METADATA_KEY][TOTAL_KEY] = target[METADATA_KEY].get(TOTAL_KEY, 0) + value
        target[METADATA_KEY][MONTHLY_KEY][datestamp] = target[METADATA_KEY][MONTHLY_KEY].get(datestamp, 0) + value


def print_aside(value, shift_index=1):
    depth = len(DATA_NESTING_SEQUENCE)

    for i in range(depth):
        if i != shift_index:
            print(f'{"":<{COLUMN_WIDTH_ASIDE}}', end='')
        else:
            print(f'{value :<{COLUMN_WIDTH_ASIDE_MAX}}', end='')


def print_header():
    print_aside('')

    for date in dates:
        print(f'{date:>{COLUMN_WIDTH_BASE}}', end='')

    print(f'{TOTAL_COLUMN_CAPTION:>{COLUMN_WIDTH_BASE}}', end='')


def print_body(dictionary, level=0):
    for key in dictionary:
        if key == METADATA_KEY:
            continue

        print_aside(key, level)

        for date in dates:
            print(f'{dictionary[key][METADATA_KEY][MONTHLY_KEY].get(date, 0):>{COLUMN_WIDTH_BASE}.{NUM_OF_DECIMALS}f}',
                  end='')
        print(f'{dictionary[key][METADATA_KEY].get(TOTAL_KEY, 0):>{COLUMN_WIDTH_BASE}.{NUM_OF_DECIMALS}f}', end='')
        new_line()

        if isinstance(dictionary[key], dict):
            print_body(dictionary[key], level + 1)
        else:
            print(dictionary[key])


def new_line():
    print('')


def sorter(k_v):
    if METADATA_KEY in k_v[1]:
        return k_v[1][METADATA_KEY][TOTAL_KEY], k_v[0]
    return 0, 0


def sort(source):
    for key in source:
        if isinstance(source[key], dict) and METADATA_KEY in source[key]:
            source[key] = OrderedDict(sorted(source[key].items(), key=lambda k_v: sorter(k_v), reverse=True))
            sort(source[key])


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

        date = format_date(transaction[DATE_KEY], INPUT_DATE_FORMAT, OUTPUT_DATE_FORMAT)
        dates.add(date)

        subtotal = get_subtotal(transaction)
        targets_to_update = get_nested_paths(storage, transaction, DATA_NESTING_SEQUENCE)
        update_nested_totals(subtotal, date, targets_to_update)

# post-processing
dates = sorted(dates, key=lambda date: datetime.strptime(date, OUTPUT_DATE_FORMAT))
sort(storage)

# print
print_header()
new_line()
print_body(storage)
