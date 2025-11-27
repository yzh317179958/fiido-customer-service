#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成完整的 v13.0 脚本（141行数据）
基于更新后的 aa.xlsx
"""

import pandas as pd
import json

# 读取 Excel 文件
df = pd.read_excel('/home/yzh/AI客服/鉴权/aa.xlsx')

# 提取问题和答案列
questions = df['问题'].tolist()
answers = df['问题回复'].tolist()

# 生成 fillData 数组
fill_data = []
for q, a in zip(questions, answers):
    # 处理 NaN 值
    q_text = str(q) if pd.notna(q) else ""
    a_text = str(a) if pd.notna(a) else ""

    fill_data.append({
        "question": q_text,
        "answer": a_text
    })

print(f"✅ 读取到 {len(fill_data)} 行数据")

# 检查是否有空值
empty_count = sum(1 for item in fill_data if not item['question'].strip() or not item['answer'].strip())
if empty_count > 0:
    print(f"⚠️  警告: 发现 {empty_count} 行有空值")
    for i, item in enumerate(fill_data, 1):
        if not item['question'].strip() or not item['answer'].strip():
            print(f"   第 {i} 行: 问题='{item['question']}', 答案='{item['answer']}'")

# 生成 JavaScript 代码
js_template = '''/**
 * v13.0 完整版: 基于创建文本节点的自动填充脚本
 * 数据来源: aa.xlsx (已更新，列139已填充)
 * 总行数: ''' + str(len(fill_data)) + '''
 */

(function() {
  console.clear();
  console.log('🚀 Coze知识库自动填充工具 v13.0 完整版\\n');
  console.log('📊 数据行数: ''' + str(len(fill_data)) + '''\\n');

  // 完整的141行数据
  var fillData = ''' + json.dumps(fill_data, ensure_ascii=False, indent=2) + ''';

  var currentIndex = 0;
  var addButton = document.querySelector('button.semi-button-primary');

  if (!addButton) {
    console.error('❌ 找不到 Add value 按钮');
    return;
  }

  console.log('✅ 找到 Add value 按钮');
  console.log('⏳ 准备开始自动填充...\\n');

  // 填充单个输入框（创建文本节点 + innerText）
  function fillWithTextNode(element, text, label) {
    console.log('  ' + label + ':');

    // 步骤1: 如果没有文本节点，创建一个
    if (element.childNodes.length === 0) {
      console.log('    1️⃣ 创建文本节点');
      var textNode = document.createTextNode('');
      element.appendChild(textNode);
      console.log('    ✓ 文本节点已创建');
    }

    // 步骤2: 填充内容
    console.log('    2️⃣ 填充内容:', text.substring(0, 30) + (text.length > 30 ? '...' : ''));
    element.innerText = text;

    // 步骤3: 触发事件
    console.log('    3️⃣ 触发事件');
    var events = [
      new FocusEvent('focus', { bubbles: true }),
      new InputEvent('input', {
        bubbles: true,
        cancelable: true,
        inputType: 'insertText',
        data: text
      }),
      new Event('change', { bubbles: true }),
      new FocusEvent('blur', { bubbles: true })
    ];

    events.forEach(function(event) {
      element.dispatchEvent(event);
    });

    console.log('    ✅ 完成');
  }

  // 填充下一行
  function fillNextRow() {
    if (currentIndex >= fillData.length) {
      console.log('\\n' + '='.repeat(60));
      console.log('✅ 全部完成！共填充 ' + fillData.length + ' 行');
      console.log('='.repeat(60));
      console.log('\\n🔍 请检查:');
      console.log('  1. 页面上是否显示所有数据？');
      console.log('  2. ⭐⭐⭐ Confirm 按钮是否可点击？');
      console.log('  3. 如果可以，请手动点击 Confirm 提交');
      console.log('='.repeat(60));
      return;
    }

    var data = fillData[currentIndex];
    var rowNumber = currentIndex + 1;

    console.log('\\n' + '─'.repeat(60));
    console.log('📝 填充第 ' + rowNumber + '/' + fillData.length + ' 行');
    console.log('─'.repeat(60));

    // 点击 Add value 按钮
    addButton.click();

    // 等待新行生成
    setTimeout(function() {
      var rows = document.querySelectorAll('tr.semi-table-row');

      if (rows.length === 0) {
        console.error('❌ 找不到表格行');
        return;
      }

      var lastRow = rows[rows.length - 1];
      var cells = lastRow.querySelectorAll('td.semi-table-row-cell');

      if (cells.length < 2) {
        console.error('❌ 单元格不足');
        return;
      }

      var questionCell = cells[0];
      var answerCell = cells[1];

      var questionDiv = questionCell.querySelector('div.text-content');
      var answerDiv = answerCell.querySelector('div.text-content');

      if (!questionDiv || !answerDiv) {
        console.error('❌ 找不到输入框');
        return;
      }

      // 顺序填充问题和答案
      fillWithTextNode(questionDiv, data.question, '📝 问题框');

      setTimeout(function() {
        fillWithTextNode(answerDiv, data.answer, '📝 答案框');

        setTimeout(function() {
          console.log('✅ 第 ' + rowNumber + ' 行填充完成');

          // 继续下一行
          currentIndex++;
          fillNextRow();

        }, 300); // 答案填充后等待300ms

      }, 300); // 问题填充后等待300ms

    }, 800); // 点击按钮后等待800ms
  }

  // 开始执行
  setTimeout(function() {
    console.log('🚀 开始自动填充...\\n');
    fillNextRow();
  }, 1000);

  console.log('⏳ 1秒后开始自动填充...');
  console.log('⚠️  预计耗时: ' + Math.ceil(fillData.length * 1.4 / 60) + ' 分钟');

})();
'''

# 保存到文件
output_file = '/home/yzh/AI客服/鉴权/fill_coze_v13_full.js'
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(js_template)

print(f"\n✅ 脚本已生成: {output_file}")
print(f"📊 数据行数: {len(fill_data)}")
print(f"⏱️  预计耗时: {len(fill_data) * 1.4 / 60:.1f} 分钟")
print("\n使用方法:")
print("1. 在 Firefox 浏览器打开 Coze 知识库页面")
print("2. 按 F12 打开开发者工具控制台")
print("3. 复制整个脚本内容到控制台并回车执行")
print("4. 等待自动填充完成后，手动点击 Confirm 按钮提交")
