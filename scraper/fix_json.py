import json

file_path = r'C:\Users\ENIGMA\AppData\Local\Temp\opencode\educational-portal\assets\content\data.json'

with open(file_path, 'r', encoding='utf-8-sig') as f:
    content = f.read()

# Remove the last incomplete entry and its trailing comma
last_open = content.rfind('{')
last_comma = content.rfind(',', 0, last_open)

if last_comma > 0:
    truncated = content[:last_comma]
else:
    truncated = content[:last_open]

truncated = truncated.rstrip()

# Track brackets outside strings using a stack
stack = []
i = 0
in_str = False
esc = False

while i < len(truncated):
    ch = truncated[i]
    if esc:
        esc = False
        i += 1
        continue
    if ch == '\\':
        esc = True
        i += 1
        continue
    if ch == '"':
        in_str = not in_str
        i += 1
        continue
    if not in_str:
        if ch == '{':
            stack.append('}')
        elif ch == '[':
            stack.append(']')
        elif ch == '}':
            if stack and stack[-1] == '}':
                stack.pop()
        elif ch == ']':
            if stack and stack[-1] == ']':
                stack.pop()
    i += 1

closing = ''.join(reversed(stack))
fixed = truncated + '\n' + closing

try:
    data = json.loads(fixed)
    with open(file_path, 'w', encoding='utf-8-sig') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    total = sum(len(c["files"]) for ld in data.values() for y in ld["years"].values() for s in y["subjects"].values() for c in s["categories"].values())
    with_urls = sum(1 for ld in data.values() for y in ld["years"].values() for s in y["subjects"].values() for c in s["categories"].values() for f in c["files"] if f.get("direct_url") and f["direct_url"] != "_unavailable")
    pending = sum(1 for ld in data.values() for y in ld["years"].values() for s in y["subjects"].values() for c in s["categories"].values() for f in c["files"] if not f.get("direct_url"))
    print(f'SUCCESS! Total: {total}, With URLs: {with_urls}, Pending: {pending}')
except json.JSONDecodeError as e:
    print(f'Failed: line {e.lineno}, col {e.colno}: {e.msg}')
    print(f'Closing: {closing}')
    # Show context
    lines = fixed[:e.pos].split('\n')
    for li in range(max(0, len(lines)-5), len(lines)):
        print(f'  L{li+1}: ...{lines[li][-100:]}')
