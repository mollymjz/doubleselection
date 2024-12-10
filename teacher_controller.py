from flask import session, request, flash, redirect, url_for, render_template
from .base_controller import BaseController
import random
from datetime import datetime

class TeacherController(BaseController):
    def get_profile(self):
        try:
            # 获取教师信息
            teacher = self.dao_factory.teacher_dao.get_by_user_id(session['user_id'])
            if request.method == 'POST':
                # 更新教师信息
                self.dao_factory.teacher_dao.update_profile(
                    teacher['id'],
                    {
                        'introduction': request.form['introduction'],
                        'research_direction': request.form['research_direction']
                    }
                )
                flash('个人信息更新成功')
            
            return render_template('teacher/profile.html', teacher=teacher)
        except Exception as e:
            return self.handle_error(e, '操作失败', 'index')
    
    def get_students(self):
        try:
            # 获取教师信息和名额情况
            teacher = self.dao_factory.teacher_dao.get_by_user_id(session['user_id'])
            if not teacher:
                flash('导师信息不存在')
                return redirect(url_for('teacher_profile'))
            
            # 获取申请该导师的学生列表
            applications = self.dao_factory.teacher_dao.get_students(teacher['id'])
            
            return render_template('teacher/students.html', 
                                 teacher=teacher,
                                 applications=applications)
        except Exception as e:
            return self.handle_error(e, '获取数据失败', 'teacher_profile')
    
    def accept_student(self, app_id):
        """接受学生申请"""
        try:
            # 获取申请信息
            app = self.dao_factory.application_dao.get_by_id(app_id)
            if not app:
                flash('申请不存在')
                return redirect(url_for('teacher_students'))
            
            # 检查名额
            teacher = self.dao_factory.teacher_dao.get_by_user_id(session['user_id'])
            current_count = self.dao_factory.teacher_dao.check_student_count(teacher['id'])
            
            if current_count >= teacher['max_students']:
                flash('您的招生名额已满')
                return redirect(url_for('teacher_students'))
            
            # 使用事务处理申请
            with self.dao_factory.application_dao.transaction_context() as cursor:
                # 更新当前申请状态
                sql = '''
                    UPDATE student_applications 
                    SET status = '已通过',
                        process_time = CURRENT_TIMESTAMP,
                        process_comment = %s,
                        approval_status = '待审批'
                    WHERE id = %s
                '''
                cursor.execute(sql, ('申请通过', app_id))
                
                # 拒绝该学生的其他申请
                sql = '''
                    UPDATE student_applications 
                    SET status = '未通过',
                        process_time = CURRENT_TIMESTAMP,
                        process_comment = '已被其他导师录取'
                    WHERE student_id = %s 
                    AND id != %s
                    AND status = '待处理'
                '''
                cursor.execute(sql, (app['student_id'], app_id))
            
            flash(f'已接受 {app["student_name"]} 的申请')
        except Exception as e:
            return self.handle_error(e, '操作失败', 'teacher_students')
        
        return redirect(url_for('teacher_students'))
    
    def reject_student(self, app_id):
        try:
            # 获取申请信息
            app = self.dao_factory.application_dao.get_by_id(app_id)
            if not app:
                flash('申请不存在')
                return redirect(url_for('teacher_students'))
            
            # 更新申请状态
            self.dao_factory.application_dao.update_status(
                app_id, '未通过', '申请未通过')
            
            flash(f'已拒绝 {app["student_name"]} 的申请')
        except Exception as e:
            return self.handle_error(e, '操作失败', 'teacher_students')
        
        return redirect(url_for('teacher_students'))
    
    def apply_qualification(self):
        try:
            # 准备申请数据
            qual_data = {
                'sci_papers': int(request.form['sci_papers']),
                'ei_papers': int(request.form['ei_papers']),
                'core_papers': int(request.form['core_papers']),
                'national_projects': int(request.form['national_projects']),
                'province_projects': int(request.form['province_projects']),
                'other_projects': int(request.form['other_projects']),
                'research_funds': float(request.form['research_funds']),
                'awards': request.form.get('awards', ''),
                'students_count': int(request.form['students_count'])
            }
            
            # 获取教师信息
            teacher = self.dao_factory.teacher_dao.get_by_user_id(session['user_id'])
            if not teacher:
                flash('导师信息不存在')
                return redirect(url_for('teacher_profile'))
            
            # 检查是否已有申请
            if self.dao_factory.qualification_dao.check_year_application(
                teacher['id'], datetime.now().year):
                flash('本年度已提交过申请')
                return redirect(url_for('teacher_profile'))
            
            # 计算评分
            score_info = self.dao_factory.qualification_dao.calculate_score(qual_data)
            qual_data.update(score_info)
            
            # 判定等级
            qual_data['review_level'] = self.dao_factory.qualification_dao.get_review_level(
                qual_data['score'])
            
            # 创建资格申请
            self.dao_factory.qualification_dao.create(teacher['id'], qual_data)
            
            flash('资格申请已提交，请等待审核')
        except Exception as e:
            return self.handle_error(e, '申请提交失败', 'teacher_profile')
        
        return redirect(url_for('teacher_profile'))
    
    def get_draw_lots(self):
        try:
            # 获取教师信息
            teacher = self.dao_factory.teacher_dao.get_by_user_id(session['user_id'])
            if not teacher:
                flash('导师信息不存在')
                return redirect(url_for('teacher_profile'))
            
            # 获取可抽签的学生列表
            students = self.dao_factory.draw_dao.get_available_students(teacher['id'])
            
            return render_template('teacher/draw_lots.html',
                                 teacher=teacher,
                                 students=students)
        except Exception as e:
            return self.handle_error(e, '获取数据失败', 'teacher_profile') 