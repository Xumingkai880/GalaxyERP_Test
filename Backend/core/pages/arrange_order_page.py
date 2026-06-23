"""
页面对象：安排订单页面 (Arrange Order Page)
功能：安排订单到供销商的所有 UI 操作
- 独立导航（自带 Order 标签点击）
- 分销视角切换
- 搜索订单 → 推送 → 选择供销商 → 确认
- 供销侧验证（数量差量 + 订单存在）

继承 BasePage（独立，不依赖 OrderPage 的隐含前提）
"""

from selenium.webdriver.common.by import By
from .base_page import BasePage
import time


class ArrangeOrderPage(BasePage):
    """安排订单页面对象 — 独立实现导航 + 推送 + 验证"""

    # ==================== 定位器 ====================

    LOCATORS = {
        # 表格行
        "order_rows": (By.CSS_SELECTOR, 'table.el-table__body tbody tr.el-table__row'),
    }

    # 安排订单专用定位器（全文本匹配，不依赖租户动态 ID）
    ARRANGE_LOCATORS = {
        # 推送到供销商按钮
        "push_btn": (By.XPATH, '//button[contains(., "Push orders to suppliers") or contains(., "推送到供销商")]'),
        # 供销商下拉框（弹窗中）
        "supplier_select": (By.CSS_SELECTOR, '.el-select.w-300, .el-select'),
        # 下拉选项
        "supplier_dropdown_item": (By.CSS_SELECTOR, '.el-select-dropdown__item'),
        # 弹窗确认按钮
        "push_confirm_btn": (By.XPATH, '//div[@role="dialog"]//button[contains(., "Sure") or contains(., "确")]'),
        # 搜索输入框
        "search_input": (By.XPATH, '//input[@placeholder and (contains(@placeholder, "订单号") or contains(@placeholder, "Order") or contains(@placeholder, "order"))]'),
    }

    # ==================== 导航 ====================

    def _click_order_tab(self):
        """点击顶部 Order 标签，打开下拉菜单

        实际 HTML（从截图提取）:
        <div class="el-tabs__item is-top is-active" id="tab-Order1912746753302405122" ...>
          <div class="label-container">
            Order
            <ul class="box en_width" style="display: none;">  ← 下拉菜单
              <li>
                <div class="box-menu-title">Shop Orders</div>  ← 分类标题，不可点
                <div class="box-menu-list">
                  <div class="menu-name"><span>Waiting Process</span></div>  ← 可点
                </div>
              </li>
            </ul>
          </div>
        </div>

        注意：点击外层 .el-tabs__item 不会触发下拉（Element Plus 默认行为）。
              必须点击内层 .label-container 才会展开 .box 下拉面板。
        """
        print("  ⏳ 点击顶部 Order 标签...")

        # 策略 1: 精确点击 .label-container 内的 Order 文本节点
        xpaths = [
            # ★ 最佳：class 同时含 label-container 且直接子文本是 Order
            '(//div[contains(@class, "label-container")])[1]',
            # 兜底：任意 .label-container
            '//div[contains(@class, "label-container")]',
        ]

        for i, xpath in enumerate(xpaths):
            try:
                elements = self.driver.find_elements(By.XPATH, xpath)
                if not elements:
                    continue
                target = elements[0]
                # 必须 visible（dist 登录后可能在 Dashboard，但 Order 标签仍可见）
                if not target.is_displayed():
                    continue
                # JS 强制点击（避开 Element Plus 内部事件拦截）
                self.driver.execute_script("arguments[0].click();", target)
                time.sleep(1)
                # 校验：.box 应该是 display:block
                expanded = self.driver.execute_script("""
                    var box = document.querySelector('.el-tabs__item .box, .label-container .box');
                    return box && window.getComputedStyle(box).display !== 'none';
                """)
                if expanded:
                    print(f"  ✅ Order 下拉已打开 (label-container #{i+1})")
                    return True
                else:
                    print(f"  ⚠️ 策略 #{i+1} 点击后下拉未展开，尝试下一策略")
            except Exception as e:
                print(f"  ⚠️ 策略 #{i+1} 异常: {e}")
                continue

        # 策略 2: JS 兜底 - 在所有 el-tabs__item 中找含 "Order" 文本的
        js_code = """
        var items = document.querySelectorAll('.el-tabs__item');
        for (var i = 0; i < items.length; i++) {
            var label = items[i].querySelector('.label-container');
            if (label && (label.textContent || '').trim().indexOf('Order') === 0) {
                label.click();
                return 'clicked-label-in-tab';
            }
        }
        // 兜底：直接找 .label-container
        var labels = document.querySelectorAll('.label-container');
        for (var j = 0; j < labels.length; j++) {
            if ((labels[j].textContent || '').trim().indexOf('Order') === 0) {
                labels[j].click();
                return 'clicked-label-direct';
            }
        }
        return '';
        """
        try:
            result = self.driver.execute_script(js_code)
            if result:
                time.sleep(1)
                print(f"  ✅ Order 下拉已打开 (JS 兜底: {result})")
                return True
        except Exception as e:
            print(f"  ⚠️ JS 兜底异常: {e}")

        print("  ❌ 未找到 Order 标签（顶层导航栏中无 label-container）")
        return False

    def navigate_to_waiting_process(self):
        """导航到 Waiting Process

        实际 UI 结构（自定义下拉，非 Element Plus 侧边栏）:
            顶部 .label-container → 点击打开 .box.en_width 下拉面板
            → 下拉中 .menu-name > span 文本 = "Waiting Process"

        注意: 不需要 _click_left_menu 中间步骤。
              下拉面板中 Shop Orders (.box-menu-title) 是分类标题，不可点击。
              可点击的是 .menu-name span。
        """
        print("⏳ 导航到待处理订单界面...")

        # Step 0: 点击 Order 标签打开下拉面板
        self._click_order_tab()
        time.sleep(2)

        # Step 1: 在下拉面板中点击 Waiting Process
        locators = [
            (By.XPATH, '//div[contains(@class, "menu-name")]//span[contains(text(), "Waiting Process")]'),
            (By.XPATH, '//span[contains(text(), "Waiting Process")]'),
            (By.XPATH, '//span[contains(., "待处理")]'),
            (By.CSS_SELECTOR, '.menu-name span'),
            # 宽泛兜底：下拉面板中任意含 "Waiting" 的 span
            (By.XPATH, '//ul[contains(@class, "box")]//span[contains(text(), "Waiting")]'),
        ]

        found = False
        for i, (by, value) in enumerate(locators):
            try:
                elements = self.driver.find_elements(by, value)
                for el in elements:
                    if el.is_displayed():
                        txt = (el.text or "").strip()
                        if "Waiting" in txt or "待处理" in txt:
                            self.driver.execute_script("arguments[0].click();", el)
                            time.sleep(2)
                            print(f"✅ 已进入待处理订单界面 (定位器 #{i+1}: '{txt}')")
                            found = True
                            break
                if found:
                    break
            except Exception:
                continue

        if not found:
            raise Exception("❌ 无法导航到待处理订单界面（下拉中未找到 Waiting Process）")

    # ==================== 计数 ====================

    def get_order_count(self) -> int:
        """获取待处理订单数量（优先菜单标签 → 表格兜底）"""
        try:
            time.sleep(0.5)
            locators = [
                (By.XPATH, '//span[@title="Waiting Process"]/../span[@class="el-tag el-tag--primary el-tag--dark"]//span[@class="el-tag__content"]'),
                (By.CSS_SELECTOR, 'span[title="Waiting Process"] + span.el-tag span.el-tag__content'),
            ]
            for locator in locators:
                try:
                    elements = self.driver.find_elements(*locator)
                    if elements:
                        txt = elements[0].text.strip()
                        if txt and txt.isdigit():
                            count = int(txt)
                            print(f"  待处理订单数量: {count}")
                            return count
                except Exception:
                    continue

            print("  ⚠️ 菜单标签获取失败 → 表格兜底")
            return self._get_order_count_from_table()
        except Exception as e:
            print(f"  ❌ 获取订单数量失败: {e}")
            return 0

    def _get_order_count_from_table(self) -> int:
        """从表格行数获取订单数量（兜底）"""
        try:
            time.sleep(1)
            rows = self.driver.find_elements(*self.LOCATORS["order_rows"])
            count = len(rows)
            print(f"  表格订单数量: {count}")
            return count
        except Exception as e:
            print(f"  ❌ 表格计数失败: {e}")
            return 0

    # ==================== 分销侧：主流程 ====================

    def arrange_order_dist_side(self, order_no: str, supplier_name: str = "分销测试"):
        """分销侧安排订单（对外入口）

        流程: 导航 → 分销视角 → 搜订单 → 勾选订单 → 推送 → 选供应商 → 确认
        """
        print(f"\n========== 安排订单 (分销侧) ==========")
        print(f"  订单号: {order_no}")
        print(f"  供销商: {supplier_name}")

        self.navigate_to_waiting_process()
        self._switch_to_distribution_view()
        self._search_order(order_no)
        self._click_push_to_supplier()
        self._select_supplier(supplier_name)
        self._confirm_push()

        print(f"✅ 安排订单完成: {order_no}\n")

    # ==================== 分销视角切换 ====================

    def _switch_to_distribution_view(self):
        """切换到 Distribution 视角（Segmented Control: Self / Distribution）"""
        print("⏳ 切换到 Distribution 视角...")

        locators = [
            (By.XPATH, '//div[contains(@class, "tab-item") and contains(., "Distribution")]'),
            (By.XPATH, '//div[contains(@class, "tab-item")][contains(@title, "Distribution")]'),
            (By.CSS_SELECTOR, '.tab-item[title*="Distribution"]'),
            (By.XPATH, '//div[contains(@class, "segmented-control")]//div[contains(@class, "tab-item")][2]'),
        ]

        for i, (by, value) in enumerate(locators):
            try:
                elements = self.driver.find_elements(by, value)
                for el in elements:
                    if el.is_displayed():
                        self.driver.execute_script("arguments[0].click();", el)
                        print(f"✅ Distribution 视角已切换 (定位器 #{i+1})")
                        time.sleep(1.5)
                        return
            except Exception:
                continue

        # JS 兜底
        js_code = """
        var tabs = document.querySelectorAll('.tab-item');
        for (var i = 0; i < tabs.length; i++) {
            if (tabs[i].textContent.trim() === 'Distribution') {
                tabs[i].click();
                return true;
            }
        }
        return false;
        """
        if self.driver.execute_script(js_code):
            print("✅ Distribution 视角已切换 (JS)")
            time.sleep(1.5)
            return

        print("⚠️ 未找到 Distribution 切换按钮（可能已在该视角）")
        time.sleep(1)

    # ==================== 搜索订单 ====================

    def _search_order(self, order_no: str):
        """搜索订单号"""
        print(f"🔍 搜索订单号: {order_no}")

        strategies = [
            (By.XPATH, '//input[contains(@placeholder, "Order") or contains(@placeholder, "订单号") or contains(@placeholder, "order")]'),
            (By.CSS_SELECTOR, 'input.el-input__inner[placeholder*="Order"], input.el-input__inner[placeholder*="订单"]'),
            (By.XPATH, '//div[contains(@class, "el-input")]//input[@type="text"]'),
        ]

        search_input = None
        for by, value in strategies:
            try:
                elements = self.driver.find_elements(by, value)
                for el in elements:
                    if el.is_displayed():
                        search_input = el
                        break
                if search_input:
                    break
            except Exception:
                continue

        if not search_input:
            raise Exception("❌ 未找到搜索输入框")

        search_input.clear()
        time.sleep(0.2)
        search_input.send_keys(order_no)
        search_input.send_keys("\n")
        time.sleep(2)

        # 搜索按钮兜底
        try:
            btns = self.driver.find_elements(
                By.XPATH, '//button[contains(., "搜索") or contains(., "Search") or contains(@class, "el-button--primary")]'
            )
            for btn in btns:
                if btn.is_displayed() and btn.text.strip() in ["搜索", "Search", ""]:
                    self.driver.execute_script("arguments[0].click();", btn)
                    time.sleep(1)
                    break
        except Exception:
            pass

        print(f"✅ 搜索完成: {order_no}")
        time.sleep(1)

        # 搜索后勾选匹配的订单（表格行前的复选框）
        self._check_searched_order(order_no)

    def _check_searched_order(self, order_no: str):
        """勾选搜索结果中的目标订单（表格复选框）

        Element Plus 表格复选框结构:
          <label class="el-checkbox">
            <span class="el-checkbox__input">
              <span class="el-checkbox__inner"></span>
              <input type="checkbox" ...>
            </span>
          </label>
        """
        print(f"☑️ 勾选搜索结果中的订单: {order_no}")

        strategies = [
            # 策略 1: 找含订单号的行，点行内第一个复选框
            f'//table[contains(@class,"el-table")]//tr[contains(., "{order_no}")]//label[contains(@class, "el-checkbox")]',
            # 策略 2: 任意含订单号的行 + td[1] 复选框
            f'//tr[contains(., "{order_no}")]//td[1]//label[contains(@class, "el-checkbox")]',
            # 策略 3: 表格 tbody 内所有行，复选框在第一列
            '//table[contains(@class,"el-table__body")]//tr//td[1]//label[contains(@class, "el-checkbox")]',
            # 策略 4: 仅 .el-checkbox__inner（最宽泛）
            '//label[contains(@class, "el-checkbox")]//span[contains(@class, "el-checkbox__inner")]',
        ]

        for i, xpath in enumerate(strategies, 1):
            try:
                elements = self.driver.find_elements(By.XPATH, xpath)
                visible = [e for e in elements if e.is_displayed()]
                if not visible:
                    continue

                target = visible[0]
                # JS 强制点击（避开 Element Plus 内部事件拦截 + 触发 change 事件）
                self.driver.execute_script("""
                    var el = arguments[0];
                    if (el.tagName === 'LABEL') el.click();
                    else {
                        var lbl = el.closest('label.el-checkbox') || el.closest('label');
                        if (lbl) lbl.click();
                        else el.click();
                    }
                """, target)
                time.sleep(0.5)

                # 校验：复选框应变为 checked
                checked = self.driver.execute_script("""
                    var el = arguments[0];
                    var lbl = el.tagName === 'LABEL' ? el : (el.closest('label.el-checkbox') || el.closest('label'));
                    if (!lbl) return false;
                    var input = lbl.querySelector('input[type="checkbox"]');
                    if (input) return input.checked;
                    return lbl.classList.contains('is-checked');
                """, target)

                if checked:
                    print(f"  ✅ 已勾选 (定位器 #{i})")
                    return
                else:
                    print(f"  ⚠️ 定位器 #{i} 点击后未勾选，尝试下一策略")
            except Exception as e:
                print(f"  ⚠️ 定位器 #{i} 异常: {e}")
                continue

        raise Exception(f"❌ 搜索后未找到订单 {order_no} 的复选框，无法勾选")

    # ==================== 推送流程 ====================

    def _click_push_to_supplier(self):
        """点击推送到供销商按钮"""
        print("⏳ 点击推送到供销商按钮...")

        locators = [
            (By.XPATH, '//button[contains(., "Push orders to suppliers") or contains(., "推送到供销商")]'),
            (By.XPATH, '//button[contains(., "Push") and contains(., "supplier")]'),
            (By.XPATH, '//button[contains(., "Push")]'),
            (By.CSS_SELECTOR, 'button.el-button--primary'),
        ]

        for i, (by, value) in enumerate(locators):
            try:
                elements = self.driver.find_elements(by, value)
                for el in elements:
                    if el.is_displayed():
                        txt = (el.text or "").strip()
                        if "Push" in txt or "push" in txt or "推送" in txt:
                            self.driver.execute_script("arguments[0].click();", el)
                            print(f"✅ 已点击: '{txt}' (定位器 #{i+1})")
                            time.sleep(1.5)
                            print("  等待弹窗打开...")
                            return
            except Exception:
                continue

        raise Exception("❌ 未找到推送到供销商按钮")

    def _select_supplier(self, supplier_name: str):
        """选择供销商 — 展开下拉框 → 匹配选项

        Element Plus el-select 真实结构（从截图提取）:
          <div class="el-select__wrapper el-tooltip__trigger" tabindex="-1">
            <div class="el-select__selection">
              <div class="el-select__placeholder is-transparent"><span>Supplier</span></div>
            </div>
            <div class="el-select__suffix">
              <i class="el-icon el-select__caret el-select__icon">▾</i>
            </div>
          </div>
        """
        print(f"⏳ 选择供销商: {supplier_name}")

        time.sleep(1)

        # Step 1: 点击下拉框（.el-select__wrapper）
        strategies = [
            # ★ Element Plus 新结构：.el-select__wrapper
            (By.CSS_SELECTOR, '.el-select__wrapper'),
            (By.XPATH, '//div[contains(@class, "el-select__wrapper")]'),
            # 兜底旧结构
            (By.CSS_SELECTOR, '.el-select.w-300'),
            (By.CSS_SELECTOR, '.el-select'),
            (By.XPATH, '//div[contains(@class, "el-select")]//input[@placeholder="Supplier" or contains(@placeholder, "Supplier")]'),
            (By.XPATH, '//div[@role="dialog"]//div[contains(@class, "el-select")]'),
        ]

        select_found = False
        for i, (by, value) in enumerate(strategies, 1):
            try:
                elements = self.driver.find_elements(by, value)
                for el in elements:
                    if not el.is_displayed():
                        continue
                    # 跳过其它 select（弹窗中可能多个 el-select）
                    txt = (el.text or "").strip()
                    # 仅匹配弹窗内 + 含 "Supplier" 文本的
                    in_dialog = self.driver.execute_script("""
                        var el = arguments[0];
                        return !!el.closest('.el-dialog, .el-overlay-dialog, [role="dialog"]');
                    """, el)
                    if not in_dialog:
                        continue
                    if "Supplier" not in txt and "supplier" not in (value or "").lower() and i > 2:
                        continue

                    self.driver.execute_script("arguments[0].click();", el)
                    time.sleep(0.5)
                    # 校验：.el-select-dropdown 是否出现且可见
                    opened = self.driver.execute_script("""
                        var dd = document.querySelector('.el-select-dropdown, .el-popper[aria-hidden="false"]');
                        if (!dd) return false;
                        var style = window.getComputedStyle(dd);
                        return style.display !== 'none' && style.visibility !== 'hidden';
                    """)
                    if opened:
                        print(f"  ✅ 下拉框已展开 (定位器 #{i})")
                        select_found = True
                        break
                if select_found:
                    break
            except Exception as e:
                print(f"  ⚠️ 定位器 #{i} 异常: {e}")
                continue

        if not select_found:
            # 兜底：JS 直接点击弹窗内的 .el-select__wrapper
            try:
                result = self.driver.execute_script("""
                    var wraps = document.querySelectorAll('.el-dialog .el-select__wrapper, [role="dialog"] .el-select__wrapper');
                    for (var i = 0; i < wraps.length; i++) {
                        var ph = wraps[i].querySelector('.el-select__placeholder');
                        if (ph && ph.textContent.trim() === 'Supplier') {
                            wraps[i].click();
                            return 'js-wrapper';
                        }
                    }
                    return '';
                """)
                if result:
                    print(f"  ✅ 下拉框已展开 (JS 兜底: {result})")
                    select_found = True
            except Exception as e:
                print(f"  ⚠️ JS 兜底异常: {e}")

        if not select_found:
            raise Exception("❌ 未找到供销商下拉框（弹窗内 .el-select__wrapper 不可点）")

        time.sleep(1)

        # Step 2: 在展开的下拉中匹配目标供销商选项
        # Element Plus 下拉项: <li class="el-select-dropdown__item"><span>分销测试</span></li>
        try:
            time.sleep(0.5)
            items = self.driver.find_elements(By.CSS_SELECTOR, '.el-select-dropdown__item, .el-select-dropdown__list li')
            visible_items = [it for it in items if it.is_displayed()]
            print(f"  找到 {len(visible_items)} 个可见下拉选项")
            for item in visible_items:
                txt = (item.text or "").strip()
                print(f"    - '{txt}'")
                if supplier_name and supplier_name in txt:
                    self.driver.execute_script("arguments[0].click();", item)
                    print(f"✅ 已选择供销商: '{txt}'")
                    time.sleep(0.5)
                    return

            # 兜底：选第一个非空项
            for item in visible_items:
                txt = (item.text or "").strip()
                if txt:
                    print(f"⚠️ 未匹配 '{supplier_name}'，选择第一项: '{txt}'")
                    self.driver.execute_script("arguments[0].click();", item)
                    time.sleep(0.5)
                    return
        except Exception as e:
            print(f"⚠️ 下拉选项异常: {e}")

        raise Exception(f"❌ 未找到供销商: {supplier_name}")

    def _confirm_push(self):
        """确认推送"""
        print("⏳ 确认推送...")

        locators = [
            (By.XPATH, '//div[@role="dialog"]//button[contains(., "Sure")]'),
            (By.XPATH, '//div[@role="dialog"]//button[contains(., "确")]'),
            (By.CSS_SELECTOR, '.el-dialog__footer button.el-button--primary'),
            (By.CSS_SELECTOR, '.el-overlay-dialog .el-dialog__footer button:last-child'),
        ]

        for i, (by, value) in enumerate(locators):
            try:
                elements = self.driver.find_elements(by, value)
                for el in elements:
                    if el.is_displayed():
                        self.driver.execute_script("arguments[0].click();", el)
                        print(f"✅ 已确认 (定位器 #{i+1})")
                        time.sleep(3)
                        print("✅ 推送完成")
                        return
            except Exception:
                continue

        raise Exception("❌ 未找到确认按钮")

    # ==================== 供销侧：验证 ====================

    def get_waiting_process_count(self) -> int:
        """供销侧获取待处理数量（推送前记录 count_before）"""
        self.navigate_to_waiting_process()
        return self.get_order_count()

    def verify_arrange_in_supply(self, order_no: str, count_before: int) -> dict:
        """供销侧验证：数量 +1 ? 订单存在 ?

        Returns: {"order_exists": bool, "count_before": int, "count_after": int, "count_ok": bool}
        Raises: AssertionError 数量不对时
        """
        print(f"\n========== 验证安排结果 (供销侧) ==========")

        self.navigate_to_waiting_process()
        count_after = self.get_order_count()

        print(f"  推送前: {count_before} → 推送后: {count_after} (增量: {count_after - count_before})")

        count_ok = (count_after == count_before + 1)
        if count_ok:
            print(f"✅ 数量验证通过 (+1)")
        else:
            print(f"❌ 数量验证失败: 预期 {count_before + 1}，实际 {count_after}")

        order_exists = self._check_order_exists(order_no)
        if order_exists:
            print(f"✅ 订单 {order_no} 已存在")

        result = {"order_exists": order_exists, "count_before": count_before,
                   "count_after": count_after, "count_ok": count_ok}

        if not count_ok:
            raise AssertionError(f"安排订单验证失败: {count_before} → {count_after} (预期 +1)")

        print("========== 验证完成 ==========\n")
        return result

    def _check_order_exists(self, order_no: str) -> bool:
        """页面全文搜索订单号（body text → 表格行）"""
        try:
            time.sleep(1)
            page_text = self.driver.find_element(By.TAG_NAME, 'body').text
            if order_no in page_text:
                return True

            rows = self.driver.find_elements(*self.LOCATORS["order_rows"])
            for row in rows:
                if order_no in (row.text or ""):
                    return True
        except Exception as e:
            print(f"  检查订单存在异常: {e}")
        return False
