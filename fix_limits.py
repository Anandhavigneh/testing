import re

path = r'd:\testing\testing\futures\test_futures_limit_e2e.py'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

def replace_params(match):
    prefix = match.group(1)
    suffix = match.group(2)
    return prefix + '''qty="0.002",
        price="76250",
        amount="152.4804",
        order_type="1",
        order_side="0",
        leverage="3"''' + suffix

pattern1 = r'(test_futures_limit_long_valid[\s\S]*?symbol=\"BTC/USDT\",\n\s*)qty=[\s\S]*?leverage=\"[^\"]*\"([\s\S]*?assert)'
text = re.sub(pattern1, replace_params, text)

# For test_futures_limit_long_with_tpsl
pattern_tpsl = r'(test_futures_limit_long_with_tpsl[\s\S]*?symbol=\"BTC/USDT\",\n\s*)qty=[\s\S]*?leverage=\"[^\"]*\"([\s\S]*?tp_price)'
def replace_params_tpsl(match):
    prefix = match.group(1)
    suffix = match.group(2)
    return prefix + '''qty="0.002",
        price="76250",
        amount="152.4804",
        order_type="1",
        order_side="0",
        leverage="3",''' + suffix
text = re.sub(pattern_tpsl, replace_params_tpsl, text)


def replace_params_short(match):
    prefix = match.group(1)
    suffix = match.group(2)
    return prefix + '''qty="0.002",
        price="90000",
        amount="180",
        order_type="1",
        order_side="1",
        leverage="3"''' + suffix

pattern2 = r'(test_futures_limit_short_valid[\s\S]*?symbol=\"BTC/USDT\",\n\s*)qty=[\s\S]*?leverage=\"[^\"]*\"([\s\S]*?assert)'
text = re.sub(pattern2, replace_params_short, text)

def replace_cancel(match):
    prefix = match.group(1)
    suffix = match.group(2)
    return prefix + '''qty="0.002",
        price="76250",
        amount="152.4804",
        order_type="1",
        order_side="0",
        leverage="3"''' + suffix

pattern3 = r'(test_futures_limit_cancel_order[\s\S]*?symbol=\"BTC/USDT\",\n\s*)qty=[\s\S]*?leverage=\"[^\"]*\"([\s\S]*?if)'
text = re.sub(pattern3, replace_cancel, text)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
print('Updated tests!')
