#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Excel文件智能整理脚本 v3
修正：正确识别文件结构（问题在第1列和第7列，回答在第2列和第8列，补充建议在第9列）
"""

import pandas as pd
from openpyxl.styles import Alignment, Font
import re

def intelligent_split_question(question):
    """
    智能拆分问题
    规则：
    1. 识别明显的多个问题（如"A？B？"）
    2. 识别用"/"连接的选择性问题
    3. 保持短句风格
    """
    if pd.isna(question) or not isinstance(question, str):
        return [question]

    question = str(question).strip()
    if not question:
        return [question]

    questions = []

    # 按"？"分割
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
                        if not sq.endswith('？') and not sq.endswith('?'):
                            sq += '？'
                        questions.append(sq)
            else:
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

    # 检查是否包含补充关键词
    is_partial = any(keyword in supplement_str[:50] for keyword in partial_keywords)

    # 判断是否为完整回复（通常较长且结构完整）
    is_complete = (
        len(supplement_str) > 80 and
        ('感谢' in supplement_str or '您好' in supplement_str or '关于' in supplement_str) and
        not is_partial
    )

    if is_complete:
        return ('complete', supplement_str)
    elif is_partial:
        return ('partial', supplement_str)
    else:
        # 默认为完整替换
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

def process_data_intelligent(test_df):
    """
    智能处理数据
    文件结构：
    - 列0-4: 第一组数据（问题在列0，回答在列1）
    - 列5: 空列
    - 列6: 第二组问题
    - 列7: 第二组回答
    - 列8: 优化建议（针对第二组）
    """
    print("\n开始智能处理数据...")

    questions = []
    answers = []

    # 跳过标题行（第一行）
    for idx, row in test_df.iloc[1:].iterrows():
        # 处理第一组数据（列0和列1）
        q1 = row[0] if len(row) > 0 else ''
        a1 = row[1] if len(row) > 1 else ''

        if pd.notna(q1) and str(q1).strip():
            print(f"\n--- 处理第一组 行{idx} ---")
            print(f"问题: {q1}")

            # 拆分问题
            split_questions = intelligent_split_question(q1)
            print(f"拆分后: {split_questions}")

            # 使用原回答（第一组没有补充建议）
            final_answer = str(a1).strip() if not pd.isna(a1) else ''

            for q in split_questions:
                if q and str(q).strip():
                    questions.append(str(q).strip())
                    answers.append(final_answer)

        # 处理第二组数据（列6、列7、列8）
        q2 = row[6] if len(row) > 6 else ''
        a2 = row[7] if len(row) > 7 else ''
        supplement = row[8] if len(row) > 8 else ''

        if pd.notna(q2) and str(q2).strip():
            print(f"\n--- 处理第二组 行{idx} ---")
            print(f"问题: {q2}")

            # 拆分问题
            split_questions = intelligent_split_question(q2)
            print(f"拆分后: {split_questions}")

            # 智能合并回答
            final_answer = merge_answer_intelligent(a2, supplement)
            supplement_type, _ = analyze_supplement(supplement)
            print(f"补充类型: {supplement_type}")
            print(f"最终回答前100字: {final_answer[:100]}...")

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

    print(f"保存成功！共保存 {len(questions)} 条问答对")

def main():
    """主函数"""
    print("=" * 80)
    print("Excel文件智能整理工具 v3")
    print("=" * 80)

    # 文件路径
    test_file = "/home/yzh/AI客服/鉴权/test.xlsx"
    output_file = "/home/yzh/AI客服/鉴权/test2.xlsx"

    try:
        # 读取文件
        print(f"\n读取待处理文件: {test_file}")
        test_df = pd.read_excel(test_file, header=None)
        print(f"待处理文件行数: {len(test_df)}")
        print(f"待处理文件列数: {len(test_df.columns)}")

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
            print(f"   回答: {answers[i][:150]}...")

        print("\n" + "=" * 80)
        print("处理完成！")
        print(f"输出文件: {output_file}")
        print("=" * 80)

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
