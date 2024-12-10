from flask import session, request, flash, redirect, url_for, render_template
from .base_controller import BaseController

class StudentController(BaseController):
    def get_profile(self):
        try:
            # 获取学生信息
            student = self.dao_factory.student_dao.get_by_user_id(session['user_id'])
            
            if request.method == 'POST':
                # 更新学生信息
                student_data = {
                    'name': request.form['name'],
                    'phone': request.form.get('phone', ''),
                    'email': request.form.get('email', '')
                }
                self.dao_factory.student_dao.update(student['id'], student_data)
                flash('个人信息更新成功')
                return redirect(url_for('student_profile'))
            
            return render_template('student/profile.html', student=student)
        except Exception as e:
            return self.handle_error(e, '操作失败', 'index')
    
    def get_teachers(self):
        try:
            # 获取学生信息
            student = self.dao_factory.student_dao.get_by_user_id(session['user_id'])
            if not student:
                flash('请先完善个人信息')
                return redirect(url_for('student_profile'))
            
            # 获取可申请的导师列表
            teachers = self.dao_factory.teacher_dao.get_all_qualified()
            
            # 获取学生的申请记录
            applications = self.dao_factory.student_dao.get_applications(student['id'])
            
            # 获取专业列表
            majors = self.dao_factory.major_dao.get_all()
            
            return render_template('student/teachers.html', 
                                 teachers=teachers,
                                 applications=applications,
                                 majors=majors)
        except Exception as e:
            return self.handle_error(e, '获取数据失败', 'index')
    
    def get_results(self):
        try:
            # 获取学生申请结果
            student = self.dao_factory.student_dao.get_by_user_id(session['user_id'])
            applications = self.dao_factory.student_dao.get_applications(student['id'])
            return render_template('student/results.html', applications=applications)
        except Exception as e:
            return self.handle_error(e, '获取数据失败', 'index')
    
    def apply_teacher(self, teacher_id):
        try:
            # 检查学生信息
            student = self.dao_factory.student_dao.get_by_user_id(session['user_id'])
            if not student:
                flash('请先完善个人信息')
                return redirect(url_for('student_profile'))
            
            # 检查学生状态
            if student['status'] != '已通过':
                flash('您的考生资格还未通过审核，暂时无法申请导师')
                return redirect(url_for('index'))
            
            # 检查导师是否可以申请
            teacher = self.dao_factory.teacher_dao.get_by_id(teacher_id)
            if not teacher or teacher['qual_status'] != '已通过':
                flash('该导师暂不可申请')
                return redirect(url_for('index'))
            
            # 检查申请数量
            app_count = self.dao_factory.student_dao.check_application_count(student['id'])
            if app_count >= 3:
                flash('最多只能申请3个志愿')
                return redirect(url_for('index'))
            
            # 检查是否已申请过该导师
            existing_app = self.dao_factory.application_dao.get_by_student_teacher(
                student['id'], teacher_id)
            if existing_app:
                flash('您已申请过该导师')
                return redirect(url_for('index'))
            
            # 创建申请
            try:
                self.dao_factory.application_dao.create(
                    student_id=student['id'],
                    teacher_id=teacher_id,
                    priority=int(request.form['priority']),
                    personal_statement=request.form.get('personal_statement', ''),
                    research_interest=request.form.get('research_interest', ''),
                    apply_reason=request.form.get('apply_reason', '')
                )
                flash('申请提交成功')
            except Exception as e:
                error_msg = str(e)
                if 'check_application_priority' in error_msg:
                    if '必须先提交第一志愿' in error_msg:
                        flash('请先提交第一志愿申请')
                    elif '请等待当前志愿审核完成' in error_msg:
                        flash('请等待当前志愿审核完成后再提交新申请')
                    elif '已有志愿被通过' in error_msg:
                        flash('您已有志愿被通过，不能继续申请')
                    elif '请按顺序提交志愿' in error_msg:
                        flash('请按照��愿顺序依次提交申请')
                    elif '最多只能申请三个志愿' in error_msg:
                        flash('最多只能申请三个志愿')
                    else:
                        flash('申请提交失败：' + error_msg)
                    return redirect(url_for('index'))
                raise e
                
        except Exception as e:
            return self.handle_error(e, '申请提交失败', 'index')
        
        return redirect(url_for('index'))
    
    def withdraw_application(self, app_id):
        try:
            # 检查是否是本人的申请
            app = self.dao_factory.application_dao.get_by_id(app_id)
            if not app or app['student_id'] != session['student_id']:
                return '无权操作', 403
            
            if app['status'] != '待处理':
                return '不能撤回已处理的申请', 400
            
            # 删除申请记录
            self.dao_factory.application_dao.delete(app_id)
            
            return '', 204
        except Exception as e:
            print(f"撤回申请错误: {e}")
            return '操作失败', 500 
    
    def get_available_priority(self, student_id: int) -> int:
        """获取学生当前可申请的志愿顺序"""
        sql = '''
            SELECT priority, status
            FROM student_applications
            WHERE student_id = %s
            ORDER BY create_time DESC
            LIMIT 1
        '''
        result = self.query_one(sql, (student_id,))
        
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