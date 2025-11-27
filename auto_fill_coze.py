#!/usr/bin/env python3
"""
自动填写Coze知识库问答数据
从Excel读取数据并自动填充到网页表单
"""

import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
import time

def connect_to_existing_firefox():
    """连接到已打开的Firefox浏览器"""
    # Firefox需要启用远程调试
    # 请先在Firefox地址栏输入: about:config
    # 搜索并设置: marionette.enabled = true

    # 使用Firefox的远程调试端口
    firefox_options = Options()
    firefox_options.add_argument('--marionette-port')
    firefox_options.add_argument('2828')

    # 连接到现有的Firefox会话
    driver = webdriver.Firefox(options=firefox_options)
    return driver

def fill_data_from_excel(excel_path):
    """从Excel读取数据并填充到网页"""
    # 1. 读取Excel数据（跳过标题行）
    print(f"📖 正在读取Excel文件: {excel_path}")
    df = pd.read_excel(excel_path)

    # 跳过标题行，只处理数据行
    data_rows = df.iloc[0:]  # 从第1行开始（索引0）
    total_rows = len(data_rows)

    print(f"✅ 读取成功！共 {total_rows} 行数据需要填写")
    print(f"列名: {list(df.columns)}")
    print("\n" + "="*60)

    # 2. 连接到已打开的Firefox浏览器
    print("🌐 正在连接到Firefox浏览器...")
    print("⚠️  请确保Firefox已打开目标网页:")
    print("   https://www.coze.com/space/.../upload")

    input("\n按Enter键继续...")

    try:
        # 创建新的Firefox实例（会打开新窗口）
        # 注意：需要手动切换到已有的标签页
        driver = webdriver.Firefox()

        print("\n✅ 浏览器已启动")
        print("⚠️  请手动切换到Coze知识库的标签页，然后按Enter继续...")
        input()

        # 3. 逐行填写数据
        print(f"\n🚀 开始自动填写数据...")
        print("="*60)

        for index, row in data_rows.iterrows():
            row_num = index + 1
            question = str(row['问题'])
            answer = str(row['问题回复'])

            print(f"\n[{row_num}/{total_rows}] 正在填写:")
            print(f"  问题: {question[:50]}...")
            print(f"  回复: {answer[:50]}...")

            try:
                # 等待"Add value"按钮出现
                add_button = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//button[contains(., 'Add value')]"))
                )

                # 点击"Add value"按钮添加新行
                add_button.click()
                time.sleep(0.5)  # 等待新行加载

                # 查找所有输入框
                # 第1列（Index）- 问题
                # 第2列（String）- 问题回复

                # 方法1: 通过列序号定位输入框
                # 查找所有input元素
                inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='text'], textarea")

                if len(inputs) >= 2:
                    # 最后两个输入框应该是新添加的行
                    question_input = inputs[-2]  # 倒数第二个：问题
                    answer_input = inputs[-1]    # 最后一个：问题回复

                    # 填写数据
                    question_input.clear()
                    question_input.send_keys(question)

                    answer_input.clear()
                    answer_input.send_keys(answer)

                    print(f"  ✅ 填写完成")
                else:
                    print(f"  ❌ 错误: 找不到足够的输入框")
                    break

                # 短暂延迟，避免操作太快
                time.sleep(0.3)

            except Exception as e:
                print(f"  ❌ 填写失败: {str(e)}")
                print("  继续下一行...")
                continue

        print("\n" + "="*60)
        print(f"🎉 所有数据填写完成！共填写 {total_rows} 行")
        print("⚠️  请手动检查并点击\"Confirm\"按钮提交数据")
        print("\n浏览器窗口保持打开，请手动关闭")

        # 不自动关闭浏览器，让用户检查
        input("\n按Enter键关闭脚本（浏览器窗口会保持打开）...")

    except Exception as e:
        print(f"\n❌ 发生错误: {str(e)}")
        print("请检查:")
        print("1. Firefox浏览器是否已打开目标网页")
        print("2. 网页是否加载完成")
        print("3. 是否需要先登录Coze平台")

    finally:
        # 不关闭driver，保持浏览器打开
        print("\n脚本执行完毕")

if __name__ == "__main__":
    excel_path = "/home/yzh/AI客服/鉴权/aa.xlsx"
    fill_data_from_excel(excel_path)
