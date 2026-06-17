"""
种子脚本：写入「导入订单」测试用例到数据库
运行方式：
    cd D:/xmk/GalaxyERP_Test/Backend
    .venv\Scripts\python.exe seed_import_order.py
"""
import json
import sys
sys.path.insert(0, ".")

from db.database import SessionLocal
from db.models import TestCase

ORDER_FILE = r"D:/xmk/GalaxyERP_Test/Backend/files/导出订单包裹-20260325135831.xlsx"
WAYBILL_FILE = r"D:/xmk/GalaxyERP_Test/Backend/files/面单(1).pdf"

steps = [
    {"action": "open_url", "url": "https://mes.nat.zhsvr.com", "desc": "打开 GalaxyERP"},
    {"action": "login", "role": "dist", "desc": "分销用户登录"},
    {"action": "import_order", "file_path": ORDER_FILE, "desc": "导入订单"},
    {"action": "import_waybill", "file_path": WAYBILL_FILE, "desc": "导入面单"},
]

db = SessionLocal()
try:
    existing = db.query(TestCase).filter(TestCase.case_name == "导入订单").first()
    if existing:
        print(f"[SKIP] case '导入订单' already exists (id={existing.id})")
    else:
        case = TestCase(
            case_name="导入订单",
            browser="chrome",
            steps=json.dumps(steps, ensure_ascii=False),
        )
        db.add(case)
        db.commit()
        db.refresh(case)
        print(f"[OK] case '导入订单' created (id={case.id})")
finally:
    db.close()
