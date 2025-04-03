import uiautomator2 as u2
import pytest
import time
from typing import Optional
from config.contant import DS_API_KEY
from libs.MobileAgent.api import inference_chat
class SettingsGoogleTest:
    def __init__(self, device_serial: Optional[str] = None):
        """
        初始化设备连接
        :param device_serial: 设备序列号，如果是USB连接的单设备可以为None
        """
        self.d = u2.connect(device_serial) if device_serial else u2.connect()
        self.d.implicitly_wait(10)  # 设置隐式等待时间

    def open_settings(self):
        """打开系统设置"""
        print("打开系统设置")
        self.d.app_stop_all()
        self.d.app_start("com.android.settings")
        time.sleep(3)

        return True


    def navigate_to_google_settings(self):
        """导航到Google设置"""
        print("尝试找到Google设置")

        # 不同设备可能有不同的Google设置入口
        google_entries = [
            {"text": "Google"},
            {"text": "Google Settings"},
            {"text": "Google", "className": "android.widget.TextView"},
            {"textContains": "Google"}
        ]

        for entry in google_entries:
            if self.d(**entry).exists:
                print(f"找到Google入口: {entry}")
                element_info=self.d(**entry).info
                print(element_info)
                self.d(**entry).click()
                time.sleep(3)
                current_ui_tree=self.d.dump_hierarchy(compressed=True)
                time.sleep(1)
                print(current_ui_tree)
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                self.d.screenshot(f"settings_test_failure_{timestamp}.png")
                res=inference_chat(f" 我现在操作的元素信息时{element_info}\n 操作后UI树是{current_ui_tree} 请判断是否异常",DS_API_KEY)
                time.sleep(2)
                print(res)
                return True

        # 如果没找到，尝试滚动查找
        return False

    def verify_google_settings_page(self):
        """验证是否在Google设置页面"""
        indicators = [
            {"text": "Google"},
            {"textContains": "Google Account"},
            {"textContains": "Google services"}
        ]

        for indicator in indicators:
            if self.d(**indicator).exists:
                print(f"确认在Google设置页面，标识: {indicator}")
                return True
        return False

    def press_back_and_verify(self):
        """按下返回键并验证是否回到主设置页面"""
        print("按下返回键")
        self.d.press("back")
        time.sleep(2)

        # 验证是否返回主设置
        if self.d(text="Settings").exists or self.d(description="Settings").exists:
            print("成功返回主设置页面")
            return True

        print("未能返回主设置页面")
        return False

    def run_test(self):
        """执行完整测试流程"""
        try:
            # 1. 打开设置
            if not self.open_settings():
                raise Exception("无法打开设置应用")

            # 2. 导航到Google设置
            if not self.navigate_to_google_settings():
                raise Exception("无法导航到Google设置")

            print("测试通过!")
            return True

        except Exception as e:
            print(f"测试失败: {str(e)}")
            # 失败时截图
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            self.d.screenshot(f"settings_test_failure_{timestamp}.png")
            return False
        finally:
            # 清理: 回到主页
            self.d.press("home")


if __name__ == "__main__":
    # 使用示例
    tester = SettingsGoogleTest()  # 自动连接设备

    # 运行测试
    test_result = tester.run_test()

    # 输出结果
    print("\n测试结果:", "通过" if test_result else "失败")

    # 退出
    exit(0 if test_result else 1)