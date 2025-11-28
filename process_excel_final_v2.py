#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Excel文件整理脚本 - 最终优化版
规则：
1. 只处理test.xlsx中第二组数据（列6、7、8），不包含aa.xlsx的内容
2. 问题拆分：只拆分用" / "（空格+斜杠+空格）或行首的"/"分隔的问题
3. 保持同一场景、语义连贯的问题在一起
4. 智能处理补充建议
"""

import pandas as pd
from openpyxl.styles import Alignment, Font
import re

def split_question_smart(question):
    """
    智能拆分问题
    规则：
    - 只拆分明确作为分隔符的"/"（如" / "或行首的"/"）
    - 不拆分编号中的"/"（如"2002/24/EC"）
    - 保持语义连贯
    """
    if pd.isna(question) or not isinstance(question, str):
        return [question]

    question = str(question).strip()
    if not question:
        return [question]

    # 检测是否有明确的分隔符"/"
    # 1. " / "（前后有空格）
    # 2. 行首或句首的"/"或"-"

    # 先尝试按" / "分割
    if ' / ' in question:
        parts = [p.strip() for p in question.split(' / ')]
        questions = []
        for part in parts:
            if part:
                if not part.endswith('？') and not part.endswith('?'):
                    part += '？'
                questions.append(part)
        return questions if questions else [question]

    # 检查是否有以"/"或"-"开头的行（表示列表项）
    lines = question.split('\n')
    if len(lines) > 1:
        # 检查是否是列表格式
        list_items = []
        current_item = []

        for line in lines:
            line = line.strip()
            if line.startswith('/') or line.startswith('-') or re.match(r'^\d+[\.\)、]', line):
                # 新的列表项
                if current_item:
                    list_items.append('\n'.join(current_item))
                current_item = [line]
            else:
                # 继续当前项
                if line:
                    if current_item:
                        current_item.append(line)
                    else:
                        # 前置说明文字
                        current_item.append(line)

        # 添加最后一项
        if current_item:
            list_items.append('\n'.join(current_item))

        # 如果识别到多个列表项，作为独立问题
        if len(list_items) > 1:
            questions = []
            for item in list_items:
                item = item.strip()
                if item:
                    # 移除列表标记
                    item = re.sub(r'^[\-/]\s*', '', item)
                    item = re.sub(r'^\d+[\.\)、]\s*', '', item)
                    if not item.endswith('？') and not item.endswith('?'):
                        item += '？'
                    questions.append(item)
            return questions if questions else [question]

    # 否则保持完整
    return [question]

def analyze_supplement(supplement):
    """
    分析补充建议的类型
    """
    if pd.isna(supplement) or supplement == '':
        return ('none', '')

    supplement_str = str(supplement).strip()

    # 部分补充关键词
    partial_keywords = [
        '补充', '增加', '添加', '还需要', '建议', '需要加上',
        '可以提及', '建议提到', '增加说明', '优化', '多问题回复'
    ]

    # 检查前100个字符
    is_partial = any(keyword in supplement_str[:100] for keyword in partial_keywords)

    # 完整回复标志
    complete_indicators = ['感谢', '您好', '关于', '抱歉', '非常理解']
    is_complete = (
        len(supplement_str) > 80 and
        any(indicator in supplement_str[:150] for indicator in complete_indicators) and
        not is_partial
    )

    if is_complete:
        return ('complete', supplement_str)
    elif is_partial:
        return ('partial', supplement_str)
    else:
        return ('complete', supplement_str)

def merge_answer_intelligent(original_answer, supplement):
    """
    智能合并原回答和补充建议
    """
    supplement_type, supplement_content = analyze_supplement(supplement)

    if supplement_type == 'none':
        return str(original_answer).strip() if not pd.isna(original_answer) else ''

    if supplement_type == 'partial':
        original_str = str(original_answer).strip() if not pd.isna(original_answer) else ''

        # 提取补充的具体内容
        if '：' in supplement_content:
            parts = supplement_content.split('：', 1)
            if len(parts) > 1:
                supplement_content = parts[1].strip()
        elif ':' in supplement_content:
            parts = supplement_content.split(':', 1)
            if len(parts) > 1:
                supplement_content = parts[1].strip()

        # 合并
        if original_str:
            return f"{original_str}\n\n{supplement_content}"
        else:
            return supplement_content

    else:  # complete
        return supplement_content

def process_test_file(test_df):
    """
    处理test.xlsx中第二组数据（列6、7、8）
    """
    print("\n开始处理test.xlsx数据...")

    questions = []
    answers = []

    # 跳过标题行
    for idx, row in test_df.iloc[1:].iterrows():
        question = row[6] if len(row) > 6 else ''
        answer = row[7] if len(row) > 7 else ''
        supplement = row[8] if len(row) > 8 else ''

        # 跳过空行
        if pd.isna(question) or str(question).strip() == '':
            continue

        print(f"\n--- 处理行 {idx} ---")
        print(f"原问题: {str(question)[:100]}{'...' if len(str(question)) > 100 else ''}")

        # 智能拆分问题
        split_questions = split_question_smart(question)
        print(f"拆分后问题数: {len(split_questions)}")
        for sq in split_questions:
            print(f"  - {str(sq)[:80]}{'...' if len(str(sq)) > 80 else ''}")

        # 智能合并回答
        final_answer = merge_answer_intelligent(answer, supplement)
        supplement_type, _ = analyze_supplement(supplement)
        print(f"补充类型: {supplement_type}")
        print(f"回答前80字: {final_answer[:80]}...")

        # 为每个拆分的问题分配回答
        for q in split_questions:
            if q and str(q).strip():
                questions.append(str(q).strip())
                answers.append(final_answer)

    print(f"\n处理完成！共生成 {len(questions)} 条问答对")
    return questions, answers

def save_to_excel_formatted(questions, answers, output_filepath):
    """保存到Excel并格式化"""
    print(f"\n正在保存到文件: {output_filepath}")

    df = pd.DataFrame({
        '问题': questions,
        '回答': answers
    })

    with pd.ExcelWriter(output_filepath, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')

        workbook = writer.book
        worksheet = writer.sheets['Sheet1']

        # 设置列宽
        worksheet.column_dimensions['A'].width = 80
        worksheet.column_dimensions['B'].width = 100

        # 设置自动换行和对齐
        for row in worksheet.iter_rows(min_row=2, max_row=len(questions)+1):
            for cell in row:
                cell.alignment = Alignment(wrap_text=True, vertical='top')

        # 设置标题行格式
        for cell in worksheet[1]:
            cell.font = Font(bold=True, size=12)
            cell.alignment = Alignment(horizontal='center', vertical='center')

    print(f"保存成功！共保存 {len(questions)} 条问答对")

def main():
    """主函数"""
    print("=" * 80)
    print("Excel文件整理工具 - 最终优化版")
    print("=" * 80)

    test_file = "/home/yzh/AI客服/鉴权/test.xlsx"
    output_file = "/home/yzh/AI客服/鉴权/test2.xlsx"

    try:
        print(f"\n读取文件: {test_file}")
        test_df = pd.read_excel(test_file, header=None)
        print(f"文件行数: {len(test_df)}")
        print(f"文件列数: {len(test_df.columns)}")

        # 处理数据
        questions, answers = process_test_file(test_df)

        # 保存结果
        save_to_excel_formatted(questions, answers, output_file)

        # 显示示例
        print("\n" + "=" * 80)
        print("生成结果示例（前5条）:")
        print("=" * 80)
        for i in range(min(5, len(questions))):
            print(f"\n{i+1}. 问题: {questions[i][:100]}{'...' if len(questions[i]) > 100 else ''}")
            print(f"   回答: {answers[i][:120]}...")

        print("\n" + "=" * 80)
        print("处理完成！")
        print(f"输出文件: {output_file}")
        print(f"总问答对数: {len(questions)}")
        print("=" * 80)

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
