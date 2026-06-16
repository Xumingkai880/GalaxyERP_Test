"""GalaxyERP 测试配置"""

import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("BASE_URL", "https://mes.nat.zhsvr.com")

# 超时配置
EXPLICIT_WAIT = 15  # 显式等待（秒），base_page.py 默认使用此值

TEST_ACCOUNTS = [
    {
        "name": "供销账户",
        "tenant": os.getenv("SUPPLY_TENANT", "202348"),
        "username": os.getenv("SUPPLY_USERNAME", "admin"),
        "password": os.getenv("SUPPLY_PASSWORD", "admin123"),
    },
    {
        "name": "分销账户",
        "tenant": os.getenv("DIST_TENANT", "123881"),
        "username": os.getenv("DIST_USERNAME", "admin"),
        "password": os.getenv("DIST_PASSWORD", "admin123"),
    },
]
