"""
种子脚本：预置「安排订单」用例到数据库
用例步骤: open_url → login(dist) → arrange_order
注意：推送订单由分销账号操作，所以外层必须先 login(dist)。
      _do_arrange_order 内部沿用外层 dist 会话执行推送。
"""
import json
from datetime import datetime
from db.database import SessionLocal
from db.models import TestCase

SEED_DATA = {
    "case_name": "安排订单",
    "browser": "chrome",
    "steps": json.dumps([
        {"action": "open_url", "desc": "打开 GalaxyERP"},
        {"action": "login", "role": "dist", "desc": "登录分销账号"},
        {"action": "arrange_order", "order_no": "", "supplier": "分销测试", "desc": "安排订单到供销商"},
    ], ensure_ascii=False),
    "create_time": datetime.now(),
}


def seed():
    db = SessionLocal()
    try:
        existing = db.query(TestCase).filter(TestCase.case_name == SEED_DATA["case_name"]).first()
        if existing:
            print(f"[SKIP] case_name={SEED_DATA['case_name']} already exists (id={existing.id})")
            return
        record = TestCase(**SEED_DATA)
        db.add(record)
        db.commit()
        db.refresh(record)
        print(f"[OK] case_name={SEED_DATA['case_name']} created (id={record.id})")
    except Exception as e:
        db.rollback()
        print(f"[FAIL] {e}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
