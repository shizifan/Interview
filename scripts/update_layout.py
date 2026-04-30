p = 'web/src/layouts/HRLayout.tsx'
with open(p, 'r', encoding='utf-8') as f:
    c = f.read()

# Add RobotOutlined import
c = c.replace(
    '  LogoutOutlined,\n} from',
    '  LogoutOutlined,\n  RobotOutlined,\n} from'
)

# Add menu item between candidates and interviews
c = c.replace(
    'label: \'候选人管理\' },\n  { key: \'/hr/interviews\'',
    'label: \'候选人管理\' },\n  { key: \'/hr/intelligent-filter\', icon: <RobotOutlined />, label: \'智能筛选\' },\n  { key: \'/hr/interviews\''
)

with open(p, 'w', encoding='utf-8') as f:
    f.write(c)
print('OK')
