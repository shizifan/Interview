p = 'web/src/api/hr.ts'
with open(p, 'r', encoding='utf-8') as f:
    c = f.read()

# Add limit_percent to FilterRule
old_filter = '''  logic: string;
  limit?: number;
  description: string;'''

new_filter = '''  logic: string;
  limit?: number;
  limit_percent?: number;
  description: string;'''

c = c.replace(old_filter, new_filter)

# Add limit_percent to ParseFilterResponse
old_parse = '''  logic: string;
  limit?: number;
  description: string;
  error?: string;'''

new_parse = '''  logic: string;
  limit?: number;
  limit_percent?: number;
  description: string;
  error?: string;'''

c = c.replace(old_parse, new_parse)

with open(p, 'w', encoding='utf-8') as f:
    f.write(c)
print('OK')
