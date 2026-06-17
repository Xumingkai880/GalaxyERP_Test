"""
任务 API — 接收前端请求，驱动 Selenium 执行
"""

import json
import threading
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db.database import get_db
from db.models import TestTask, TestScreenshot, TestCase
from core.selenium_engine import SeleniumRunner

router = APIRouter(prefix="/api/task", tags=["任务管理"])


@router.post("/run")
def run_task(data: dict, db: Session = Depends(get_db)):
    """
    执行测试任务

    Request:
        {
            "case_id": 1,
            "steps": [
                {"action": "open_url", "url": "https://..."},
                {"action": "login", "role": "supply"},
                {"action": "click", "loc_type": "css", "loc_value": ".btn", "desc": "点击按钮"}
            ]
        }

    Response:
        {"task_id": 123, "message": "任务已创建，正在执行中..."}
    """
    case_id = data.get("case_id", 0)
    steps = data.get("steps", [])

    # 1. 入库：创建任务记录（状态=运行中）
    task = TestTask(
        case_id=case_id,
        status=1,  # 1 = 运行中
        start_time=datetime.now(),
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    task_id = task.id

    # 2. 异步执行 Selenium（不阻塞接口响应）
    threading.Thread(
        target=_execute_task, args=(task_id, steps), daemon=True
    ).start()

    return {"task_id": task_id, "message": "任务已创建，正在执行中..."}


@router.get("/{task_id}")
def get_task_detail(task_id: int, db: Session = Depends(get_db)):
    """
    查询任务详情（含截图列表）

    Response:
        {
            "task": {...},
            "screenshots": [{"step_index": 1, "img_path": "/static/screenshots/..."}]
        }
    """
    task = db.query(TestTask).filter(TestTask.id == task_id).first()
    if not task:
        return {"error": "任务不存在"}

    screenshots = (
        db.query(TestScreenshot)
        .filter(TestScreenshot.task_id == task_id)
        .order_by(TestScreenshot.step_index)
        .all()
    )

    return {
        "id": task.id,
        "case_id": task.case_id,
        "status": task.status,
        "start_time": str(task.start_time) if task.start_time else None,
        "end_time": str(task.end_time) if task.end_time else None,
        "result_log": task.report_path or task.log_path or "",
        "screenshots": [
            {"step_index": s.step_index, "screenshot_path": s.img_path}
            for s in screenshots
        ],
    }


@router.get("/list/all")
def list_tasks(db: Session = Depends(get_db)):
    """返回最近 50 条任务（含用例名，供前端分组用）"""
    tasks = (
        db.query(TestTask)
        .order_by(TestTask.id.desc())
        .limit(50)
        .all()
    )

    # 批量查用例名，避免 N+1
    case_ids = {t.case_id for t in tasks}
    case_map = {}
    if case_ids:
        cases = db.query(TestCase).filter(TestCase.id.in_(case_ids)).all()
        case_map = {c.id: c.case_name for c in cases}

    return {
        "tasks": [
            {
                "id": t.id,
                "case_id": t.case_id,
                "case_name": case_map.get(t.case_id, f"用例#{t.case_id}"),
                "status": t.status,
                "start_time": str(t.start_time) if t.start_time else None,
                "end_time": str(t.end_time) if t.end_time else None,
            }
            for t in tasks
        ]
    }


@router.delete("/clear")
def clear_all_tasks(db: Session = Depends(get_db)):
    """一键清空所有任务记录及截图（保留用例）"""
    deleted_screenshots = db.query(TestScreenshot).delete()
    deleted_tasks = db.query(TestTask).delete()
    db.commit()
    return {"message": "已清空", "deleted_tasks": deleted_tasks, "deleted_screenshots": deleted_screenshots}


# ==================== 内部执行逻辑 ====================


def _execute_task(task_id: int, steps: list):
    """
    后台线程：执行 Selenium、更新任务状态、存截图记录
    """
    from db.database import SessionLocal

    db = SessionLocal()
    runner = None

    try:
        # 1. 运行 Selenium
        runner = SeleniumRunner(headless=False)
        result = runner.run_steps(steps)

        # 2. 写入截图记录
        for s in result["steps"]:
            if s.get("screenshot"):
                shot = TestScreenshot(
                    task_id=task_id,
                    step_index=s["index"],
                    img_path=s["screenshot"],
                )
                db.add(shot)

        # 3. 更新任务状态
        task = db.query(TestTask).filter(TestTask.id == task_id).first()
        if task:
            task.status = 2 if result["status"] == "success" else 3  # 2=成功 3=失败
            task.end_time = datetime.now()
            task.report_path = json.dumps(result, ensure_ascii=False)

        db.commit()

    except Exception as e:
        task = db.query(TestTask).filter(TestTask.id == task_id).first()
        if task:
            task.status = 3
            task.end_time = datetime.now()
            task.log_path = str(e)[:5000]  # 截断，避免极端情况超长
        db.commit()

    finally:
        if runner:
            runner.close()
        db.close()
