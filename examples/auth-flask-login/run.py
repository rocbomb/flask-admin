from flask import Flask, request, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, ForeignKey, Time
from sqlalchemy.orm import relationship
from couse import CourseList
import os
import logging
from logging.handlers import TimedRotatingFileHandler

# 配置日志
log_path = './logs/logfile.log'  # 日志文件的路径
if not os.path.exists(os.path.dirname(log_path)):
    os.makedirs(os.path.dirname(log_path))


# 设置日志格式
log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=log_format)

# 设置日志轮转
handler = TimedRotatingFileHandler(log_path, when='midnight', interval=1, backupCount=30)
handler.setFormatter(logging.Formatter(log_format))
logger = logging.getLogger('my_logger')
logger.addHandler(handler)


app = Flask(__name__)
app.config["SECRET_KEY"] = "123456790"
app.config["DATABASE_FILE"] = "test2.sqlite"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + app.config["DATABASE_FILE"]
db = SQLAlchemy(app)
app.template_folder = os.path.join(os.getcwd(), 'html')

class StudyRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, nullable=False)
    course_id = db.Column(db.Integer, nullable=False)
    study_time = db.Column(db.Integer, nullable=False)

# Create user model.
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    login = db.Column(db.String(100), unique=True)
    phone = db.Column(db.String(80))
    password = db.Column(db.String(64))
    courses_list = db.Column(db.String(256))
    is_admin = db.Column(db.Boolean)

    # Flask-Login integration
    # NOTE: is_authenticated, is_active, and is_anonymous
    # are methods in Flask-Login < 0.3.0
    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id

    # Required for administrative interface
    def __unicode__(self):
        return self.name
    
    def getCourseList(self):
        return self.courses_list.split('|')


@app.route('/api/result')
def studentInfos():
    result = []
    records = StudyRecord.query.all()

    students_data = db.session.query(User).all()

    for student_info in students_data:
        for course_info in CourseList:
            if not course_info["type"] in student_info.getCourseList():
                continue

            record = None
            for r in records:
                #logger.info(f"{r.student_id}  {student_info.id}")
                if r.student_id == student_info.id and r.course_id == course_info['id']:
                    record = r
                    break
                continue
            over = "未完成"
            if record != None and record.study_time / 60 + 1 > course_info['time']:
                over = "完成"
            info = {
                'name': student_info.name,
                'course': course_info['name'],
                'over': over,
                'video_time': course_info['time'],
                'study_time': int(record.study_time / 60) if record != None else -1
                }
            result.append(info)
    return render_template('student.html', student_info=result)

@app.route('/api/study_records', methods=['POST'])
def create_study_record():
    student_id = request.json.get('student_id')
    course_id = request.json.get('course_id')
    study_time = request.json.get('study_time')
    study_record = StudyRecord(student_id=student_id, course_id=course_id, study_time=study_time)
    db.session.add(study_record)
    db.session.commit()

    return {'id': study_record.id}, 201

@app.route('/api/study_records', methods=['GET'])
def get_study_records():
    records = StudyRecord.query.all()
    return {'records': [{'id': r.id, 'student_id': r.student_id, 'course_id': r.course_id, 'study_time': str(r.study_time)} for r in records]}, 200

@app.route('/api/update_records', methods=['POST'])
def update_records():
    student_id = request.json.get('student_id')
    course_id = request.json.get('course_id')
    study_time = request.json.get('study_time')
    
    record = StudyRecord.query.filter_by(student_id = student_id, course_id = course_id).first()
    if record is None:
        record = StudyRecord(student_id = student_id, course_id = course_id, study_time = study_time)
        db.session.add(record)
        db.session.commit()
    else:
        record.study_time = record.study_time + study_time
        db.session.commit()
    logger.info(f"update_records student_id: {student_id}, course_id: {course_id}, study_time: {study_time}, endTime: {record.study_time}")
    return f"{course_id},{record.study_time}", 200

def findStudent(phone):
    return db.session.query(User).filter_by(login=phone).first()

def findStudentById(id):
    return db.session.query(User).filter_by(id=id).first()


def findCourse(id):
    for c in CourseList:
        if c["id"] == id:
            return c
    return None

@app.route('/api/login', methods=['POST'])
def login():
    userid = request.json.get('userid')
    password = request.json.get('password')

    userid = userid.strip()
    logger.info(f"login start userid:{userid} password:{password}")
    student = findStudent(userid)

    if student is None:
        logger.info(f"login no user userid:{userid} ")
        return {'id': -1, "error": "没有该用户"}, 201

    if str(student.password) != str(password):
        logger.info(f"login password error userid:{userid} ")
        return {'id': -1, "error": "密码错误"}, 201

    records = StudyRecord.query.filter_by(student_id = student.id).all()

    videos = []
    for course in CourseList:
        if course["type"] in student.getCourseList():
            videos.append(course)

    ret = {
        'id': student.id,
        "name" : student.name,
        "videos":videos,
        "records":[{'course_id': r.course_id, 'study_time': r.study_time} for r in records]
    }

    logger.info(f"login succeed userid:{userid} password:{password}")

    return ret, 201

def create_db():
    with app.app_context():
        db.create_all()
        alluser = db.session.query(User).all()
        for user in alluser:
            print(user.id, user.name)


if __name__ == '__main__':
    create_db()
    #app.run(debug=True, port=5000)
    app.run(port=5000)
