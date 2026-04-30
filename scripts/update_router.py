p = 'web/src/router.tsx'
with open(p, 'r', encoding='utf-8') as f:
    c = f.read()

# Add import
c = c.replace(
    'import HRSettings from \'@/pages/hr/Settings\';',
    'import HRIntelligentFilter from \'@/pages/hr/IntelligentFilter\';\nimport HRSettings from \'@/pages/hr/Settings\';'
)

# Add route
c = c.replace(
    '{ path: \'settings\', element: <HRSettings /> }',
    '{ path: \'settings\', element: <HRSettings /> },\n      { path: \'intelligent-filter\', element: <HRIntelligentFilter /> }'
)

with open(p, 'w', encoding='utf-8') as f:
    f.write(c)
print('OK')
