#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Excel文件整理脚本 - 最终版
规则：
1. 只处理test.xlsx中第二组数据（列6、7、8），不包含aa.xlsx的内容
2. 问题拆分：只拆分用"/"分隔的问题（表示不同场景）
3. 保持同一场景、语义连贯的问题在一起
4. 智能处理补充建议（部分补充 vs 完整替换）
"""

import pandas as pd
from openpyxl.styles import Alignment, Font
import re

def split_question_by_slash(question):
    """
    只按"/"分隔符拆分问题
    保持同一场景、语义连贯的问题在一起
    """
    if pd.isna(question) or not isinstance(question, str):
        return [question]

    question = str(question).strip()
    if not question:
        return [question]

    # 只按"/"分割（表示不同场景的问题）
    if '/' in question:
        parts = [p.strip() for p in question.split('/')]
        questions = []
        for part in parts:
            if part:
                # 确保问题以问号结尾
                if not part.endswith('？') and not part.endswith('?'):
                    part += '？'
                questions.append(part)
        return questions if questions else [question]
    else:
        # 不包含"/"，保持完整
        return [question]

def analyze_supplement(supplement):
    """
    分析补充建议的类型
    返回: ('partial', supplement) 或 ('complete', supplement) 或 ('none', '')
    """
    if pd.isna(supplement) or supplement == '':
        return ('none', '')

    supplement_str = str(supplement).strip()

    # 判断是否为部分补充（包含关键词）
    partial_keywords = [
        '补充', '增加', '添加', '还需要', '建议', '需要加上',
        '可以提及', '建议提到', '增加说明', '优化'
    ]

    # 检查前50个字符是否包含补充关键词
    is_partial = any(keyword in supplement_str[:80] for keyword in partial_keywords)

    # 判断是否为完整回复
    complete_indicators = ['感谢', '您好', '关于', '抱歉', '非常理解']
    is_complete = (
        len(supplement_str) > 80 and
        any(indicator in supplement_str[:100] for indicator in complete_indicators) and
        not is_partial
    )

    if is_complete:
        return ('complete', supplement_str)
    elif is_partial:
        return ('partial', supplement_str)
    else:
        # 默认为完整替换（较长的内容）
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

        # 提取补充的具体内容（去掉"补充："、"增加："等前缀）
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
    只处理test.xlsx中第二组数据（列6、7、8）
    """
    print("\n开始处理test.xlsx数据...")

    questions = []
    answers = []

    # 跳过标题行（第一行）
    for idx, row in test_df.iloc[1:].iterrows():
        # 只处理第二组数据（列6、7、8）
        question = row[6] if len(row) > 6 else ''
        answer = row[7] if len(row) > 7 else ''
        supplement = row[8] if len(row) > 8 else ''

        # 跳过空行
        if pd.isna(question) or str(question).strip() == '':
            continue

        print(f"\n--- 处理行 {idx} ---")
        print(f"原问题: {str(question)[:100]}...")

        # 按"/"拆分问题（只拆分不同场景的问题）
        split_questions = split_question_by_slash(question)
        print(f"拆分后问题数: {len(split_questions)}")
        for sq in split_questions:
            print(f"  - {str(sq)[:80]}...")

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

    # 创建DataFrame
    df = pd.DataFrame({
        '问题': questions,
        '回答': answers
    })

    # 保存到Excel
    with pd.ExcelWriter(output_filepath, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')

        # 获取工作表
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
    print("Excel文件整理工具 - 最终版")
    print("=" * 80)

    # 文件路径
    test_file = "/home/yzh/AI客服/鉴权/test.xlsx"
    output_file = "/home/yzh/AI客服/鉴权/test2.xlsx"

    try:
        # 读取test.xlsx文件
        print(f"\n读取文件: {test_file}")
        test_df = pd.read_excel(test_file, header=None)
        print(f"文件行数: {len(test_df)}")
        print(f"文件列数: {len(test_df.columns)}")

        # 处理数据（只处理第二组数据：列6、7、8）
        questions, answers = process_test_file(test_df)

        # 保存结果
        save_to_excel_formatted(questions, answers, output_file)

        # 显示示例
        print("\n" + "=" * 80)
        print("生成结果示例（前10条）:")
        print("=" * 80)
        for i in range(min(10, len(questions))):
            print(f"\n{i+1}. 问题: {questions[i][:80]}...")
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
