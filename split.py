import os
import re

TEST_DIR = r"d:\testing\separated_tests"
if not os.path.exists(TEST_DIR):
    os.makedirs(TEST_DIR)

with open(r"d:\testing\test1.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

header = []
tests = {}
current_test = None
test_lines = []

# Collect header
for line in lines:
    if line.startswith("@allure.feature") or line.startswith("@pytest.") or line.startswith("def test_") or line.startswith("@requires_valid_ctid"):
        break
    header.append(line)

# Collect tests
in_test = False
for line in lines:
    if line.startswith("@allure.feature"):
        if current_test:
            tests[current_test] = test_lines
        in_test = True
        test_lines = [line]
        current_test = ""
    elif in_test:
        test_lines.append(line)
        if line.startswith("def test_"):
            current_test = line.split("def ")[1].split("(")[0]
    
if current_test:
    tests[current_test] = test_lines

for test_name, t_lines in tests.items():
    filename = os.path.join(TEST_DIR, f"{test_name}.py")
    with open(filename, "w", encoding="utf-8") as f:
        f.writelines(header)
        f.writelines(t_lines)

print(f"Created {len(tests)} test files in {TEST_DIR}")
