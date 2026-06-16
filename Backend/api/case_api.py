"""
用例 API — 测试用例的增删改查
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime

from db.database import get_db
from db.models import TestCase

router = APIRouter(prefix="/api/case", tags=["用例管理"])


@router.post("/create")
def create_case(data: dict, db: Session = Depends(get_db)):
    """
    创建测试用例

    Request:
        {
            "case_name": "登录测试",
            "browser": "chrome",
            "steps": "[{\"action\": \"open_url\", ...}]"
        }
    """
    case = TestCase(
        case_name=data["case_name"],
        browser=data.get("browser", "chrome"),
        steps=data.get("steps", "[]"),
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return {"id": case.id, "message": "用例创建成功"}


@router.get("/list")
def list_cases(db: Session = Depends(get_db)):
    """返回全部用例"""
    cases = db.query(TestCase).order_by(TestCase.id.desc()).all()
    return [
        {
            "id": c.id,
            "case_name": c.case_name,
            "browser": c.browser,
            "create_time": str(c.create_time) if c.create_time else None,
        }
        for c in cases
    ]


@router.get("/{case_id}")
def get_case(case_id: int, db: Session = Depends(get_db)):
    """获取单个用例详情（含步骤 JSON）"""
    case = db.query(TestCase).filter(TestCase.id == case_id).first()
    if not case:
        return {"error": "用例不存在"}
    return {
        "id": case.id,
        "case_name": case.case_name,
        "browser": case.browser,
        "steps": case.steps,
        "create_time": str(case.create_time) if case.create_time else None,
    }


@router.put("/{case_id}")
def update_case(case_id: int, data: dict, db: Session = Depends(get_db)):
    """更新用例"""
    case = db.query(TestCase).filter(TestCase.id == case_id).first()
    if not case:
        return {"error": "用例不存在"}
    if "case_name" in data:
        case.case_name = data["case_name"]
    if "browser" in data:
        case.browser = data["browser"]
    if "steps" in data:
        case.steps = data["steps"]
    db.commit()
    return {"message": "更新成功"}


@router.delete("/{case_id}")
def delete_case(case_id: int, db: Session = Depends(get_db)):
    """删除用例"""
    case = db.query(TestCase).filter(TestCase.id == case_id).first()
    if not case:
        return {"error": "用例不存在"}
    db.delete(case)
    db.commit()
    return {"message": "删除成功"}
