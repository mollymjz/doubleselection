from flask import Flask, render_template, request, redirect, url_for, flash, session
from dao import DAOFactory
from controllers.auth_controller import AuthController
from controllers.student_controller import StudentController
from controllers.teacher_controller import TeacherController
from controllers.admin_controller import AdminController
from utils import login_required, role_required
from pymysql.cursors import DictCursor
import json

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # 请更改为随机密钥

# 创建DAO工厂实例
dao_factory = DAOFactory({
    'host': 'localhost',
    'user': 'root',
    'password': 'Qwe!@#123',
    'db': 'yjsds2',
    'charset': 'utf8mb4',
    'cursorclass': DictCursor
})

# 创建Controller实例
auth_controller = AuthController(dao_factory)
student_controller = StudentController(dao_factory)
teacher_controller = TeacherController(dao_factory)
admin_controller = AdminController(dao_factory)

@app.route('/')
def index():
    majors = dao_factory.major_dao.get_with_teachers()
    return render_template('index.html', majors=majors)

@app.route('/login', methods=['GET', 'POST'])
def login():
    return auth_controller.login()

@app.route('/logout')
def logout():
    return auth_controller.logout()

@app.route('/register', methods=['GET', 'POST'])
def register():
    return auth_controller.register()

# 学生相关路由
@app.route('/student/apply/<int:teacher_id>', methods=['POST'])
@login_required
@role_required(['student'])
def student_apply(teacher_id):
    return student_controller.apply_teacher(teacher_id)

@app.route('/student/withdraw/<int:app_id>', methods=['POST'])
@login_required
@role_required(['student'])
def student_withdraw(app_id):
    return student_controller.withdraw_application(app_id)

@app.route('/student/profile', methods=['GET', 'POST'])
@login_required
@role_required(['student'])
def student_profile():
    return student_controller.get_profile()

@app.route('/student/results')
@login_required
@role_required(['student'])
def student_results():
    return student_controller.get_results()

@app.route('/student/teachers')
@login_required
@role_required(['student'])
def student_teachers():
    return student_controller.get_teachers()

# 教师相关路由
@app.route('/teacher/profile', methods=['GET', 'POST'])
@login_required
@role_required(['teacher'])
def teacher_profile():
    return teacher_controller.get_profile()

@app.route('/teacher/students')
@login_required
@role_required(['teacher'])
def teacher_students():
    return teacher_controller.get_students()

@app.route('/teacher/accept/<int:app_id>', methods=['POST'])
@login_required
@role_required(['teacher'])
def teacher_accept_student(app_id):
    return teacher_controller.accept_student(app_id)

@app.route('/teacher/reject/<int:app_id>', methods=['POST'])
@login_required
@role_required(['teacher'])
def teacher_reject_student(app_id):
    return teacher_controller.reject_student(app_id)

@app.route('/teacher/qualification/apply', methods=['POST'])
@login_required
@role_required(['teacher'])
def teacher_apply_qualification():
    return teacher_controller.apply_qualification()

# 管理员相关路由
@app.route('/admin/dashboard')
@login_required
@role_required(['admin'])
def admin_dashboard():
    return admin_controller.get_dashboard()

@app.route('/admin/users')
@login_required
@role_required(['admin'])
def admin_users():
    return admin_controller.get_users()

@app.route('/admin/teachers')
@login_required
@role_required(['admin'])
def admin_teachers():
    return admin_controller.get_teachers()

@app.route('/admin/students')
@login_required
@role_required(['admin'])
def admin_students():
    return admin_controller.get_students()

@app.route('/admin/qualifications')
@login_required
@role_required(['admin'])
def admin_qualifications():
    return admin_controller.get_qualifications()

@app.route('/admin/user/update/<int:user_id>', methods=['POST'])
@login_required
@role_required(['admin'])
def admin_update_user(user_id):
    return admin_controller.update_user(user_id)

@app.route('/admin/user/delete/<int:user_id>', methods=['POST'])
@login_required
@role_required(['admin'])
def admin_delete_user(user_id):
    return admin_controller.delete_user(user_id)

@app.route('/admin/qualification/update/<int:qual_id>', methods=['POST'])
@login_required
@role_required(['admin'])
def admin_update_qualification(qual_id):
    return admin_controller.update_qualification(qual_id)

@app.route('/admin/qualification/add', methods=['POST'])
@login_required
@role_required(['admin'])
def admin_add_qualification():
    return admin_controller.add_qualification()

@app.route('/admin/teacher/add', methods=['POST'])
@login_required
@role_required(['admin'])
def admin_add_teacher():
    return admin_controller.add_teacher()

@app.route('/admin/teacher/update/<int:teacher_id>', methods=['POST'])
@login_required
@role_required(['admin'])
def admin_update_teacher(teacher_id):
    return admin_controller.update_teacher(teacher_id)

@app.route('/admin/student/add', methods=['POST'])
@login_required
@role_required(['admin'])
def admin_add_student():
    return admin_controller.add_student()

@app.route('/admin/student/update/<int:student_id>', methods=['POST'])
@login_required
@role_required(['admin'])
def admin_update_student(student_id):
    return admin_controller.update_student(student_id)

@app.route('/admin/student/delete/<int:student_id>', methods=['POST'])
@login_required
@role_required(['admin'])
def admin_delete_student(student_id):
    return admin_controller.delete_student(student_id)

@app.route('/admin/quota_allocation')
@login_required
@role_required(['admin'])
def admin_quota_allocation():
    return admin_controller.get_quota_allocation()

@app.route('/admin/teacher/quota/<int:teacher_id>', methods=['POST'])
@login_required
@role_required(['admin'])
def admin_update_teacher_quota(teacher_id):
    return admin_controller.update_teacher_quota(teacher_id)

@app.route('/admin/teacher/quota/batch', methods=['POST'])
@login_required
@role_required(['admin'])
def admin_batch_update_quota():
    return admin_controller.batch_update_quota()

@app.route('/admin/majors')
@login_required
@role_required(['admin'])
def admin_majors():
    return admin_controller.get_majors()

@app.route('/admin/major/add', methods=['POST'])
@login_required
@role_required(['admin'])
def admin_add_major():
    return admin_controller.add_major()

@app.route('/admin/major/update/<int:major_id>', methods=['POST'])
@login_required
@role_required(['admin'])
def admin_update_major(major_id):
    return admin_controller.update_major(major_id)

@app.route('/admin/major/delete/<int:major_id>', methods=['POST'])
@login_required
@role_required(['admin'])
def admin_delete_major(major_id):
    return admin_controller.delete_major(major_id)

@app.route('/admin/teacher/majors/<int:teacher_id>', methods=['POST'])
@login_required
@role_required(['admin'])
def admin_update_teacher_majors(teacher_id):
    return admin_controller.update_teacher_majors(teacher_id)

@app.route('/admin/qualification/review/<int:qual_id>', methods=['POST'])
@login_required
@role_required(['admin'])
def admin_review_qualification(qual_id):
    return admin_controller.review_qualification(qual_id)

@app.route('/admin/logs')
@login_required
@role_required(['admin'])
def admin_logs():
    return admin_controller.get_logs()

@app.route('/admin/supervision')
@login_required
@role_required(['admin'])
def admin_supervision():
    return admin_controller.get_supervision()

@app.route('/admin/supervision/add', methods=['POST'])
@login_required
@role_required(['admin'])
def admin_add_supervision_phase():
    return admin_controller.add_supervision_phase()

@app.route('/admin/supervision/<int:phase_id>/status', methods=['POST'])
@login_required
@role_required(['admin'])
def admin_update_supervision_status(phase_id):
    return admin_controller.update_supervision_status(phase_id)

@app.route('/admin/admissions')
@login_required
@role_required(['admin'])
def admin_admissions():
    return admin_controller.get_admissions()

@app.route('/admin/admission/<int:app_id>/approve', methods=['POST'])
@login_required
@role_required(['admin'])
def admin_approve_admission(app_id):
    return admin_controller.approve_admission(app_id)

# 错误处理
@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('errors/500.html'), 500

@app.template_filter('from_json')
def from_json(value):
    if not value:
        return []
    try:
        return json.loads(value)
    except:
        return []

@app.template_filter('get_available_priority')
def get_available_priority(student_id):
    """获取学生当前可申请的志愿顺序"""
    if not student_id:
        return 0
        
    sql = '''
        SELECT priority, status
        FROM student_applications
        WHERE student_id = %s
        ORDER BY create_time DESC
        LIMIT 1
    '''
    result = dao_factory.student_dao.query_one(sql, (student_id,))
    
    if not result:
        return 1  # 第一次申请
    
    if result['status'] == '待处理':
        return 0  # 不能申请
    elif result['status'] == '已通过':
        return 0  # 不能申请
    elif result['status'] == '未通过':
        next_priority = result['priority'] + 1
        return next_priority if next_priority <= 3 else 0
    
    return 0  # 默认不能申请

if __name__ == '__main__':
    app.run(debug=True) 