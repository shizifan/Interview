p = 'app/services/llm_service.py'
with open(p, 'r', encoding='utf-8') as f:
    c = f.read()

# 1. Update limit description in prompt - add limit_percent
old_limit_desc = '''                    "额外支持 limit 字段：\n"
                    "- limit: 整数，表示返回前N条结果。当用户提到\"前N名\",\"前N个\",\"N人\",\"N条\",\"最多N个\",\"TOP N\",\"前几名\"等数量需求时设置。默认为null表示不限制数量。\n\n"'''

new_limit_desc = '''                    "额外支持 limit 和 limit_percent 字段：\n"
                    "- limit: 整数，表示返回前N条结果。当用户提到\"前N名\",\"前N个\",\"N人\",\"N条\",\"最多N个\",\"TOP N\",\"前几名\"等绝对数量需求时设置。默认为null。\n"
                    "- limit_percent: 整数（1-100），表示返回前X%的结果。当用户提到\"前10%\",\"前50%\",\"前百分之N\",\"前一半(50%)\",\"前三分之一\",\"排名前X%\"等百分比需求时设置。默认为null。\n"
                    "注意：limit 和 limit_percent 不要同时设置，根据用户表述选择其一。\n\n"'''

c = c.replace(old_limit_desc, new_limit_desc)

# 2. Update JSON template in prompt
old_json = '''{"conditions": [{"field": "字段名", "operator": "操作符", "value": "值或数组", "description": "条件中文说明"}], "logic": "AND或OR", "limit": 数量或null, "description": "筛选逻辑的中文解释"}'''

new_json = '''{"conditions": [{"field": "字段名", "operator": "操作符", "value": "值或数组", "description": "条件中文说明"}], "logic": "AND或OR", "limit": 数量或null, "limit_percent": 百分比或null, "description": "筛选逻辑的中文解释"}'''

c = c.replace(f"'{old_json}'", f"'{new_json}'")

# 3. Update return in parse_candidate_filter
old_return = '''            return {
                "conditions": result.get("conditions", []),
                "logic": result.get("logic", "AND"),
                "limit": result.get("limit", None),
                "description": result.get("description", ""),
            }'''

new_return = '''            return {
                "conditions": result.get("conditions", []),
                "logic": result.get("logic", "AND"),
                "limit": result.get("limit", None),
                "limit_percent": result.get("limit_percent", None),
                "description": result.get("description", ""),
            }'''

c = c.replace(old_return, new_return)

with open(p, 'w', encoding='utf-8') as f:
    f.write(c)
print('OK')
