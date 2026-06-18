"""
种子脚本：预置「导入订单」测试用例
运行方式：python seed_import_order.py
"""
import json
from datetime import datetime
from db.database import SessionLocal
from db.models import TestCase

SEED_DATA = {
    "case_name": "导入订单",
    "browser": "chrome",
    "steps": json.dumps([
        {"action": "open_url", "url": "https://mes.nat.zhsvr.com", "desc": "打开 GalaxyERP"},
        {"action": "login", "role": "supply", "desc": "供销账户登录"},
        {"action": "import_order", "desc": "导入订单"},
        {"action": "import_waybill", "desc": "导入面单"},
    ], ensure_ascii=False),
    "create_time": datetime.now(),
}


def seed():
    """导入订单用例 — 幂等写入（已存在则跳过）"""
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
