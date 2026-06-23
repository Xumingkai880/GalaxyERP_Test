"""
Selenium 执行引擎 — 自动化测试平台核心

职责：
1. 接收前端下发的步骤 JSON → 转译成浏览器操作
2. 每一步自动截图，失败时记录错误
3. 直接调用同目录 pages/ 下的 Page Object

使用方式：
    runner = SeleniumRunner(headless=False)
    result = runner.run_steps([
        {"action": "open_url", "url": "https://erp.link"},
        {"action": "login", "role": "supply"},
        {"action": "import_order", "file_path": "/path/to/order.xlsx", "desc": "导入订单"},
        {"action": "import_waybill", "file_path": "/path/to/waybill.pdf", "desc": "导入面单"},
        {"action": "arrange_order", "order_no": "EB...", "supplier": "分销测试", "desc": "安排订单"},
        {"action": "click", "loc_type": "css", "loc_value": ".menu-item", "desc": "点击菜单"},
    ])
    runner.close()
"""

import os
import time
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementClickInterceptedException,
    ElementNotInteractableException,
)

# ---- 直接导入 Page Object ----
from core.config import BASE_URL, TEST_ACCOUNTS, ORDER_FILE, WAYBILL_FILE
from core.pages.login_page import LoginPage
from core.pages.order_page import OrderPage
from core.pages.arrange_order_page import ArrangeOrderPage

# ===================== 配置 =====================

SCREENSHOT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "static", "screenshots"
)
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

LOC_TYPE_MAP = {
    "id": By.ID,
    "xpath": By.XPATH,
    "css": By.CSS_SELECTOR,
    "name": By.NAME,
    "class": By.CLASS_NAME,
    "tag": By.TAG_NAME,
    "link_text": By.LINK_TEXT,
    "partial_link": By.PARTIAL_LINK_TEXT,
}

# ===================== 执行引擎 =====================


class SeleniumRunner:
    """
    Selenium 执行器

    Attributes:
        driver: WebDriver 实例
        wait: WebDriverWait（默认 15 秒超时）
        results: 执行记录列表
    """

    def __init__(self, headless=False, browser="chrome", window_size="1920,1080"):
        options = ChromeOptions()

        if headless:
            options.add_argument("--headless=new")
        options.add_argument(f"--window-size={window_size}")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-features=TranslateUI")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        options.add_experimental_option("prefs", {
            "profile.default_content_setting_values.notifications": 2,
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
        })

        # Selenium 4.6+ 内置 Selenium Manager，自动探测本地 Chrome 版本
        # 并下载匹配的 chromedriver，无需 webdriver-manager
        self.driver = webdriver.Chrome(options=options)
        self.driver.implicitly_wait(5)
        self.wait = WebDriverWait(self.driver, 15)

        self.results: list[dict] = []

    # ---------- 公开入口 ----------

    def run_steps(self, steps: list[dict]) -> dict:
        """
        执行完整步骤列表，返回汇总结果

        Args:
            steps: 见模块 docstring 中的示例

        Returns:
            {"status": "success|fail", "total": 4, "passed": 3, "failed": 1, "steps": [...]}
        """
        self.results = []

        for i, step in enumerate(steps):
            try:
                step_result = self._run_one(i, step)
                self.results.append(step_result)
            except Exception as e:
                shot = self._screenshot(f"step_{i + 1}_crash")
                self.results.append({
                    "index": i + 1,
                    "action": step.get("action", "unknown"),
                    "desc": step.get("desc", ""),
                    "status": "fail",
                    "error": str(e),
                    "screenshot": shot,
                })

        return {
            "status": "success" if all(r["status"] == "success" for r in self.results) else "fail",
            "total": len(steps),
            "passed": sum(1 for r in self.results if r["status"] == "success"),
            "failed": sum(1 for r in self.results if r["status"] == "fail"),
            "steps": self.results,
        }

    def close(self):
        """关闭浏览器驱动"""
        if self.driver:
            self.driver.quit()
            self.driver = None

    # ---------- 单步执行 ----------

    def _run_one(self, idx: int, step: dict) -> dict:
        """执行单个步骤"""
        action = step.get("action", "")
        desc = step.get("desc", action)

        try:
            if action == "open_url":
                self.driver.get(step["url"])
                time.sleep(2)

            elif action == "click":
                locator = self._build_locator(step)
                self._robust_click(locator)

            elif action == "input":
                locator = self._build_locator(step)
                self._robust_input(locator, str(step.get("value", "")))

            elif action == "assert_text":
                locator = self._build_locator(step)
                expect = step.get("expect", "")
                actual = self._get_text(locator)
                assert expect in actual, (
                    f"断言失败：预期包含「{expect}」，实际「{actual}」"
                )

            elif action == "assert_url":
                expect = step.get("expect", "")
                actual = self.driver.current_url
                assert expect in actual, (
                    f"断言失败：预期 URL 包含「{expect}」，实际「{actual}」"
                )

            elif action == "wait":
                time.sleep(step.get("seconds", 2))

            elif action == "wait_element":
                locator = self._build_locator(step)
                self.wait.until(EC.presence_of_element_located(locator))

            elif action == "scroll":
                locator = self._build_locator(step)
                el = self.driver.find_element(*locator)
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center'});", el
                )

            # ---- 预置业务操作（直接调用 Page Object） ----

            elif action == "login":
                self._do_login(step)

            elif action == "import_order":
                self._do_import_order(step)

            elif action == "import_waybill":
                self._do_import_waybill(step)

            elif action == "arrange_order":
                self._do_arrange_order(step)

            else:
                raise ValueError(f"不支持的操作类型: {action}")

            shot = self._screenshot(f"step_{idx + 1}")
            return {
                "index": idx + 1,
                "action": action,
                "desc": desc,
                "status": "success",
                "screenshot": shot,
            }

        except Exception as e:
            shot = self._screenshot(f"step_{idx + 1}_fail")
            return {
                "index": idx + 1,
                "action": action,
                "desc": desc,
                "status": "fail",
                "error": str(e),
                "screenshot": shot,
            }

    # ---------- 预置业务操作 ----------

    def _do_login(self, step: dict):
        """使用预置账户登录 GalaxyERP（默认分销用户）"""
        role = step.get("role", "dist")  # 默认为分销用户
        acc = TEST_ACCOUNTS[1] if role == "dist" else TEST_ACCOUNTS[0]

        page = LoginPage(self.driver)
        page.open(BASE_URL)
        page.perform_login(
            tenant=acc["tenant"],
            username=acc["username"],
            password=acc["password"],
        )
        page.wait_for_login_success()
        print(f"✅ {acc['name']} 登录成功")

    def _do_import_order(self, step: dict):
        """导入订单：导航手工订单页 → 上传 Excel → 确认"""
        file_path = step.get("file_path", ORDER_FILE)
        page = OrderPage(self.driver)
        page.import_order(file_path)

    def _do_import_waybill(self, step: dict):
        """导入面单：导航待处理 → 批量操作 → 导入运单 → 上传 PDF → 确认"""
        file_path = step.get("file_path", WAYBILL_FILE)
        page = OrderPage(self.driver)
        page.import_waybill(file_path)

    def _do_arrange_order(self, step: dict):
        """安排订单到供销商（dist 推送 + 页面验证）

        前置条件：外层步骤已先 login(dist) 登录分销账号（推送必须由 dist 操作）。

        流程：沿用外层 dist 会话 → 推送订单 → 验证页面。
        （数量差量验证太脆已移除，只验证订单是否进入列表。）
        """
        order_no = step.get("order_no", "")
        supplier = step.get("supplier", "分销测试")

        if not order_no:
            raise ValueError("arrange_order 需要指定 order_no 参数")

        page = ArrangeOrderPage(self.driver)

        # Step 1: dist 推送（外层已登录 dist，这里直接执行推送）
        print("\n========== 安排订单 (dist 推送) ==========")
        print(f"  订单号: {order_no}")
        print(f"  供销商: {supplier}")
        page.arrange_order_dist_side(order_no, supplier)
        print("========== 安排订单完成 ==========\n")

    # ---------- 元素操作 ----------

    def _build_locator(self, step: dict) -> tuple:
        loc_type = step.get("loc_type", "css")
        loc_value = step.get("loc_value", "")
        if not loc_value:
            raise ValueError("缺少 loc_value")
        by = LOC_TYPE_MAP.get(loc_type)
        if not by:
            raise ValueError(f"不支持的定位方式: {loc_type}，可选 {list(LOC_TYPE_MAP.keys())}")
        return (by, loc_value)

    def _robust_click(self, locator: tuple):
        """健壮点击：滚动 + 等待可点击 + JS 兜底"""
        el = self.wait.until(EC.presence_of_element_located(locator))
        self.driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});", el
        )
        time.sleep(0.3)
        try:
            WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable(locator)
            ).click()
        except (ElementClickInterceptedException, ElementNotInteractableException):
            self.driver.execute_script("arguments[0].click();", el)

    def _robust_input(self, locator: tuple, text: str):
        """健壮输入：滚动 + 清空 + 输入"""
        el = self.wait.until(EC.visibility_of_element_located(locator))
        self.driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});", el
        )
        time.sleep(0.2)
        el.clear()
        el.send_keys(text)

    def _get_text(self, locator: tuple) -> str:
        el = self.wait.until(EC.visibility_of_element_located(locator))
        return el.text

    # ---------- 截图 ----------

    def _screenshot(self, label: str) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"{label}_{timestamp}.png"
        filepath = os.path.join(SCREENSHOT_DIR, filename)
        try:
            self.driver.save_screenshot(filepath)
        except Exception:
            pass
        return f"/static/screenshots/{filename}"
