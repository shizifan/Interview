p = 'web/src/pages/hr/Candidates.tsx'
with open(p, 'r', encoding='utf-8') as f:
    c = f.read()

# Remove the smart filter modal imports that are no longer needed
# Keep RobotOutlined for the button
# Remove unused filter-related state and functions

# Step 1: Remove unused imports (Spin, Alert - keep if used elsewhere)
# Actually let's just replace the button to navigate instead of opening modal

# Change openFilterModal function and button
old_func = '''  const openFilterModal = () => {
    setFilterModalOpen(true);
    setFilterInput('');
    setFilterRules(null);
    setFilterError(null);
    setFilterResult(null);
  };'''
new_func = '''  const goToFilter = () => {
    navigate('/hr/intelligent-filter');
  };'''

c = c.replace(old_func, new_func)

# Change button onClick
c = c.replace('onClick={openFilterModal}', 'onClick={goToFilter}')

# Remove filter state variables (filterModalOpen, filterInput, filterRules, filterLoading, filterError, filterResult)
old_states = '''  const [filterModalOpen, setFilterModalOpen] = useState(false);
  const [filterInput, setFilterInput] = useState('');
  const [filterRules, setFilterRules] = useState<FilterRule | null>(null);
  const [filterLoading, setFilterLoading] = useState(false);
  const [filterError, setFilterError] = useState<string | null>(null);
  const [filterResult, setFilterResult] = useState<Candidate[] | null>(null);'''
c = c.replace(old_states, '')

# Remove filter handler functions (parse, execute, close)
old_parse = '''
  const handleParseFilter = async () => {
    if (!filterInput.trim()) return;
    setFilterLoading(true);
    setFilterError(null);
    setFilterRules(null);
    try {
      const result = await hrApi.parseFilterRule(filterInput);
      if (result.error) {
        setFilterError(result.error);
      } else {
        setFilterRules(result as FilterRule);
      }
    } catch (err) {
      setFilterError(err instanceof Error ? err.message : '解析失败');
    } finally {
      setFilterLoading(false);
    }
  };

  const handleExecuteFilter = async () => {
    if (!filterRules) return;
    setFilterLoading(true);
    try {
      const result = await hrApi.executeIntelligentFilter(filterRules);
      setFilterResult(result.items);
    } catch (err) {
      message.error(err instanceof Error ? err.message : '执行筛选失败');
    } finally {
      setFilterLoading(false);
    }
  };

  const closeFilterModal = () => {
    setFilterModalOpen(false);
    setFilterInput('');
    setFilterRules(null);
    setFilterError(null);
    setFilterResult(null);
    load(1);
  };'''
c = c.replace(old_parse, '')

# Remove the filter modal JSX (from Modal title="智能筛选候选人" to the closing </Modal>)
old_modal_start = '''      <Modal
        title="智能筛选候选人"
        open={filterModalOpen}
        onCancel={closeFilterModal}
        width={600}'''

# Find the end of the modal
idx = c.find(old_modal_start)
if idx >= 0:
    # Find the matching closing </Modal> (the next </Modal> after this one)
    # Actually there are two modals, need to find the right one
    end_idx = c.find('</Modal>', idx)
    if end_idx >= 0:
        end_idx = c.find('</Modal>', end_idx + 8)  # Skip first </Modal>
        if end_idx >= 0:
            c = c[:idx] + c[end_idx + 8:]

# Remove unused imports that are now dead
c = c.replace('''
  const openFilterModal = () => {
    navigate('/hr/intelligent-filter');
  };
''', '''

  const goToFilter = () => {
    navigate('/hr/intelligent-filter');
  };
''')

with open(p, 'w', encoding='utf-8') as f:
    f.write(c)
print('OK')
