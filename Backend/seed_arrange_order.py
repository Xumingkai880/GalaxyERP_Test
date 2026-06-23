"""
种子脚本：预置「安排订单」用例到数据库
用例 id=7，步骤: open_url → login(dist) → arrange_order
注意：推送订单由分销账号操作，所以外层必须先登录 dist。
      _do_arrange_order 内部直接沿用外层 dist 会话推送（不再做 supply 验证）。
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.database import get_connection


def seed():
    steps = [
        {"action": "open_url", "desc": "打开 GalaxyERP"},
        {"action": "login", "role": "dist", "desc": "登录分销账号"},
        {"action": "arrange_order", "order_no": "", "supplier": "分销测试", "desc": "安排订单到供销商"},
    ]

    case = {
        "id": 7,
        "name": "安排订单",
        "category": "POD",
        "steps": json.dumps(steps, ensure_ascii=False),
        "enabled": 1,
    }

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """INSERT INTO test_case (id, name, category, steps, enabled)
           VALUES (%s, %s, %s, %s, %s)
           ON DUPLICATE KEY UPDATE name=VALUES(name), steps=VALUES(steps), enabled=VALUES(enabled)""",
        (case["id"], case["name"], case["category"], case["steps"], case["enabled"]),
    )

    conn.commit()
    cursor.close()
    conn.close()
    print(f"✅ 种子数据已写入: {case['name']} (id={case['id']})")


if __name__ == "__main__":
    seed()
