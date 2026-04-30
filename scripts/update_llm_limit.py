p = 'app/services/llm_service.py'
with open(p, 'r', encoding='utf-8') as f:
    c = f.read()

# 1. Update parse_candidate_filter return to include limit
old_return = '''            return {
                "conditions": result.get("conditions", []),
                "logic": result.get("logic", "AND"),
                "description": result.get("description", ""),
            }'''
new_return = '''            return {
                "conditions": result.get("conditions", []),
                "logic": result.get("logic", "AND"),
                "limit": result.get("limit", None),
                "description": result.get("description", ""),
            }'''
c = c.replace(old_return, new_return)

# 2. Update System Prompt - add limit description
old_prompt = '''                    "- in_list: 在列表中\\n\\n"
                    "请严格按照以下JSON格式输出，不要输出任何其他内容：\\n"'''

new_prompt = '''                    "- in_list: 在列表中\\n\\n"
                    "额外支持 limit 字段：\\n"
                    "- limit: 整数，表示返回前N条结果。当用户提到\\"前N名\\",\\"前N个\\",\\"N人\\",\\"N条\\",\\"最多N个\\",\\"TOP N\\",\\"前几名\\"等数量需求时设置。默认为null表示不限制数量。\\n\\n"
                    "请严格按照以下JSON格式输出，不要输出任何其他内容：\\n"'''

c = c.replace(old_prompt, new_prompt)

# 3. Update JSON output template in prompt
old_json_template = '''{"conditions": [{"field": "字段名", "operator": "操作符", "value": "值或数组", "description": "条件中文说明"}], "logic": "AND或OR", "description": "筛选逻辑的中文解释"}'''
new_json_template = '''{"conditions": [{"field": "字段名", "operator": "操作符", "value": "值或数组", "description": "条件中文说明"}], "logic": "AND或OR", "limit": 数量或null, "description": "筛选逻辑的中文解释"}'''

c = c.replace(f"'{old_json_template}'", f"'{new_json_template}'")

# Also need to handle the already-on-second-message pattern (user content)
old_user_msg = 'f"自然语言筛选条件：{natural_language}\\n\\n请输出JSON格式的筛选规则："'
c = c.replace(old_user_msg, old_user_msg.replace('规则"', '规则（含limit字段）"'))

with open(p, 'w', encoding='utf-8') as f:
    f.write(c)
print('OK')
