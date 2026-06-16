from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from datetime import datetime
from db.database import Base

# 测试用例表
class TestCase(Base):
    __tablename__ = "test_case"
    id = Column(Integer, primary_key=True, index=True)
    case_name = Column(String(200), comment="用例名称")
    browser = Column(String(50), default="chrome")
    steps = Column(Text, comment="步骤json字符串")
    create_time = Column(DateTime, default=datetime.now)

# 执行任务表
class TestTask(Base):
    __tablename__ = "test_task"
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer)
    status = Column(Integer, default=0) # 0待执行 1运行中 2成功 3失败
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    log_path = Column(String(300), nullable=True)
    report_path = Column(String(300), nullable=True)

# 截图表
class TestScreenshot(Base):
    __tablename__ = "test_screenshot"
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer)
    step_index = Column(Integer)
    img_path = Column(String(300))
    create_time = Column(DateTime, default=datetime.now)