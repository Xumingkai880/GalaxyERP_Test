"""
登录页面对象 (Login Page)
功能：封装登录页面的所有 UI 操作
- 打开登录页面
- 填写登录表单（租户、用户名、密码）
- 执行登录
- 验证登录成功
"""
from selenium.webdriver.common.by import By
from .base_page import BasePage
from selenium.webdriver.support.ui import WebDriverWait

class LoginPage(BasePage):
    # 定位器集中管理，如果页面改版，只改这里
    LOCATORS = {
        "tenant_tab": (By.ID, "tab-tenantId"), # 登录方式选择标签
        "tenant_input": (By.CSS_SELECTOR, '[placeholder="Tenant"]'), # 租户输入框
        "username_input": (By.CSS_SELECTOR, '[placeholder="Username"]'), # 用户名输入框
        "password_input": (By.CSS_SELECTOR, '[placeholder="Password"]'), # 密码输入框
        "login_btn": (By.CLASS_NAME, "login-btn") # 登录按钮
    }

    def open(self, url: str):
        """打开登录页面
        
        Args:
            url: 登录页面的 URL 地址
        """
        self.driver.get(url)

    def perform_login(self, tenant: str, username: str, password: str):
        """执行完整的登录操作流程
        
        操作步骤：
        1. 点击租户标签（切换登录方式）
        2. 填写租户 ID
        3. 填写用户名
        4. 填写密码
        5. 点击登录按钮
        
        Args:
            tenant: 租户 ID
            username: 用户名
            password: 密码
        """
        # 1. 点击租户标签
        self.find_and_click(self.LOCATORS["tenant_tab"])

        # 2. 填写表单
        self.find_and_input(self.LOCATORS["tenant_input"], tenant)
        self.find_and_input(self.LOCATORS["username_input"], username)
        self.find_and_input(self.LOCATORS["password_input"], password)

        # 3. 点击登录
        self.find_and_click(self.LOCATORS["login_btn"])

    def wait_for_login_success(self, timeout: int = 10):
        """等待登录成功（URL 不再包含 login）
        
        Args:
            timeout: 等待超时时间（秒），默认 10 秒
        
        判断标准：当前 URL 中不再包含 "login" 字符串
        """
        WebDriverWait(self.driver, timeout).until(
            lambda d: "login" not in d.current_url.lower()
        )
