p = 'web/src/pages/hr/IntelligentFilter.tsx'
with open(p, 'r', encoding='utf-8') as f:
    c = f.read()

# 1. Add limit display after conditions list, before the closing of the rule box
old_close = '''                    </ul>
                  </div>
                )}
              </div>
              {hasRules && (
                <div style={{ marginTop: 8 }}>'''

new_close = '''                    </ul>
                    {msg.rules.limit && (
                      <p style={{ margin: '8px 0 0 0', fontWeight: 600, color: '#1677ff' }}>
                        数量限制：前 {msg.rules.limit} 条
                      </p>
                    )}
                  </div>
                )}
              </div>
              {hasRules && (
                <div style={{ marginTop: 8 }}>'''

c = c.replace(old_close, new_close)

with open(p, 'w', encoding='utf-8') as f:
    f.write(c)
print('OK')
