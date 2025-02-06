import openpyxl
import json



# 初始化一个空列表，用来存储学生信息
students_data = []
def readXlsx():
    # 打开 Excel 文件
    wb = openpyxl.load_workbook('xlsx/student.xlsx')
    sheet = wb.active
    # 遍历每一行数据，跳过第一行（标题行）
    for row in sheet.iter_rows(values_only=True, min_row=2):
        id, name, phone, password, courses = row
        if courses is None:
            continue
        courses_list = courses.split('|') if '|' in courses else [courses]  # 多个课程使用 | 分隔
        
        # 将学生信息存储为字典
        student_data = {
            "id": int(id),
            "name": name,
            "phone": phone,
            "password": password,
            "courses_list": courses_list,
            "courses": courses
        }
        print(f"{id} {name}-{phone}: {courses_list}")

        # 将学生信息字典添加到列表中
        students_data.append(student_data)
    # 关闭 Excel 文件
    wb.close()
readXlsx()