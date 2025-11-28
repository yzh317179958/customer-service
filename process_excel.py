#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Excel文件整理脚本
功能：
1. 读取参考文件(aa.xlsx)和待处理文件(test.xlsx)
2. 按照规则整理问题和回答
3. 生成新文件(test2.xlsx)
"""

import pandas as pd
import openpyxl
from openpyxl.styles import Alignment, Font
import re

def read_reference_file(filepath):
    """读取参考文件aa.xlsx，分析问题格式"""
    print(f"正在读取参考文件: {filepath}")
    df = pd.read_excel(filepath, header=None)
    print(f"参考文件行数: {len(df)}")
    print("\n参考文件前5行内容:")
    print(df.head())
    return df

def read_test_file(filepath):
    """读取待处理文件test.xlsx"""
    print(f"\n正在读取待处理文件: {filepath}")
    df = pd.read_excel(filepath, header=None)
    print(f"待处理文件行数: {len(df)}")
    print("\n待处理文件前5行内容:")
    print(df.head())
    return df

def split_question(question):
    """
    拆分包含多个语境的问题
    规则：识别"？"、"，"、"、"等分隔符，拆分成多个短句
    """
    if pd.isna(question) or not isinstance(question, str):
        return [question]

    # 按照"？"分割，保留问号
    questions = []
    parts = question.split('？')
    for i, part in enumerate(parts):
        if part.strip():
            if i < len(parts) - 1:
                questions.append(part.strip() + '？')
            else:
                # 最后一个部分，如果不以问号结尾，检查是否需要拆分
                if '，' in part or '、' in part or '。' in part:
                    # 包含多个子问题，拆分
                    sub_parts = re.split(r'[，、。]', part)
                    for sub in sub_parts:
                        if sub.strip():
                            questions.append(sub.strip())
                elif part.strip():
                    questions.append(part.strip())

    return questions if questions else [question]

def merge_answer(original_answer, supplement):
    """
    合并原回答和补充建议
    规则：
    1. 如果补充建议包含"补充"、"增加"等字眼，则合并到原回答
    2. 如果补充建议是完整回复，则替换原回答
    3. 严格保留补充建议的原文，不修改内容
    """
    if pd.isna(supplement) or supplement == '':
        return original_answer

    supplement_str = str(supplement).strip()
    original_str = str(original_answer).strip() if not pd.isna(original_answer) else ''

    # 判断补充建议的类型
    keywords = ['补充', '增加', '添加', '还需要', '建议']
    is_partial_supplement = any(keyword in supplement_str for keyword in keywords)

    if is_partial_supplement and original_str:
        # 部分补充：合并原回答和补充建议
        # 检查补充建议中是否有具体的补充内容
        if '：' in supplement_str or ':' in supplement_str:
            # 提取补充内容
            supplement_content = re.split(r'[：:]', supplement_str, 1)[-1].strip()
            return f"{original_str}\n\n{supplement_content}"
        else:
            return f"{original_str}\n\n{supplement_str}"
    else:
        # 完整回复：使用补充建议替换原回答
        return supplement_str

def process_data(reference_df, test_df):
    """
    处理数据
    返回：问题列表和回答列表
    """
    print("\n开始处理数据...")

    questions = []
    answers = []

    for idx, row in test_df.iterrows():
        # 读取三列数据
        original_question = row[0] if len(row) > 0 else ''
        original_answer = row[1] if len(row) > 1 else ''
        supplement = row[2] if len(row) > 2 else ''

        print(f"\n--- 处理第 {idx + 1} 行 ---")
        print(f"原问题: {original_question}")
        print(f"原回答: {original_answer}")
        print(f"补充建议: {supplement}")

        # 步骤1：拆分问题
        split_questions = split_question(original_question)
        print(f"拆分后问题数: {len(split_questions)}")

        # 步骤2：合并回答
        final_answer = merge_answer(original_answer, supplement)
        print(f"最终回答: {final_answer[:100]}..." if len(str(final_answer)) > 100 else f"最终回答: {final_answer}")

        # 步骤3：如果问题被拆分成多个，每个问题使用相同的回答
        for q in split_questions:
            if q and str(q).strip():
                questions.append(str(q).strip())
                answers.append(final_answer)

    print(f"\n处理完成！共生成 {len(questions)} 条问答对")
    return questions, answers

def save_to_excel(questions, answers, output_filepath):
    """保存到Excel文件"""
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
        worksheet.column_dimensions['A'].width = 50
        worksheet.column_dimensions['B'].width = 80

        # 设置自动换行和对齐
        for row in worksheet.iter_rows(min_row=2, max_row=len(questions)+1):
            for cell in row:
                cell.alignment = Alignment(wrap_text=True, vertical='top')

        # 设置标题行格式
        for cell in worksheet[1]:
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal='center', vertical='center')

    print(f"保存成功！文件路径: {output_filepath}")

def main():
    """主函数"""
    print("=" * 60)
    print("Excel文件整理工具")
    print("=" * 60)

    # 文件路径
    reference_file = "/home/yzh/AI客服/鉴权/aa.xlsx"
    test_file = "/home/yzh/AI客服/鉴权/test.xlsx"
    output_file = "/home/yzh/AI客服/鉴权/test2.xlsx"

    try:
        # 读取文件
        reference_df = read_reference_file(reference_file)
        test_df = read_test_file(test_file)

        # 处理数据
        questions, answers = process_data(reference_df, test_df)

        # 保存结果
        save_to_excel(questions, answers, output_file)

        print("\n" + "=" * 60)
        print("处理完成！")
        print("=" * 60)

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
