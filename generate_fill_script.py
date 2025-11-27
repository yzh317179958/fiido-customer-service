#!/usr/bin/env python3
"""
生成Coze知识库自动填充的JavaScript脚本 v2
修复：使用IIFE避免变量重复声明，修正填写逻辑
"""

import pandas as pd
import json

def escape_js_string(s):
    """转义JavaScript字符串"""
    if pd.isna(s):
        return ""
    s = str(s)
    s = s.replace('\\', '\\\\')
    s = s.replace('"', '\\"')
    s = s.replace('\n', '\\n')
    s = s.replace('\r', '\\r')
    s = s.replace('\t', '\\t')
    return s

def generate_js_script(excel_path, output_js_path):
    """读取Excel并生成JavaScript脚本"""
    print(f"📖 正在读取Excel: {excel_path}")

    # 读取Excel（跳过标题行）
    df = pd.read_excel(excel_path)
    data_rows = df.iloc[0:]  # 从索引0开始

    total_rows = len(data_rows)
    print(f"✅ 读取成功！共 {total_rows} 行数据")

    # 生成JavaScript数组
    js_data = []
    for _, row in data_rows.iterrows():
        question = escape_js_string(row['问题'])
        answer = escape_js_string(row['问题回复'])
        js_data.append(f'    ["{question}", "{answer}"]')

    js_data_str = ',\n'.join(js_data)

    # 生成完整的JavaScript脚本
    js_script = f'''/**
 * Coze知识库自动填充脚本 v2.0
 *
 * 使用方法:
 * 1. 确保已在Coze知识库页面
 * 2. 按F12打开浏览器控制台
 * 3. 复制整个脚本粘贴到控制台
 * 4. 按Enter运行
 * 5. 等待自动填充完成
 * 6. 手动点击Confirm提交
 */

(async function() {{
  const DATA = [
{js_data_str}
  ];

  console.clear();
  console.log('🚀 Coze知识库自动填充工具 v2.0');
  console.log('=''.repeat(60));
  console.log(`📊 共 ${{DATA.length}} 行数据待填充`);
  console.log('=''.repeat(60));

  let successCount = 0;
  let failCount = 0;

  for (let i = 0; i < DATA.length; i++) {{
    const [question, answer] = DATA[i];
    const rowNum = i + 1;

    console.log(`\\n[${{rowNum}}/${{DATA.length}}] 正在处理...`);
    console.log(`  问题: ${{question.substring(0, 50)}}...`);

    try {{
      // 步骤1: 点击"Add value"按钮添加新行
      let addButton = null;

      // 尝试多种方式查找"Add value"按钮
      const allButtons = document.querySelectorAll('button');
      for (const btn of allButtons) {{
        if (btn.textContent.includes('Add value') ||
            btn.textContent.includes('add') ||
            btn.textContent.includes('添加')) {{
          addButton = btn;
          break;
        }}
      }}

      if (!addButton) {{
        console.error('  ❌ 找不到"Add value"按钮');
        failCount++;
        break;
      }}

      // 点击按钮
      addButton.click();
      console.log('  ✓ 已点击"Add value"按钮');

      // 等待新行加载完成
      await new Promise(resolve => setTimeout(resolve, 800));

      // 步骤2: 查找新添加的输入框
      const allInputs = document.querySelectorAll('input, textarea');

      if (allInputs.length < 2) {{
        console.error(`  ❌ 输入框不足 (找到${{allInputs.length}}个)`);
        failCount++;
        continue;
      }}

      // 获取最后添加的两个输入框
      const questionInput = allInputs[allInputs.length - 2];
      const answerInput = allInputs[allInputs.length - 1];

      // 步骤3: 填充数据
      // 清空并填写问题
      questionInput.value = '';
      questionInput.focus();
      questionInput.value = question;

      // 触发输入事件
      const inputEvent = new Event('input', {{ bubbles: true, cancelable: true }});
      const changeEvent = new Event('change', {{ bubbles: true, cancelable: true }});
      questionInput.dispatchEvent(inputEvent);
      questionInput.dispatchEvent(changeEvent);

      // 清空并填写答案
      answerInput.value = '';
      answerInput.focus();
      answerInput.value = answer;
      answerInput.dispatchEvent(inputEvent);
      answerInput.dispatchEvent(changeEvent);

      console.log('  ✅ 数据填写完成');
      successCount++;

      // 短暂延迟再处理下一行
      await new Promise(resolve => setTimeout(resolve, 500));

    }} catch (error) {{
      console.error(`  ❌ 填写失败: ${{error.message}}`);
      console.error(error);
      failCount++;

      // 询问是否继续
      if (failCount >= 3) {{
        console.error('\\n⚠️  连续失败3次，脚本已暂停');
        console.error('请检查页面状态，然后刷新页面重新运行');
        break;
      }}
    }}
  }}

  // 最终统计
  console.log('\\n' + '=''.repeat(60));
  console.log('🎉 填充任务完成！');
  console.log('=''.repeat(60));
  console.log(`✅ 成功: ${{successCount}} 行`);
  console.log(`❌ 失败: ${{failCount}} 行`);
  console.log(`📊 总计: ${{DATA.length}} 行`);
  console.log('\\n⚠️  请手动检查数据后点击"Confirm"按钮提交');
  console.log('=''.repeat(60));

}})();
'''

    # 保存到文件
    with open(output_js_path, 'w', encoding='utf-8') as f:
        f.write(js_script)

    print(f"\n✅ JavaScript脚本已生成: {output_js_path}")
    print(f"📄 共 {total_rows} 行数据")
    print(f"📏 文件大小: {len(js_script)} 字节")
    print("\n使用方法:")
    print("1. 在Firefox打开Coze知识库页面")
    print("2. 按F12打开控制台")
    print("3. 复制脚本全部内容")
    print("4. 粘贴到控制台并按Enter")
    print("5. 等待自动填充完成")

if __name__ == "__main__":
    excel_path = "/home/yzh/AI客服/鉴权/aa.xlsx"
    output_js_path = "/home/yzh/AI客服/鉴权/fill_coze_auto.js"

    generate_js_script(excel_path, output_js_path)
