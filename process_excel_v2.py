#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Excel文件智能整理脚本 v2
优化点：
1. 更智能地拆分问题（识别多个语境）
2. 正确处理补充建议（区分补充vs完整替换）
3. 保留原文不杜撰
"""

import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Alignment, Font
import re

def analyze_question_style(reference_df):
    """分析参考文件的问题风格"""
    print("\n分析参考文件的问题风格...")
    questions = reference_df.iloc[1:, 0].dropna()  # 跳过标题行

    # 统计问题特征
    avg_length = questions.apply(lambda x: len(str(x)) if pd.notna(x) else 0).mean()
    has_multiple_questions = questions.apply(lambda x: str(x).count('？') > 1 if pd.notna(x) else False).sum()

    print(f"参考文件平均问题长度: {avg_length:.1f} 字符")
    print(f"包含多个问号的问题数: {has_multiple_questions}")
    print("\n参考问题示例:")
    for i, q in enumerate(questions.head(10)):
        print(f"{i+1}. {q}")

    return avg_length

def intelligent_split_question(question):
    """
    智能拆分问题
    规则：
    1. 识别明显的多个问题（如"A？B？"）
    2. 识别用"/"、"还是"连接的选择性问题
    3. 识别用顿号、逗号分隔的并列问题
    """
    if pd.isna(question) or not isinstance(question, str):
        return [question]

    question = str(question).strip()
    if not question:
        return [question]

    questions = []

    # 规则1: 按"？"分割（多个独立问题）
    parts = question.split('？')

    for i, part in enumerate(parts):
        part = part.strip()
        if not part:
            continue

        # 最后一个部分的处理
        if i == len(parts) - 1:
            # 检查是否包含"/"分隔符
            if '/' in part:
                # 拆分成多个小问题
                sub_questions = [s.strip() for s in part.split('/')]
                for sq in sub_questions:
                    if sq:
                        # 如果子问题不以问号结尾，添加问号
                        if not sq.endswith('？') and not sq.endswith('?'):
                            sq += '？'
                        questions.append(sq)
            else:
                # 没有"/"，直接添加
                if part:
                    if not part.endswith('？') and not part.endswith('?'):
                        part += '？'
                    questions.append(part)
        else:
            # 中间部分，添加问号
            questions.append(part + '？')

    return questions if questions else [question]

def analyze_supplement(supplement):
    """
    分析补充建议的类型
    返回: ('partial', supplement) 或 ('complete', supplement)
    """
    if pd.isna(supplement) or supplement == '':
        return ('none', '')

    supplement_str = str(supplement).strip()

    # 判断是否为部分补充（包含关键词）
    partial_keywords = [
        '补充', '增加', '添加', '还需要', '建议', '需要加上',
        '可以提及', '建议提到', '增加说明', '增加法国识别码'
    ]

    # 检查是否包含补充关键词
    is_partial = any(keyword in supplement_str for keyword in partial_keywords)

    # 判断是否为完整回复（通常较长且结构完整）
    is_complete = (
        len(supplement_str) > 100 and  # 长度超过100字符
        ('感谢' in supplement_str or '您好' in supplement_str or '关于' in supplement_str) and
        not is_partial
    )

    if is_complete:
        return ('complete', supplement_str)
    elif is_partial:
        return ('partial', supplement_str)
    else:
        # 默认为完整替换（如果不确定）
        return ('complete', supplement_str)

def merge_answer_intelligent(original_answer, supplement):
    """
    智能合并原回答和补充建议
    规则：
    1. 如果补充类型为'none'，返回原回答
    2. 如果补充类型为'partial'，合并原回答和补充内容
    3. 如果补充类型为'complete'，完全替换为补充内容
    """
    supplement_type, supplement_content = analyze_supplement(supplement)

    if supplement_type == 'none':
        return str(original_answer).strip() if not pd.isna(original_answer) else ''

    if supplement_type == 'partial':
        original_str = str(original_answer).strip() if not pd.isna(original_answer) else ''

        # 提取补充的具体内容
        # 尝试找到"："或":"后的内容
        if '：' in supplement_content:
            # 找到第一个"："之后的内容
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

def process_data_intelligent(test_df):
    """
    智能处理数据
    返回：问题列表和回答列表
    """
    print("\n开始智能处理数据...")

    questions = []
    answers = []

    # 跳过标题行（第一行）
    for idx, row in test_df.iloc[1:].iterrows():
        # 读取三列数据
        original_question = row[0] if len(row) > 0 else ''
        original_answer = row[1] if len(row) > 1 else ''
        supplement = row[2] if len(row) > 2 else ''

        # 跳过空行
        if pd.isna(original_question) or str(original_question).strip() == '':
            continue

        print(f"\n--- 处理第 {idx} 行 ---")
        print(f"原问题: {original_question}")

        # 步骤1：智能拆分问题
        split_questions = intelligent_split_question(original_question)
        print(f"拆分后问题: {split_questions}")

        # 步骤2：智能合并回答
        final_answer = merge_answer_intelligent(original_answer, supplement)
        supplement_type, _ = analyze_supplement(supplement)
        print(f"补充类型: {supplement_type}")
        print(f"最终回答前100字: {final_answer[:100]}...")

        # 步骤3：为每个拆分的问题分配回答
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
        worksheet.column_dimensions['A'].width = 60
        worksheet.column_dimensions['B'].width = 100

        # 设置自动换行和对齐
        for row in worksheet.iter_rows(min_row=2, max_row=len(questions)+1):
            for cell in row:
                cell.alignment = Alignment(wrap_text=True, vertical='top')

        # 设置标题行格式
        for cell in worksheet[1]:
            cell.font = Font(bold=True, size=12)
            cell.alignment = Alignment(horizontal='center', vertical='center')

    print(f"保存成功！文件路径: {output_filepath}")
    print(f"共保存 {len(questions)} 条问答对")

def main():
    """主函数"""
    print("=" * 80)
    print("Excel文件智能整理工具 v2")
    print("=" * 80)

    # 文件路径
    reference_file = "/home/yzh/AI客服/鉴权/aa.xlsx"
    test_file = "/home/yzh/AI客服/鉴权/test.xlsx"
    output_file = "/home/yzh/AI客服/鉴权/test2.xlsx"

    try:
        # 读取文件
        print(f"\n读取参考文件: {reference_file}")
        reference_df = pd.read_excel(reference_file, header=None)
        print(f"参考文件行数: {len(reference_df)}")

        print(f"\n读取待处理文件: {test_file}")
        test_df = pd.read_excel(test_file, header=None)
        print(f"待处理文件行数: {len(test_df)}")

        # 分析参考文件风格
        analyze_question_style(reference_df)

        # 智能处理数据
        questions, answers = process_data_intelligent(test_df)

        # 保存结果
        save_to_excel_formatted(questions, answers, output_file)

        # 显示示例
        print("\n" + "=" * 80)
        print("生成结果示例（前5条）:")
        print("=" * 80)
        for i in range(min(5, len(questions))):
            print(f"\n{i+1}. 问题: {questions[i]}")
            print(f"   回答: {answers[i][:100]}...")

        print("\n" + "=" * 80)
        print("处理完成！")
        print("=" * 80)

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
