"""
页面对象：安排生产页面 (Production Arrange Page)
功能：安排生产到生产线的所有 UI 操作
- 独立导航（顶部 Produce 标签 + 左侧 Element Plus 侧边栏）
- 三层菜单：Produce → Production Orders → Waiting Arrange
- 搜索订单（Basic conditions 输入框 + Search 按钮）
- 勾选目标订单（复用 arrange_order_page 的复选框定位器）
- Production Arrange 下拉按钮 → Arrange selected orders

继承 BasePage（独立，不依赖 ArrangeOrderPage 的隐含前提）

注意：导航路径参考 GalaxyERP 截图:
  顶部: Produce 标签
  左侧: Produce 分组 → Production Orders（可展开）→ Waiting Arrange（子项）
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from .base_page import BasePage
from .arrange_order_page import ArrangeOrderPage
import time


class ProductionArrangePage(BasePage):
    """安排生产页面对象 — 独立实现导航 + 搜索 + 勾选 + Production Arrange 下拉"""

    # ==================== 定位器 ====================

    LOCATORS = {
        # 表格行
        "order_rows": (By.CSS_SELECTOR, 'table.el-table__body tbody tr.el-table__row'),
    }

    # 安排生产专用定位器（全文本匹配，不依赖租户动态 ID）
    PRODUCTION_LOCATORS = {
        # 顶部 Produce 标签
        "produce_tab": (By.XPATH, '//div[contains(@class, "label-container")][contains(translate(text(), "PRODUCE", "produce"), "produce")]'),
        # 左侧 Production Orders 菜单
        "production_orders_menu": (By.XPATH, '//*[contains(@class, "el-menu-item") and contains(., "Production Orders")]'),
        # 左侧 Waiting Arrange 菜单
        "waiting_arrange_menu": (By.XPATH, '//*[contains(@class, "el-menu-item") and contains(., "Waiting Arrange")]'),
        # Basic conditions 搜索输入框
        "search_input": (By.XPATH, '//input[contains(@placeholder, "Basic conditions") or contains(@placeholder, "Origin Order ID") or contains(@placeholder, "Batch search")]'),
        # Search 按钮
        "search_button": (By.XPATH, '//button[contains(., "Search") or contains(., "搜索")]'),
        # Production Arrange 下拉按钮
        "production_arrange_btn": (By.XPATH, '//button[contains(., "Production Arrange")]'),
        # 下拉选项 Arrange selected orders
        "arrange_selected_item": (By.XPATH, '//li[contains(., "Arrange selected orders") or contains(., "安排选中订单")]'),
    }

    # ==================== 导航 ====================

    def _click_produce_tab(self):
        """点击顶部 Produce 标签（如果当前不在 Produce 页面）

        实际 HTML（参考 arrange_order_page 的 Order 标签）:
          <div class="el-tabs__item ...">
            <div class="label-container"> Produce </div>
          </div>
        """
        print("  ⏳ 点击顶部 Produce 标签...")

        # 检查是否已在 Produce 页面（侧边栏有 Production Orders 即认为已激活）
        if self._is_produce_page_active():
            print("  ✅ 当前已在 Produce 页面，跳过点击")
            return True

        # 策略 1: 精确点击 .label-container 内的 Produce 文本
        xpaths = [
            '(//div[contains(@class, "label-container")])[1]',  # 兜底第一个
            '//div[contains(@class, "label-container")]',
        ]
        for i, xpath in enumerate(xpaths):
            try:
                elements = self.driver.find_elements(By.XPATH, xpath)
                if not elements:
                    continue
                # 找文本 === "Produce" 的那个
                target = None
                for el in elements:
                    txt = (el.text or "").strip()
                    if txt == "Produce" or txt.startswith("Produce"):
                        target = el
                        break
                if not target:
                    continue
                if not target.is_displayed():
                    continue
                self.driver.execute_script("arguments[0].click();", target)
                time.sleep(1.5)
                if self._is_produce_page_active():
                    print(f"  ✅ Produce 标签已点击 (label-container #{i+1})")
                    return True
            except Exception as e:
                print(f"  ⚠️ 策略 #{i+1} 异常: {e}")
                continue

        # 策略 2: JS 兜底
        js_code = """
        var labels = document.querySelectorAll('.label-container');
        for (var i = 0; i < labels.length; i++) {
            var txt = (labels[i].textContent || '').trim();
            if (txt === 'Produce' || txt.indexOf('Produce') === 0) {
                labels[i].click();
                return 'clicked';
            }
        }
        return '';
        """
        try:
            result = self.driver.execute_script(js_code)
            if result:
                time.sleep(1.5)
                if self._is_produce_page_active():
                    print(f"  ✅ Produce 标签已点击 (JS 兜底)")
                    return True
        except Exception as e:
            print(f"  ⚠️ JS 兜底异常: {e}")

        print("  ❌ 未找到 Produce 标签")
        return False

    def _is_produce_page_active(self) -> bool:
        """检查是否已在 Produce 页面（侧边栏有 Production Orders / Waiting Arrange 元素）"""
        js_code = """
        var menus = document.querySelectorAll('.el-menu-item');
        for (var i = 0; i < menus.length; i++) {
            var txt = (menus[i].textContent || '').trim();
            if (txt.indexOf('Production Orders') >= 0 || txt.indexOf('Waiting Arrange') >= 0) {
                return true;
            }
        }
        return false;
        """
        try:
            return bool(self.driver.execute_script(js_code))
        except Exception:
            return False

    def _click_production_orders_menu(self):
        """点击左侧 Production Orders 菜单（展开子菜单）"""
        print("  ⏳ 点击左侧 Production Orders 菜单...")

        strategies = [
            (By.XPATH, '//*[contains(@class, "el-menu-item") and contains(., "Production Orders")]'),
            (By.XPATH, '//*[contains(., "Production Orders")]'),
        ]
        for i, (by, value) in enumerate(strategies, 1):
            try:
                elements = self.driver.find_elements(by, value)
                for el in elements:
                    if el.is_displayed():
                        self.driver.execute_script("arguments[0].click();", el)
                        time.sleep(1)
                        print(f"  ✅ Production Orders 已点击 (定位器 #{i})")
                        return
            except Exception as e:
                print(f"  ⚠️ 定位器 #{i} 异常: {e}")
                continue

        raise Exception("❌ 未找到 Production Orders 菜单")

    def _click_waiting_arrange_menu(self):
        """点击左侧 Waiting Arrange 菜单"""
        print("  ⏳ 点击左侧 Waiting Arrange 菜单...")

        strategies = [
            (By.XPATH, '//*[contains(@class, "el-menu-item") and contains(., "Waiting Arrange")]'),
            (By.XPATH, '//*[contains(., "Waiting Arrange")]'),
            (By.XPATH, '//ul[contains(@class, "el-menu")]//li[contains(., "Waiting Arrange")]'),
        ]
        for i, (by, value) in enumerate(strategies, 1):
            try:
                elements = self.driver.find_elements(by, value)
                for el in elements:
                    if el.is_displayed():
                        self.driver.execute_script("arguments[0].click();", el)
                        time.sleep(2)
                        print(f"  ✅ Waiting Arrange 已点击 (定位器 #{i})")
                        return
            except Exception as e:
                print(f"  ⚠️ 定位器 #{i} 异常: {e}")
                continue

        raise Exception("❌ 未找到 Waiting Arrange 菜单")

    def navigate_to_waiting_arrange(self):
        """导航到 Waiting Arrange 页面

        流程: 点 Produce 标签 → 点左侧 Production Orders（展开子菜单）→ 点 Waiting Arrange
        """
        print("⏳ 导航到 Waiting Arrange 页面...")

        self._click_produce_tab()
        time.sleep(1)
        self._click_production_orders_menu()
        self._click_waiting_arrange_menu()
        time.sleep(2)

        print("✅ 已进入 Waiting Arrange 页面")

    # ==================== 搜索订单 ====================

    def _search_order(self, order_no: str):
        """搜索订单号（Basic conditions 输入框 + Search 按钮）

        截图显示:
          [Basic conditions 输入框] [Search] [Clear]
        """
        print(f"🔍 搜索订单号: {order_no}")

        # Step 1: 找 Basic conditions 输入框
        strategies = [
            (By.XPATH, '//input[contains(@placeholder, "Basic conditions") or contains(@placeholder, "Origin Order ID") or contains(@placeholder, "Batch search")]'),
            (By.CSS_SELECTOR, 'input[placeholder*="Basic conditions"], input[placeholder*="Origin Order ID"]'),
            (By.XPATH, '//div[contains(@class, "el-input")]//input[@type="text"]'),
        ]

        search_input = None
        for i, (by, value) in enumerate(strategies, 1):
            try:
                elements = self.driver.find_elements(by, value)
                for el in elements:
                    if el.is_displayed():
                        search_input = el
                        break
                if search_input:
                    break
            except Exception as e:
                print(f"  ⚠️ 搜索框定位器 #{i} 异常: {e}")
                continue

        if not search_input:
            raise Exception("❌ 未找到 Basic conditions 搜索输入框")

        # Step 2: 输入订单号
        search_input.clear()
        time.sleep(0.2)
        search_input.send_keys(order_no)
        time.sleep(0.5)

        # Step 3: 点 Search 按钮
        btn_strategies = [
            (By.XPATH, '//button[normalize-space(text())="Search" or normalize-space(text())="搜索"]'),
            (By.XPATH, '//button[contains(@class, "el-button--primary") and (contains(., "Search") or contains(., "搜索"))]'),
            (By.XPATH, '//button[contains(., "Search") or contains(., "搜索")]'),
        ]
        btn_clicked = False
        for i, (by, value) in enumerate(btn_strategies, 1):
            try:
                elements = self.driver.find_elements(by, value)
                for btn in elements:
                    if btn.is_displayed():
                        self.driver.execute_script("arguments[0].click();", btn)
                        time.sleep(2)
                        print(f"  ✅ Search 按钮已点击 (定位器 #{i})")
                        btn_clicked = True
                        break
                if btn_clicked:
                    break
            except Exception as e:
                print(f"  ⚠️ Search 按钮定位器 #{i} 异常: {e}")
                continue

        if not btn_clicked:
            # 兜底：直接按 Enter
            search_input.send_keys("\n")
            time.sleep(2)
            print("  ⚠️ 未找到 Search 按钮，已按 Enter 兜底")

        print(f"✅ 搜索完成: {order_no}")
        time.sleep(1)

        # 搜索后勾选匹配的订单（复用 ArrangeOrderPage 的复选框定位器）
        self._check_searched_order(order_no)

    def _check_searched_order(self, order_no: str):
        """勾选搜索结果中的目标订单（表格复选框）

        复用 ArrangeOrderPage 的实现，确保两个模块的勾选逻辑一致。
        """
        # 实例化一个 ArrangeOrderPage 共用复选框定位器
        helper = ArrangeOrderPage(self.driver)
        helper._check_searched_order(order_no)

    # ==================== Production Arrange 下拉 ====================

    def _click_production_arrange(self):
        """点击 Production Arrange 下拉按钮"""
        print("⏳ 点击 Production Arrange 按钮...")

        strategies = [
            (By.XPATH, '//button[contains(., "Production Arrange")]'),
            (By.XPATH, '//*[contains(@class, "el-button") and contains(., "Production Arrange")]'),
        ]
        for i, (by, value) in enumerate(strategies, 1):
            try:
                elements = self.driver.find_elements(by, value)
                for el in elements:
                    if el.is_displayed():
                        self.driver.execute_script("arguments[0].click();", el)
                        time.sleep(1)
                        # 校验下拉是否展开
                        expanded = self.driver.execute_script("""
                            var popper = document.querySelector('.el-dropdown-menu, .el-popper[aria-hidden="false"], .el-menu--popup');
                            if (!popper) return false;
                            var style = window.getComputedStyle(popper);
                            return style.display !== 'none' && style.visibility !== 'hidden';
                        """)
                        if expanded:
                            print(f"  ✅ Production Arrange 下拉已展开 (定位器 #{i})")
                            return
                        else:
                            print(f"  ⚠️ 策略 #{i} 点击后下拉未展开，尝试下一策略")
            except Exception as e:
                print(f"  ⚠️ 定位器 #{i} 异常: {e}")
                continue

        # JS 兜底
        try:
            result = self.driver.execute_script("""
                var btns = document.querySelectorAll('button');
                for (var i = 0; i < btns.length; i++) {
                    if ((btns[i].textContent || '').trim().indexOf('Production Arrange') >= 0) {
                        btns[i].click();
                        return true;
                    }
                }
                return false;
            """)
            if result:
                time.sleep(1)
                print("  ✅ Production Arrange 下拉已展开 (JS 兜底)")
                return
        except Exception as e:
            print(f"  ⚠️ JS 兜底异常: {e}")

        raise Exception("❌ 未找到 Production Arrange 按钮或下拉未展开")

    def _click_arrange_selected(self):
        """在下拉中选择 Arrange selected orders"""
        print("⏳ 选择 Arrange selected orders...")

        # 等待下拉动画
        time.sleep(0.5)

        strategies = [
            (By.XPATH, '//li[contains(., "Arrange selected orders")]'),
            (By.XPATH, '//*[contains(@class, "el-dropdown-menu__item") and contains(., "Arrange selected orders")]'),
            (By.XPATH, '//ul[contains(@class, "el-dropdown-menu")]//li[contains(., "Arrange")]'),
            (By.XPATH, '//ul[contains(@class, "el-menu--popup")]//li[contains(., "Arrange")]'),
        ]
        for i, (by, value) in enumerate(strategies, 1):
            try:
                elements = self.driver.find_elements(by, value)
                for el in elements:
                    if el.is_displayed():
                        txt = (el.text or "").strip()
                        self.driver.execute_script("arguments[0].click();", el)
                        time.sleep(2)
                        print(f"  ✅ 已选择: '{txt}' (定位器 #{i})")
                        return
            except Exception as e:
                print(f"  ⚠️ 定位器 #{i} 异常: {e}")
                continue

        # JS 兜底
        try:
            result = self.driver.execute_script("""
                var items = document.querySelectorAll('.el-dropdown-menu__item, .el-menu--popup li');
                for (var i = 0; i < items.length; i++) {
                    var txt = (items[i].textContent || '').trim();
                    if (txt.indexOf('Arrange selected') >= 0 || txt.indexOf('安排选中') >= 0) {
                        items[i].click();
                        return txt;
                    }
                }
                return '';
            """)
            if result:
                time.sleep(2)
                print(f"  ✅ 已选择 (JS 兜底): '{result}'")
                return
        except Exception as e:
            print(f"  ⚠️ JS 兜底异常: {e}")

        raise Exception("❌ 未找到 Arrange selected orders 选项")

    def _confirm_arrange(self):
        """点二次确认弹窗的 OK 按钮（Element Plus message-box）

        截图结构:
          <div class="el-message-box">
            <div class="el-message-box__btns">
              <button>Cancel</button>
              <button class="el-button--primary">OK</button>   ← 主按钮
            </div>
          </div>
        """
        print("⏳ 等待二次确认弹窗...")

        # Step 1: 等弹窗出现（10 秒超时）
        try:
            WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, '.el-message-box'))
            )
        except TimeoutException:
            raise Exception("❌ 二次确认弹窗未出现（10 秒超时）")

        time.sleep(0.3)  # 让弹窗动画稳定

        # Step 2: 点 OK 按钮（主按钮 = el-button--primary，在 .el-message-box__btns 内）
        locators = [
            (By.CSS_SELECTOR, '.el-message-box__btns button.el-button--primary'),
            (By.CSS_SELECTOR, '.el-message-box .el-button--primary'),
            (By.XPATH, '//div[contains(@class, "el-message-box")]//button[contains(., "OK")]'),
            (By.CSS_SELECTOR, '.el-message-box__btns button:last-child'),
        ]
        for i, (by, value) in enumerate(locators, 1):
            try:
                elements = self.driver.find_elements(by, value)
                for el in elements:
                    if el.is_displayed():
                        txt = (el.text or "").strip()
                        self.driver.execute_script("arguments[0].click();", el)
                        print(f"✅ 已点二次确认: '{txt}' (定位器 #{i})")
                        time.sleep(2)
                        return
            except Exception as e:
                print(f"  ⚠️ 定位器 #{i} 异常: {e}")
                continue

        raise Exception("❌ 未找到二次确认 OK 按钮")

    # ==================== 对外入口 ====================

    def arrange_production(self, order_no: str):
        """安排生产（对外入口）

        流程: 导航 → 搜索 → 勾选 → Production Arrange 下拉 → Arrange selected orders → 二次确认 OK
        """
        print(f"\n========== 安排生产 (供销侧) ==========")
        print(f"  订单号: {order_no}")

        self.navigate_to_waiting_arrange()
        self._search_order(order_no)
        self._click_production_arrange()
        self._click_arrange_selected()
        self._confirm_arrange()   # ★ 二次确认弹窗 OK 按钮

        print(f"✅ 安排生产完成: {order_no}\n")
