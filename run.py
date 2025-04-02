import argparse
import os

from libs.MobileAgent.AndroidUITraverser import AndroidUITraverser
def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sn", type=str, default=None)
    parser.add_argument("--depth", type=int ,default=3)
    parser.add_argument("--app", type=str,help="app name")
    parser.add_argument("--out", type=str, help="output dir")
    args = parser.parse_args()
    return args

if __name__ == '__main__':
    # 配置测试文本
    args = get_args()
    test_texts = [
        "测试", "自动化", "hello",
        "12345", "搜索", "android",
        "输入测试", "QA", "test"
    ]
    # 初始化遍历器
    traverser = AndroidUITraverser(
        device_serial=args.sn,  # 替换为你的设备序列号
        output_dir=args.out,
        test_texts=test_texts,
        app_identifier=args.app,
        max_depth=args.depth #配置遍历层数


    )

    # 方式1: 直接遍历当前界面
    # traverser.traverse_app(max_depth=2)

    # 方式2: 通过包名启动并遍历
    # traverser.traverse_app('com.android.settings', max_depth=2)

    # 方式3: 通过应用名启动并遍历
    #traverser.traverse_app_with_depth('com.android.settings', max_depth=2)
    main_window=traverser.start_main_window()
    traverser.handle_current_level(1)
    print("\n遍历完成，输出保存在:", os.path.abspath(traverser.output_dir))