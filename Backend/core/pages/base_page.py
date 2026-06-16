"""
基础页面对象类 (Base Page)
功能：提供所有页面通用的 Selenium 操作方法
- 元素查找和点击
- 文本输入
- 元素可见性检查
- 滚动到视图
- JavaScript 点击

所有具体的页面对象类都继承自这个基类
"""
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webdriver import WebDriver
from typing import Tuple
from core.config import EXPLICIT_WAIT
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException, ElementNotInteractableException
import time

class BasePage:
    """基础页面类，封装常用的 Selenium 操作
    
    Attributes:
        driver: Selenium WebDriver 实例
        wait: WebDriverWait 实例，用于显式等待
    """
    
    def __init__(self, driver: WebDriver, timeout: int = None):
        """初始化基础页面
        
        Args:
            driver: Selenium WebDriver 实例
            timeout: 显式等待超时时间（秒），默认使用配置文件中的 EXPLICIT_WAIT
        """
        self.driver = driver
        if timeout is None:
            timeout = EXPLICIT_WAIT
        self.wait = WebDriverWait(driver, timeout)

    def find_and_click(self, locator: Tuple[str, str]):
        """等待元素可点击并点击（终极稳定版）
        
        Args:
            locator: 元素定位器元组
        
        Returns:
            WebElement: 被点击的元素对象
        """
        # 1. 等待元素出现在 DOM 中
        element = self.wait.until(EC.presence_of_element_located(locator))
        
        # 2. 滚动到视图中心，这是解决“不可交互”最关键的一步
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        time.sleep(0.3) # 稍微多等一点点，让浏览器渲染跟上

        try:
            # 3. 策略一：尝试等待可点击并执行普通点击
            WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable(locator)).click()
        except (ElementClickInterceptedException, ElementNotInteractableException, Exception) as e:
            # 4. 策略二：如果普通点击失败（被遮挡或不可交互），直接使用 JS 强制点击
            print(f"⚠️ 普通点击失败 ({type(e).__name__})，已切换为 JS 强制点击")
            self.driver.execute_script("arguments[0].click();", element)
        
        return element

    def find_and_input(self, locator: Tuple[str, str], text: str):
        """等待元素可见并输入文本
        
        Args:
            locator: 元素定位器元组
            text: 要输入的文本内容
        
        Returns:
            WebElement: 输入框元素对象
        """
        element = self.wait.until(EC.visibility_of_element_located(locator))
        element.clear()
        element.send_keys(text)
        return element

    def get_text(self, locator: Tuple[str, str]) -> str:
        """获取元素文本内容
        
        Args:
            locator: 元素定位器元组
        
        Returns:
            str: 元素的文本内容
        """
        element = self.wait.until(EC.visibility_of_element_located(locator))
        return element.text

    def is_element_present(self, locator: Tuple[str, str], timeout: int = 5) -> bool:
        """检查元素是否存在（不影响全局隐式等待）
        
        Args:
            locator: 元素定位器元组
            timeout: 等待超时时间（秒），默认 5 秒
        
        Returns:
            bool: 元素是否存在
        """
        try:
            short_wait = WebDriverWait(self.driver, timeout)
            short_wait.until(EC.presence_of_element_located(locator))
            return True
        except (TimeoutException, NoSuchElementException):
            return False

    def wait_for_element_gone(self, locator: Tuple[str, str], timeout: int = 10):
        """等待元素从 DOM 中消失
        
        Args:
            locator: 元素定位器元组
            timeout: 等待超时时间（秒），默认 10 秒
        """
        self.wait.until_not(EC.presence_of_element_located(locator))

    def scroll_into_view(self, locator: Tuple[str, str]):
        """滚动元素到视图中央
        
        Args:
            locator: 元素定位器元组
        
        Returns:
            WebElement: 滚动后的元素对象
        """
        element = self.wait.until(EC.presence_of_element_located(locator))
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        return element

    def click_with_js(self, locator: Tuple[str, str]):
        """使用JavaScript点击元素（处理被遮挡的元素）
        
        Args:
            locator: 元素定位器元组
        
        Returns:
            WebElement: 被点击的元素对象
        """
        element = self.wait.until(EC.presence_of_element_located(locator))
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        time.sleep(0.2)
        self.driver.execute_script("arguments[0].click();", element)
        return element

    def smart_click(self, locator: Tuple[str, str], timeout: int = 10):
        """智能点击：带有重试机制和滚动处理
        
        Args:
            locator: 元素定位器
            timeout: 超时时间
        
        Returns:
            WebElement: 被点击的元素
        """
        last_exception = None
        end_time = time.time() + timeout
        
        while time.time() < end_time:
            try:
                # 1. 等待元素可点击
                element = self.wait.until(EC.element_to_be_clickable(locator))
                
                # 2. 滚动到视图中心
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                time.sleep(0.2) # 给滚动一点时间
                
                # 3. 尝试点击
                element.click()
                return element
                
            except (ElementClickInterceptedException, TimeoutException, Exception) as e:
                last_exception = e
                print(f"⚠️ 点击失败，正在重试... ({str(e)[:50]})")
                time.sleep(0.5) # 重试间隔
                continue
        
        # 如果所有重试都失败，抛出异常
        raise Exception(f"智能点击失败: {locator}. 最后错误: {last_exception}")

    def smart_input(self, locator: Tuple[str, str], text: str, timeout: int = 10):
        """智能输入：带有清空和重试机制"""
        last_exception = None
        end_time = time.time() + timeout
        
        while time.time() < end_time:
            try:
                element = self.wait.until(EC.visibility_of_element_located(locator))
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                time.sleep(0.2)
                
                element.clear()
                element.send_keys(text)
                return element
                
            except Exception as e:
                last_exception = e
                print(f"⚠️ 输入失败，正在重试... ({str(e)[:50]})")
                time.sleep(0.5)
                continue
        
        raise Exception(f"智能输入失败: {locator}. 最后错误: {last_exception}")
