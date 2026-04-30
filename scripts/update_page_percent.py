p = 'web/src/pages/hr/IntelligentFilter.tsx'
with open(p, 'r', encoding='utf-8') as f:
    c = f.read()

# Add limit_percent display right after the limit display
old_limit_display = '''                    {msg.rules.limit && (
                      <p style={{ margin: '8px 0 0 0', fontWeight: 600, color: '#1677ff' }}>
                        数量限制：前 {msg.rules.limit} 条
                      </p>
                    )}'''

new_limit_display = '''                    {msg.rules.limit_percent && (
                      <p style={{ margin: '8px 0 0 0', fontWeight: 600, color: '#1677ff' }}>
                        数量限制：前 {msg.rules.limit_percent}%
                      </p>
                    )}
                    {msg.rules.limit && (
                      <p style={{ margin: '8px 0 0 0', fontWeight: 600, color: '#1677ff' }}>
                        数量限制：前 {msg.rules.limit} 条
                      </p>
                    )}'''

c = c.replace(old_limit_display, new_limit_display)

with open(p, 'w', encoding='utf-8') as f:
    f.write(c)
print('OK')
