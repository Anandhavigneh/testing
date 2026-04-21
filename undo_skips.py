import re
import glob

# Remove @requires_user_details
wallet_file = r'd:\testing\testing\wallet\test_asset_transfer_bidirectional_e2e.py'
with open(wallet_file, 'r', encoding='utf-8') as f:
    content = f.read()

# remove definition of requires_user_details
remove_pattern = re.compile(r'def _user_details_available\(\) -> bool:.*?requires_user_details = pytest\.mark\.skipif\([^)]+\)\n+', re.DOTALL)
content = remove_pattern.sub('', content)

# remove usages
content = content.replace('@requires_user_details\n', '')

# remove the xfail from the zero amount test
xfail_pattern = re.compile(r'@pytest\.mark\.xfail\([\s\S]*?strict=False,?\n\)\n')
content = xfail_pattern.sub('', content)

with open(wallet_file, 'w', encoding='utf-8') as f:
    f.write(content)

files = glob.glob(r'd:\testing\testing\futures\*.py') + glob.glob(r'd:\testing\testing\spot\*.py')
for path in files:
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    new_content = xfail_pattern.sub('', content)
    if new_content != content:
        print(f'Removed xfails from {path}')
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_content)
print('Done!')
