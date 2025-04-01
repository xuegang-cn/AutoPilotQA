import os
import time
import hashlib
import random
import subprocess
from datetime import datetime

import uiautomator2 as u2

import cv2
import pyshine as ps

from colorama import Fore, Style



class AndroidUITraverser:
    def __init__(self, device_serial=None, output_dir='ui_traversal', test_texts=None,max_depth=5,app_identifier='com.android.settings'):
        """
        初始化 Android UI 遍历器 (基于uiautomator2)

        :param device_serial: 设备序列号
        :param output_dir: 输出目录
        :param test_texts: 测试用文本列表
        """
        self.d = u2.connect(device_serial) if device_serial else u2.connect()
        self.output_dir = output_dir
        self.visited_hashes = set()  # 记录已访问的页面哈希
        self.screen_width, self.screen_height = self.d.window_size()
        self.test_texts = test_texts or ["测试", "hello", "123", "自动化"]
        self.visited_elements=set()
        self.all_unique_elememts=[]
        self.app_identifier=app_identifier
        self.system_blacklist = [
            'android:id/statusBarBackground',
            'android:id/navigationBarBackground',
            'android:id/action_bar_container'
        ]
        self.max_depth = max_depth  # 最大递归深度
        self.interaction_delay = 1.5
        os.makedirs(self.output_dir, exist_ok=True)

    def get_screen_size(self):
        """获取屏幕尺寸"""
        return self.d.window_size()

    def get_window_hash(self):
        """获取当前窗口的哈希值"""
        screenshot = self.d.screenshot()
        return hashlib.md5(screenshot.tobytes()).hexdigest()
    def get_current_window(self):
        """获取当前窗口信息"""
        try:
            # 获取当前活动窗口的包名和活动名
            current = self.d.info['currentPackageName'] + '/' + self.d.app_current().get('activity', 'unknown')
            return current
        except:
            return "unknown_window"

    def is_same_window(self,expect_window):
        """检查是否仍在同一窗口"""
        new_window = self.get_current_window()
        if new_window == expect_window:
            return True
        print(f"窗口已变化: {expect_window} -> {new_window}")
        return False

    def save_ui_tree(self, prefix=''):
        """保存当前UI树到txt文件"""
        timestamp = int(time.time())
        filename = f"{prefix}_ui_tree_{timestamp}.txt"
        filepath = os.path.join(self.output_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.d.dump_hierarchy())
        return filepath

    def take_screenshot(self, prefix=''):
        """截图并返回文件路径"""
        timestamp = int(time.time())
        filename = f"{prefix}_screenshot_{timestamp}.png"
        filepath = os.path.join(self.output_dir, filename)
        self.d.screenshot(filepath)
        return filepath

    def get_operable_elements(self):
        """获取当前页面所有可操作元素"""
        elements = []
        # 使用XPath获取所有可点击元素
        for element in self.d(classNameMatches=".*"):
            try:
                info = element.info
                print(info)
                elements.append(element)
            except Exception as e:
                print(f"Error processing element: {str(e)}")
            continue
        print(f'element size : {len(elements)}')
        return elements

    def get_input_fields(self):
        """获取所有可输入字段"""
        return self.d.xpath('//android.widget.EditText').all()

    def start_app(self, app_identifier):
        """
        通过包名或应用名启动应用
        :param app_identifier: 包名(如com.android.settings)或应用名(如"设置")
        :return: 是否启动成功
        """
        # 如果包含点(.)则认为是包名
        if '.' in app_identifier:
            try:
                self.d.app_start(app_identifier)
                print(f"通过包名启动应用: {app_identifier}")
                return True
            except Exception as e:
                print(f"通过包名启动应用失败: {e}")
                return False
        else:
            # 通过应用名启动
            try:
                # 先获取所有应用
                apps = self.d.app_list()
                for app in apps:
                    if app_identifier.lower() in app['name'].lower():
                        self.d.app_start(app['package'])
                        print(f"通过应用名启动: {app_identifier} (包名: {app['package']})")
                        return True
                print(f"未找到应用: {app_identifier}")
                return False
            except Exception as e:
                print(f"通过应用名启动失败: {e}")
                return False

    def perform_text_input(self, element, text):
        """
        在输入框中输入文本
        :param element: 输入框元素
        :param text: 要输入的文本
        """
        element.click()
        time.sleep(0.5)
        #element.clear_text()
        time.sleep(0.5)
        element.set_text(text)
        time.sleep(1)
        return f"输入: '{text}'"

    def perform_search(self, search_button=None):
        """
        执行搜索操作
        :param search_button: 可选的搜索按钮元素
        """
        # 尝试点击搜索按钮
        if search_button and search_button.exists:
            search_button.click()
            time.sleep(2)
            return "点击搜索按钮"

        # 尝试按回车键
        self.d.press('enter')
        time.sleep(2)
        return "按回车键搜索"

    def perform_swipe(self, direction='up', distance=0.8):
        """执行滑动操作"""
        center_x, center_y = self.screen_width // 2, self.screen_height // 2
        distance_px = int(min(self.screen_width, self.screen_height) * distance)

        if direction == 'up':
            self.d.swipe(center_x, center_y + distance_px // 2,
                         center_x, center_y - distance_px // 2)
        elif direction == 'down':
            self.d.swipe(center_x, center_y - distance_px // 2,
                         center_x, center_y + distance_px // 2)
        elif direction == 'left':
            self.d.swipe(center_x + distance_px // 2, center_y,
                         center_x - distance_px // 2, center_y)
        elif direction == 'right':
            self.d.swipe(center_x - distance_px // 2, center_y,
                         center_x + distance_px // 2, center_y)

        time.sleep(1)
        return f"滑动: {direction}"

    def perform_random_touch(self):
        """在随机位置执行触摸操作"""
        x = random.randint(100, self.screen_width - 100)
        y = random.randint(100, self.screen_height - 100)
        self.d.click(x, y)
        time.sleep(1)
        return f"触摸: ({x}, {y})"

    def dump_current_state(self, prefix=''):
        """记录当前状态: 截图 + 保存UI树"""
        window_hash = self.get_window_hash()
        screenshot_path = self.take_screenshot(prefix)
        ui_tree_path = self.save_ui_tree(prefix)
        self.visited_hashes.add(window_hash)
        print(f"状态记录: {screenshot_path}, {ui_tree_path}")
        return screenshot_path, ui_tree_path

    def handle_input_fields(self, prefix):
        """处理当前页面的输入字段"""
        input_fields = self.get_input_fields()
        if not input_fields:
            return []

        actions = []
        for field in input_fields:
            for text in random.sample(self.test_texts, min(2, len(self.test_texts))):  # 每个字段测试2个文本
                try:
                    # 输入前记录状态
                    self.dump_current_state(f'{prefix}_pre_input_{text}')

                    # 执行输入
                    input_desc = self.perform_text_input(field, text)
                    actions.append(input_desc)
                    print(input_desc)

                    # 尝试执行搜索
                    search_desc = self.perform_search()
                    actions.append(search_desc)
                    print(search_desc)
                    # 输入后记录状态
                    self.dump_current_state(f'{prefix}_post_input_{text}')

                    # 返回上一状态
                    time.sleep(2)

                except Exception as e:
                    print(f"输入操作失败: {str(e)}")
                    continue
        return actions




        # 深度遍历

    def traverse_app_with_depth(self, app_identifier=None, max_depth=3):
        """
        主遍历方法
        :param app_identifier: 应用包名或名称 (可选)
        :param max_depth: 最大遍历深度
        """
        #先回到home界面
        self.d.press('home')
        home_window=self.get_current_window()
        #启动应用
        if app_identifier:
            if not self.start_app(app_identifier):
                print(f"无法启动应用: {app_identifier}")
                return
            time.sleep(3)  # 等待应用启动
        main_window = self.get_current_window() #第一层主界面
        print("\n=== 广度遍历 ===")
        self.get_all_interactable_elements() # dump 主界面所有可操作元素
        need_swip=True
        depth=1
        swipe_count=0
        while need_swip:
            before=self.dump_current_state(self.get_page_signature())
            for  element in self.get_all_interactable_elements() :
                try:
                    # 操作前记录
                    print("准备操作 element:"+str(element.info))
                    element_singnature = self.get_element_signature(element)
                    before=self.get_current_window()
                    if element not in self.visited_elements:
                        self.visited_elements.add(element)
                        self.operate_element_based_on_type(element)
                    time.sleep(2) #进入二级界面
                    for  child in self.get_all_interactable_elements():
                            before = self.get_current_window()
                            if child not in self.visited_elements:
                                self.visited_elements.add(child)
                                self.operate_element_based_on_type(child)
                                self.dump_current_state(self.get_element_signature(child))
                                time.sleep(2)
                            if  before!=self.get_current_window():
                                self.d.press('back')
                                time.sleep(0.5)
                    print(f" current element signature is " + element_singnature)
                    after_window=self.get_current_window()
                    print(f"after_window {after_window}" )
                    self.dump_current_state(element_singnature)
                    # 操作后窗口变化 回到主界面继续操作其他元素
                    if after_window !=main_window:
                        self.d.press('back')
                        time.sleep(0.5)
                except Exception as e:
                    if self.get_current_window() != main_window and self.get_current_window()!=home_window:
                        print(f"操作失败: {str(e)}")
                        self.d.press('back')
                        time.sleep(0.5)
                    if  self.get_current_window()!=main_window:
                        self.d.app_stop_all()
                        self.d.press('home')
                        self.start_app(app_identifier)
                        time.sleep(3)
                        for i in range(0,swipe_count):
                            self.d.swipe(0.5, 0.8, 0.5, 0.2, duration=0.5)  # 从80%滑到20%
                            time.sleep(1.5)  # 等待新内容加载
                    continue
            print("准备滑动查找空间")
            self.d.swipe(0.5, 0.8, 0.5, 0.2, duration=0.5)  # 从80%滑到20%
            time.sleep(1.5)  # 等待新内容加载
            swipe_count=swipe_count+1
            after_swipe=self.dump_current_state(self.get_page_signature())
            if before==after_swipe:
                break


    def operate_element_based_on_type(self, element):
        """根据元素类型执行相应操作"""
        element_info = element.info

        try:
            class_name = element_info['className']


            print(f"操作元素: {element_info},")

            # 按钮类元素
            if class_name in ['android.widget.Button', 'android.widget.ImageButton']:
                element.click()

            # 输入框
            elif class_name == 'android.widget.EditText':
                print(f"在输入框输入文本: ")
                element.set_text("test_input")
                time.sleep(0.5)  # 等待输入完成

            # 复选框
            elif class_name == 'android.widget.CheckBox':
                current_state = element.info['checked']
                print(f"切换复选框状态: {current_state} -> {not current_state}")
                element.click()

            # 单选按钮
            elif class_name == 'android.widget.RadioButton':
                if not element.info['checked']:
                    print(f"选择单选按钮: ")
                    element.click()

            # 开关
            elif class_name in ['android.widget.Switch', 'android.widget.ToggleButton']:
                current_state = element.info['checked']
                print(f"切换开关状态: {current_state} -> {not current_state}")
                element.click()

            # 下拉菜单
            elif class_name == 'android.widget.Spinner':
                print(f"操作下拉菜单: ")
                self.operate_spinner(element)

            # 滑动条
            elif class_name == 'android.widget.SeekBar':
                print(f"调整滑动条: ")
                element.set_text("50")  # 设置中间值
            elif class_name == 'androidx.recyclerview.widget.RecyclerView':
                self._handle_recyclerview(element)
            # 其他可点击元素
            elif element_info.get('clickable', False):
                print(f"点击元素: ")
                element.click()
            elif element_info.get('longClickable', False):
                print(f"长击元素: ")
                element.long_click()
            time.sleep(0.3)  # 操作间隔


        except Exception as e:
            print(f"操作元素时出错: {str(e)}")


    def operate_spinner(self, spinner):
        """操作下拉菜单"""
        try:
            if spinner.click_exists():
                time.sleep(1)  # 等待下拉菜单展开

                # 尝试选择第一个可见选项
                first_option = self.d(className='android.widget.CheckedTextView',
                                      clickable=True,
                                      enabled=True).first
                if first_option.exists:
                    print(f"选择下拉选项: {first_option.info.get('text', '')}")
                    first_option.click()
        except Exception as e:
            print(f"操作下拉菜单时出错: {str(e)}")


    def scroll_down(self):
        """向下滑动屏幕，返回是否成功滑动（未到达底部）"""
        screen_width = self.d.info['displayWidth']
        screen_height = self.d.info['displayHeight']

        # 滑动参数
        start_x = screen_width // 2
        start_y = int(screen_height * 0.7)
        end_y = int(screen_height * 0.3)

        # 执行滑动
        self.d.swipe(start_x, start_y, start_x, end_y, steps=10)
        time.sleep(1)  # 等待内容加载

        # 检查是否到达底部
        current_y = self.get_screen_bottom_position()
        if self.last_y_position != -1 and abs(current_y - self.last_y_position) < 10:
            return False  # 已到达底部

        self.last_y_position = current_y
        return True  # 成功滑动


    def get_screen_bottom_position(self):
        """获取当前屏幕底部位置"""
        try:
            # 尝试找到列表或滚动视图
            scrollable = self.d(classNameMatches='.*ScrollView|.*ListView|.*RecyclerView',
                                scrollable=True).first
            if scrollable.exists:
                return scrollable.info['bounds']['bottom']
        except:
            pass

        return self.d.info['displayHeight']


    def get_all_interactable_elements(self) :
        """识别所有可交互元素而不仅仅是clickable=true的"""
        # XPath定位所有潜在可交互元素
        xpath_queries = [
            "//*[@clickable='true']",
            "//*[@enabled='true' and @focusable='true']",
            "//android.widget.EditText",
            "//android.widget.Switch",
            "//android.widget.CheckBox",
            "//android.widget.RadioButton",
            "//android.widget.Spinner",
            "//android.widget.ListView",
            "//android.widget.ScrollView",
            "//android.support.v7.widget.RecyclerView",
            "//androidx.recyclerview.widget.RecyclerView",
            "//*[contains(@class, 'Button')]",
            "//*[contains(@class, 'ImageButton')]",
            "//*[@long-clickable='true']"
        ]


        elements = []
        unique_elements = []
        screenshot_path, ui_tree_path=self.dump_current_state(self.get_page_signature())
        for query in xpath_queries:
            try:
                found = self.d.xpath(query).all()
                elements.extend(found)
            except:
                continue
        seen_element_ids = set()
        for elem in elements:
            elem_id = self.get_element_signature(elem)
            if elem_id not in seen_element_ids:
                seen_element_ids.add(elem_id)
                unique_elements.append(elem)
        self.all_unique_elememts=unique_elements
        current_time = datetime.now()
        formatted_time = current_time.strftime("%Y%m%d%H%M%S")
        self.draw_bbox_multi(screenshot_path, os.path.join(self.output_dir,f"{self.get_page_signature()}{formatted_time}labeled.png"), unique_elements)
        return self.filter_elements(unique_elements)

    def filter_elements(self, elements):
        filtered = []
        for elem in elements:
            # 检查黑名单
            resource_id = elem.info["resourceId"]
            if resource_id and any(
                    black_item in resource_id for black_item in self.system_blacklist):
                continue

            # 检查可见性

            # 检查大小(避免点击太小或空白的元素)
            rect = elem.info['bounds']
            if (rect['right']-rect['left']) < 10 or (rect['bottom']-rect['top']) < 10:
                continue

            filtered.append(elem)

        return filtered

    def get_page_signature(self) :
        """生成页面唯一签名"""
        activity = self.d.app_current().get('activity', 'unknown')
        source = self.d.info['currentPackageName']
        window_size = self.d.window_size()
        hash_obj = hashlib.md5(source.encode('utf-8'))
        source_hash = hash_obj.hexdigest()
        return f"{activity}:{window_size[0]}x{window_size[1]}:{source_hash}"

    def get_element_signature(self, element) :
        """生成元素唯一签名"""

        element_id = self.get_element_identifier(element)
        page_signature = self.get_page_signature()
        return f"{page_signature}:{element_id}"

    def get_element_identifier(self, element):
        """获取元素唯一标识"""
        resource_id = element.info["resourceId"] or ""
        text = element.info["text"] or ""
        content_desc = element.info["contentDescription"] or ""
        # 如果元素有唯一ID，优先使用
        if resource_id:
            return resource_id

        # 否则组合多个属性作为标识
        return f"{text[:20]}:{content_desc[:20]}:"
    def force_kill(self, package_name):
        """强制停止应用（最彻底）"""
        self.d.app_stop(package_name)  # 先尝试优雅停止
        subprocess.run(f'adb -s {self.d.serial} shell am force-stop {package_name}', shell=True)
    def clear_recent_tasks(self):
        """清除最近任务列表（需Android 10+）"""
        self.d.shell('am stack removeall')

    def is_element_visible(self, element):
        """判断元素是否在可见区域内"""

        if not element.exists:
            return False

            # 获取屏幕尺寸
        window_size = self.d.window_size()
        screen_width, screen_height = window_size

        # 获取元素坐标
        bounds = element.info['bounds']
        left, top, right, bottom = bounds['left'], bounds['top'], bounds['right'], bounds['bottom']

        # 判断元素是否在屏幕内
        return (0 <= left <= screen_width and
                0 <= top <= screen_height and
                0 <= right <= screen_width and
                0 <= bottom <= screen_height)


    def scroll_to_element(self, element):
        """将元素滚动到视图中心"""
        window_center = self.d.window_size()[1] /2
        elem_center = (element.info['bounds']['top'] + element.info['bounds']['bottom']) /2

        # 计算需要滑动的距离（像素）
        scroll_distance = elem_center - window_center

        if scroll_distance > 0:  # 需要向下滑动
            self.d.swipe(self.d.window_size()[0] // 2, window_center,
                         self.d.window_size()[0] // 2, window_center - scroll_distance)
        else:  # 需要向上滑动
            self.d.swipe(self.d.window_size()[0] // 2, window_center,
                         self.d.window_size()[0] // 2, window_center - scroll_distance)
        time.sleep(1)

    def _handle_recyclerview(self, element):
        """处理RecyclerView滑动"""
        print("检测到RecyclerView，执行滑动操作")
        bounds = element.info['bounds']
        start_x = (bounds['left'] + bounds['right']) / 2
        start_y = (bounds['top'] + bounds['bottom']) * 0.8  # 底部80%位置
        end_y = (bounds['top'] + bounds['bottom']) * 0.2  # 顶部20%位置

        # 缓慢滑动（400ms持续时间）
        self.d.swipe(start_x, start_y, start_x, end_y, duration=0.4)
        time.sleep(1)
        print("滑动操作结束")
    def smart_scroll_to_element(self, element):
        """智能滚动到元素（计算最佳滑动距离）"""
        elem_center = (element.info['bounds']['top'] + element.info['bounds']['bottom']) / 2
        window_center = self.d.window_size()[1] /2
        scroll_distance = elem_center - window_center

        if abs(scroll_distance) > 100:  # 需要滑动
            self.d.swipe(
                self.d.window_size()[0] / 2,
                window_center,
                self.d.window_size()[0] / 2,
                window_center - scroll_distance * 0.8,  # 滑动80%距离
                duration=0.5
            )

    def swipe_up_half_screen_if_element_at_bottom(self,element):
        # 获取屏幕尺寸
        window_size = self.d.window_size()
        screen_width, screen_height = window_size[0], window_size[1]

        # 获取元素位置
        bounds = element.info['bounds']
        element_top, element_bottom = bounds['top'], bounds['bottom']

        # 判断元素是否在屏幕底部区域（例如底部 1/3 区域）
        if element_bottom > screen_height * 9/ 10:
            # 向上滑动半个屏幕
            start_x = screen_width // 2
            start_y = screen_height * 3 // 4
            end_y = screen_height // 4
            self.d.swipe(start_x, start_y, start_x, end_y, duration=0.2)
            return True
        return False

    def _is_at_bottom(self):
        """判断是否滑动到底部"""
        last_screen = self.d.dump_hierarchy()
        self.d.swipe(0.5, 0.8, 0.5, 0.2, duration=0.5)  # 尝试滑动
        time.sleep(1)
        new_screen = self.d.dump_hierarchy()
        return last_screen == new_screen  # 如果滑动前后UI树相同，说明到底部

    def _smart_swipe_down(slef):
        """智能滑动（根据屏幕尺寸自适应）"""
        w, h = slef.d.window_size()
        slef.d.swipe(w * 0.5, h * 0.7, w * 0.5, h * 0.3, duration=0.2)

    def start_main_window(self):
        """重置测试环境到初始状态"""
        self.start_app(self.app_identifier)
        time.sleep(3)
    def reset_to_main_window(self):
        """重置测试环境到初始状态"""
        self.d.app_stop_all()
        self.d.press('home')
        self.start_app(self.app_identifier)
        time.sleep(3)
        return self.get_current_window()

    def reset_to_before_window(self,current,swipe_count):
        """在异常情况时重置到操作元素前环境，最好的做法是记忆元素操作路径来恢复环境，缺点是在多层操作元素时太耗时，
        当前用activity取代  后续在考虑fragement 处理方式"""
        self.d.app_stop_all()
        self.d.press('home')
        self.d.app_start(current.split('/')[0],current.split('/')[1])
        time.sleep(3)
        self.handle_swipe_with_times(swipe_count)
        return self.get_current_window()

    def operate_with_recovery(self,element, current_depth,current_swipe_count):
        """递归操作元素，操作完回到操作前页面"""
        before_window = self.get_current_window()
        try:
            print(f"\n[Depth {current_depth}] 操作元素: {element.info}")

            # 执行元素操作
            self.operate_element_based_on_type(element)
            time.sleep(2)  # 等待界面稳定

            # 继续递归处理子元素
            if current_depth < self.max_depth:
                self.handle_current_level(current_depth + 1)

            # 操作后状态检查
            if self.get_current_window() != before_window:
                self.d.press('back')
                time.sleep(1)
            if self.get_current_window() != before_window:
                self.reset_to_before_window(before_window, current_swipe_count)
        except Exception as e:
            print(f"操作失败: {str(e)}")
            self.reset_to_before_window(before_window,current_swipe_count)


    def handle_current_level(self, current_depth):
        """处理当前层级的所有元素"""
        need_swipe=True
        current_swipe_count=0

        print(f"\n{'=' * 20} 开始遍历深度 {current_depth} {'=' * 20}")
        while need_swipe and current_swipe_count <5:
            before = self.get_page_signature()
            elements = self.get_all_interactable_elements()
            if len(elements)==0:
                continue
            for element in elements:
                if element not in self.visited_elements:
                    self.visited_elements.add(element)
                    self.operate_with_recovery(element, current_depth,current_swipe_count)
                else:
                    print("element operate already")

            self.handle_swipe_with_times(1)
            current_swipe_count = current_swipe_count + 1
            after=self.get_page_signature()
            if after==before:
                break




    def handle_swipe_with_times(self,times):
        """处理需要滑动的内容"""
        swipe_count = 0
        while swipe_count < times:
            self.d.swipe(0.5, 0.8, 0.5, 0.2, duration=0.5)
            time.sleep(1.5)
            swipe_count=swipe_count+1


    def draw_bbox_multi(self, img_path, output_path, elem_list, record_mode=False, dark_mode=False):
        """标记当前页面元素"""
        imgcv = cv2.imread(img_path)
        count = 1
        for elem in elem_list:
            try:

                left, top = elem.info['bounds']['left'], elem.info['bounds']['top']
                right, bottom = elem.info['bounds']['right'], elem.info['bounds']['bottom']
                label = str(count)
                if record_mode:
                    if elem.info['clickable'] :
                        color = (250, 0, 0)
                    elif elem.info['focusabl'] :
                        color = (0, 0, 250)
                    else:
                        color = (0, 250, 0)
                    imgcv = ps.putBText(imgcv, label, text_offset_x=(left + right) // 2 + 10,
                                        text_offset_y=(top + bottom) // 2 + 10,
                                        vspace=10, hspace=10, font_scale=1, thickness=2, background_RGB=color,
                                        text_RGB=(255, 250, 250), alpha=0.5)
                else:
                    text_color = (10, 10, 10) if dark_mode else (255, 250, 250)
                    bg_color = (255, 250, 250) if dark_mode else (10, 10, 10)
                    imgcv = ps.putBText(imgcv, label, text_offset_x=(left + right) // 2 + 10,
                                        text_offset_y=(top + bottom) // 2 + 10,
                                        vspace=10, hspace=10, font_scale=1, thickness=2, background_RGB=bg_color,
                                        text_RGB=text_color, alpha=0.5)
            except Exception as e:
                self.print_with_color(f"ERROR: An exception occurs while labeling the image\n{e}", "red")
            count += 1
        cv2.imwrite(output_path, imgcv)
        return imgcv
    def print_with_color(self,text: str, color=""):
        if color == "red":
            print(Fore.RED + text)
        elif color == "green":
            print(Fore.GREEN + text)
        elif color == "yellow":
            print(Fore.YELLOW + text)
        elif color == "blue":
            print(Fore.BLUE + text)
        elif color == "magenta":
            print(Fore.MAGENTA + text)
        elif color == "cyan":
            print(Fore.CYAN + text)
        elif color == "white":
            print(Fore.WHITE + text)
        elif color == "black":
            print(Fore.BLACK + text)
        else:
            print(text)
        print(Style.RESET_ALL)
if __name__ == '__main__':
    # 配置测试文本
    test_texts = [
        "测试", "自动化", "hello",
        "12345", "搜索", "android",
        "输入测试", "QA", "test"
    ]

    # 初始化遍历器
    traverser = AndroidUITraverser(
        device_serial='emulator-5554',  # 替换为你的设备序列号
        output_dir='../ui_traversal_output',
        test_texts=test_texts,
        app_identifier='com.android.settings',
        max_depth=5


    )

    # 方式1: 直接遍历当前界面
    # traverser.traverse_app(max_depth=2)

    # 方式2: 通过包名启动并遍历
    # traverser.traverse_app('com.android.settings', max_depth=2)

    # 方式3: 通过应用名启动并遍历
    #traverser.traverse_app_with_depth('com.android.settings', max_depth=2)
    traverser.start_main_window()
    traverser.handle_current_level(1)
    print("\n遍历完成，输出保存在:", os.path.abspath(traverser.output_dir))


    #traverser.traverse_app('设置')  # 使用应用名称
    # traverser.traverse_app('com.android.settings')  # 使用包名

    #传统的测试程序需要测试人员输出清晰准确的指令才能运行 该程序是传统测试的基础让植入AI大模型能力。让AI赋能自动化测试
    #AI赋能的自动化测试框架，在传统测试的基础上引入了大模型的自然语言理解、模糊指令转换、图片文字识别、测试数据生成（当前搜索框、文本框输入内容推荐）、测试标准迭代（黑屏、白屏、无响应、历史重要element是否失常、是否存在文字遮挡、图片一致性）。