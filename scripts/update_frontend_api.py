p = 'web/src/api/hr.ts'
with open(p, 'r', encoding='utf-8') as f:
    c = f.read()

# 1. Add limit to FilterRule interface
old_filter = '''export interface FilterRule {
  conditions: Array<{
    field: string;
    operator: string;
    value: string | number | string[];
    description: string;
  }>;
  logic: string;
  description: string;
}'''

new_filter = '''export interface FilterRule {
  conditions: Array<{
    field: string;
    operator: string;
    value: string | number | string[];
    description: string;
  }>;
  logic: string;
  limit?: number;
  description: string;
}'''

c = c.replace(old_filter, new_filter)

# 2. Add limit to ParseFilterResponse
old_parse = '''export interface ParseFilterResponse {
  conditions: FilterRule['conditions'];
  logic: string;
  description: string;
  error?: string;
}'''

new_parse = '''export interface ParseFilterResponse {
  conditions: FilterRule['conditions'];
  logic: string;
  limit?: number;
  description: string;
  error?: string;
}'''

c = c.replace(old_parse, new_parse)

with open(p, 'w', encoding='utf-8') as f:
    f.write(c)
print('OK')
