"""
种子脚本：预置「安排生产」用例到数据库
用例步骤: open_url → login(supply) → arrange_production
注意：安排生产由供销账号操作，所以外层必须先 login(supply)。
      ProductionArrangePage 内部沿用外层 supply 会话执行导航+搜索+勾选+Production Arrange。
"""
import json
from datetime import datetime
from db.database import SessionLocal
from db.models import TestCase

SEED_DATA = {
    "case_name": "安排生产",
    "browser": "chrome",
    "steps": json.dumps([
        {"action": "open_url", "url": "https://mes.nat.zhsvr.com", "desc": "打开 GalaxyERP"},
        {"action": "login", "role": "supply", "desc": "登录供销账号"},
        {"action": "arrange_production", "order_no": "", "desc": "安排生产"},
    ], ensure_ascii=False),
    "create_time": datetime.now(),
}


def seed():
    db = SessionLocal()
    try:
        existing = db.query(TestCase).filter(TestCase.case_name == SEED_DATA["case_name"]).first()
        if existing:
            # 已存在 → 更新 steps（避免 seed 改了但 DB 还是旧数据）
            existing.steps = SEED_DATA["steps"]
            existing.browser = SEED_DATA["browser"]
            db.commit()
            db.refresh(existing)
            print(f"[UPDATE] case_name={SEED_DATA['case_name']} (id={existing.id}) steps 已更新")
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
