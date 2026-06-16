```
auto-test-server/
├── main.py               # FastAPI入口 
├── api/                  # 接口模块 
│   ├── case_api.py       # 用例CRUD 
│   ├── task_api.py       # 执行任务下发 
│   └── report_api.py    # 报告查询 
├── core/ 
│   ├── selenium_engine.py # Selenium封装执行核心 
│   └── browser_config.py # 浏览器初始化 
├── tasks/                # Celery异步任务 
│   └── run_test_task.py 
├── db/ 
│   ├── models.py         # 数据库表模型 
│   └── database.py       # MySQL连接 
├── static/               # 截图、报告静态资源 
└── requirements.txt
```

