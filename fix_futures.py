"""Fix SyntaxError in test_futures_market_e2e.py:
assert with two message strings -> merge into one message on the isinstance line.
"""
import re

path = r'd:\testing\testing\futures\test_futures_market_e2e.py'
with open(path, encoding='utf-8') as f:
    content = f.read()

# Pattern: assert isinstance(res, dict)\n    assert res...f"Order", f"Expected dict..."
# Fix: move the second message to the isinstance assert and remove from the res assert
bad_pattern = (
    r'    assert isinstance\(res, dict\)\n'
    r'    (assert res\.get\(\"Status\"\) == \"Success\" or str\(res\.get\(\"Code\"\)\) in \[\"100\", \"200\"\])'
    r', f\"Order failed: \{res\}\"'
    r', f\"Expected dict response, got: \{res\}\"'
)
good_replacement = (
    r'    assert isinstance(res, dict), f"Expected dict response, got: {res}"\n'
    r'    \1, f"Order failed: {res}"'
)

fixed = re.sub(bad_pattern, good_replacement, content)

if fixed == content:
    print("No changes made — pattern not found. Trying line-by-line approach...")
    lines = content.splitlines(keepends=True)
    result = []
    i = 0
    while i < len(lines):
        line = lines[i]
        # Detect the bad assert lines
        if 'assert res.get("Status") == "Success"' in line and ', f"Expected dict response, got: {res}"' in line:
            # Remove the trailing second message
            line = line.replace(', f"Expected dict response, got: {res}"', '')
            # Also fix the preceding isinstance line
            if result and 'assert isinstance(res, dict)' in result[-1]:
                result[-1] = result[-1].rstrip('\n').rstrip('\r') + ', f"Expected dict response, got: {res}"\n'
        result.append(line)
        i += 1
    fixed = ''.join(result)

with open(path, 'w', encoding='utf-8') as f:
    f.write(fixed)

# Verify it parses
import ast
try:
    ast.parse(fixed)
    print("SUCCESS: test_futures_market_e2e.py is now valid Python.")
except SyntaxError as e:
    print(f"STILL HAS SYNTAX ERROR: {e}")
