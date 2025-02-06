import openpyxl

CourseList = []
def readXlsx():
    CourseList.clear()
    # 打开 Excel 文件
    wb = openpyxl.load_workbook('xlsx/course.xlsx')
    # 选择第一个工作表
    sheet = wb.active
    # 遍历每一行数据
    for row in sheet.iter_rows(values_only=True, min_row=2):
        course_id, course_name, course_group, video_file_name, video_duration = row
        # 输出每一行数据
        print(f"课程ID: {course_id}, 课程名称: {course_name}, 课程组名: {course_group}, 视频文件名称: {video_file_name}, 视频时长(分钟): {video_duration}")
        course_data = {
            "id": int(course_id),
            "name": course_name,
            "type": course_group,
            "video": video_file_name,
            "time": int(video_duration)
        }
        # 将字典添加到数据列表中
        CourseList.append(course_data)
    # 关闭 Excel 文件
    wb.close()
readXlsx()