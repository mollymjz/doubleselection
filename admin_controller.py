from flask import session, request, flash, redirect, url_for, render_template
from .base_controller import BaseController
from datetime import datetime

class AdminController(BaseController):
    def get_dashboard(self):
        try:
            # 获取统计数据
            stats = self.dao_factory.application_dao.get_statistics()
            stats.update({
                'total_students': len(self.dao_factory.student_dao.get_all_with_stats()),
                'total_teachers': len(self.dao_factory.teacher_dao.get_all_with_stats()),
                'pending_qualifications': len(self.dao_factory.qualification_dao.get_pending_reviews())
            })
            
            # 获取最近活动
            activities = []
            
            # 获取最近申请活动
            applications = self.dao_factory.application_dao.get_all_with_details()
            for app in applications[:5]:
                activities.append({
                    'time': app['create_time'],
                    'type': '志愿申请',
                    'details': f"{app['student_name']} 申请了 {app['teacher_name']} 导师"
                })
            
            # 获取最近资格申请活动
            qualifications = self.dao_factory.qualification_dao.get_all_with_details()
            for qual in qualifications[:5]:
                activities.append({
                    'time': qual['create_time'],
                    'type': '资格申请',
                    'details': f"{qual['teacher_name']} 提交了 {qual['title']} 导师资格申请"
                })
            
            # 按时间排序并限制数量
            activities.sort(key=lambda x: x['time'], reverse=True)
            activities = activities[:10]
            
            return render_template('admin/dashboard.html', 
                                 stats=stats,
                                 activities=activities)
        except Exception as e:
            return self.handle_error(e, '获取数据失败', 'index')
    
    def get_users(self):
        try:
            users = self.dao_factory.user_dao.get_all_with_details()
            return render_template('admin/users.html', users=users)
        except Exception as e:
            return self.handle_error(e, '获取用户列表失败', 'admin_dashboard')
    
    def get_teachers(self):
        try:
            teachers = self.dao_factory.teacher_dao.get_all_with_stats()
            qualifications = self.dao_factory.qualification_dao.get_all_with_details()
            majors = self.dao_factory.major_dao.get_all()  # 获取所有专业
            
            # 获取每个导师的专业ID列表
            for teacher in teachers:
                teacher_majors = self.dao_factory.major_dao.get_teacher_majors(teacher['id'])
                teacher['major_ids'] = [m['id'] for m in teacher_majors]
            
            return render_template('admin/teachers.html', 
                                 teachers=teachers,
                                 qualifications=qualifications,
                                 majors=majors)  # 传递专业列表
        except Exception as e:
            flash('获取导师列表失败')
            print(f"获取导师列表错误: {e}")
            return redirect(url_for('admin_dashboard'))
    
    def get_students(self):
        try:
            students = self.dao_factory.student_dao.get_all_with_stats()
            return render_template('admin/students.html', students=students)
        except Exception as e:
            return self.handle_error(e, '获取学生列表失败', 'admin_dashboard')
    
    def get_qualifications(self):
        """获取导师资格申请列表"""
        try:
            qualifications = self.dao_factory.qualification_dao.get_all_with_details()
            return render_template('admin/qualifications.html', qualifications=qualifications)
        except Exception as e:
            print(f"获取资格申请列表错误: {e}")  # 添加错误日志
            return self.handle_error(e, '获取资格申请列表失败', 'admin_dashboard')
    
    def update_user(self, user_id):
        try:
            # 准备更新数据
            user_data = {
                'username': request.form['username'],
                'role': request.form['role']
            }
            
            if request.form.get('password'):
                user_data['password'] = request.form['password']
            
            name = request.form['name']
            
            # 使用事务更新用户信息
            with self.dao_factory.user_dao.transaction_context() as cursor:
                # 更新用户基本信息
                self.dao_factory.user_dao.update(user_id, user_data)
                
                # 根据角色更新相关表信息
                if user_data['role'] == 'student':
                    student = self.dao_factory.student_dao.get_by_user_id(user_id)
                    if student:
                        self.dao_factory.student_dao.update(student['id'], {'name': name})
                elif user_data['role'] == 'teacher':
                    teacher = self.dao_factory.teacher_dao.get_by_user_id(user_id)
                    if teacher:
                        self.dao_factory.teacher_dao.update_profile(teacher['id'], {'name': name})
            
            flash('用户信息已更新')
        except Exception as e:
            return self.handle_error(e, '更新用户失败', 'admin_users')
        
        return redirect(url_for('admin_users'))
    
    def delete_user(self, user_id):
        try:
            # 获取用户信息
            user = self.dao_factory.user_dao.get_by_id(user_id)
            if not user:
                flash('用户不存在')
                return redirect(url_for('admin_users'))
            
            # 根据角色删除相关记录
            if user['role'] == 'student':
                student = self.dao_factory.student_dao.get_by_user_id(user_id)
                if student:
                    self.dao_factory.student_dao.delete(student['id'])
            elif user['role'] == 'teacher':
                teacher = self.dao_factory.teacher_dao.get_by_user_id(user_id)
                if teacher:
                    self.dao_factory.teacher_dao.delete(teacher['id'])
            
            # 删除用户
            self.dao_factory.user_dao.delete(user_id)
            
            flash('用户已删除')
        except Exception as e:
            return self.handle_error(e, '删除用户失败', 'admin_users')
        
        return redirect(url_for('admin_users'))
    
    def update_qualification(self, qual_id):
        try:
            status = request.form['status']
            review_comment = request.form.get('review_comment', '')
            
            # 使用事务处理审核
            with self.dao_factory.qualification_dao.transaction_context() as cursor:
                # 更新审核状态
                self.dao_factory.qualification_dao.update_review(
                    qual_id, status, session['user_id'], review_comment)
                
                # 取申请信息
                qual = self.dao_factory.qualification_dao.get_by_id(qual_id)
                if not qual:
                    raise Exception('申请记录不存在')
                
                # 更新导师状态
                if status == '已通过':
                    standards = self.dao_factory.qualification_dao.get_standards()
                    max_students = standards[qual['review_level'].lower()]['max_students']
                    
                    self.dao_factory.teacher_dao.update_qualification(
                        qual['teacher_id'],
                        qual_status='已通过',
                        review_level=qual['review_level'],
                        max_students=max_students
                    )
                else:
                    self.dao_factory.teacher_dao.update_qualification(
                        qual['teacher_id'],
                        qual_status='未通过',
                        max_students=0
                    )
            
            flash('审核完成')
        except Exception as e:
            return self.handle_error(e, '审核失败', 'admin_qualifications')
        
        return redirect(url_for('admin_qualifications'))
    
    def add_qualification(self):
        try:
            # 准备申请数据
            qual_data = {
                'teacher_id': int(request.form['teacher_id']),
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
            
            # 计算评分
            score_info = self.dao_factory.qualification_dao.calculate_score(qual_data)
            qual_data.update(score_info)  # 添加 score 和 score_detail
            
            # 判定等级
            qual_data['review_level'] = self.dao_factory.qualification_dao.get_review_level(
                qual_data['score'])
            
            # 创建资格申请
            teacher_id = qual_data.pop('teacher_id')  # 从数据中取出teacher_id
            self.dao_factory.qualification_dao.create(teacher_id, qual_data)
            
            flash('资格申请已添加')
        except Exception as e:
            print(f"添加资格申请错误: {e}")  # 添加错误日志
            return self.handle_error(e, '添加失败', 'admin_qualifications')
        
        return redirect(url_for('admin_qualifications'))
    
    def add_teacher(self):
        try:
            username = request.form.get('username').strip()
            password = request.form.get('password')
            name = request.form.get('name').strip()
            
            # 准备教师数据
            teacher_data = {
                'name': name,
                'title': request.form.get('title'),
                'research_direction': request.form.get('research_direction'),
                'introduction': request.form.get('introduction'),
                'max_students': int(request.form.get('max_students', 0))
            }
            
            # 检查用户名是否已存在
            if self.dao_factory.user_dao.get_by_username(username):
                flash('用户名已存在')
                return redirect(url_for('admin_teachers'))
            
            # 使用事务创建用户和教师记录
            with self.dao_factory.user_dao.transaction_context() as cursor:
                # 创建用户账号
                user_id = self.dao_factory.user_dao.create(username, password, 'teacher')
                
                # 创建教师信息
                teacher_id = self.dao_factory.teacher_dao.create(
                    user_id=user_id,
                    name=name,
                    title=teacher_data['title']
                )
                
                # 更新教师额外信息
                self.dao_factory.teacher_dao.update_profile(teacher_id, teacher_data)
                
                # 添加专业关联
                major_ids = request.form.getlist('major_ids[]')
                if major_ids:
                    self.dao_factory.major_dao.update_teacher_majors(teacher_id, major_ids)
            
            flash('教师添加成功')
        except Exception as e:
            return self.handle_error(e, '添加失败', 'admin_teachers')
        
        return redirect(url_for('admin_teachers'))
    
    def update_teacher(self, teacher_id):
        try:
            # 准备更新数据
            teacher_data = {
                'name': request.form['name'],
                'title': request.form['title'],
                'research_direction': request.form['research_direction'],
                'introduction': request.form['introduction'],
                'max_students': int(request.form['max_students']),
                'major_ids': request.form.getlist('major_ids[]')  # 获取专业ID列表
            }
            
            # 更新教师信息
            self.dao_factory.teacher_dao.update_profile(teacher_id, teacher_data)
            flash('教师信息已更新')
        except Exception as e:
            return self.handle_error(e, '更新失败', 'admin_teachers')
        
        return redirect(url_for('admin_teachers'))
    
    def add_student(self):
        try:
            username = request.form.get('username').strip()
            password = request.form.get('password')
            name = request.form.get('name').strip()
            
            # 准备学生数据
            student_data = {
                'name': name,
                'initial_score': float(request.form.get('initial_score', 0)),
                'retest_score': float(request.form.get('retest_score', 0)),
                'status': request.form.get('status'),
                'phone': request.form.get('phone', ''),
                'email': request.form.get('email', '')
            }
            
            # 检查用户名是否已存在
            if self.dao_factory.user_dao.get_by_username(username):
                flash('用户名已存在')
                return redirect(url_for('admin_students'))
            
            # 使用事务创建用户和学生记录
            with self.dao_factory.user_dao.transaction_context() as cursor:
                # 创建用户账号
                user_id = self.dao_factory.user_dao.create(username, password, 'student')
                
                # 创建学生信息
                student_id = self.dao_factory.student_dao.create(
                    user_id=user_id,
                    name=name,
                    status=student_data['status']
                )
                
                # 更新学生额外信息
                self.dao_factory.student_dao.update(student_id, student_data)
            
            flash('学生添加成功')
        except Exception as e:
            return self.handle_error(e, '添��失败', 'admin_students')
        
        return redirect(url_for('admin_students'))
    
    def update_student(self, student_id):
        try:
            # 准备更新数据
            student_data = {
                'name': request.form['name'],
                'initial_score': float(request.form.get('initial_score', 0)),
                'retest_score': float(request.form.get('retest_score', 0)),
                'status': request.form['status'],
                'phone': request.form.get('phone', ''),
                'email': request.form.get('email', '')
            }
            
            # 更新学生信息
            self.dao_factory.student_dao.update(student_id, student_data)
            flash('学生信息已更新')
        except Exception as e:
            return self.handle_error(e, '更新失败', 'admin_students')
        
        return redirect(url_for('admin_students'))
    
    def delete_student(self, student_id):
        try:
            # 获取学生信息
            student = self.dao_factory.student_dao.get_by_id(student_id)
            if not student:
                flash('学生不存在')
                return redirect(url_for('admin_students'))
            
            # 删除学生及相关记录
            self.dao_factory.student_dao.delete(student_id)
            self.dao_factory.user_dao.delete(student['user_id'])
            
            flash('学生已删除')
        except Exception as e:
            return self.handle_error(e, '删除失败', 'admin_students')
        
        return redirect(url_for('admin_students'))
    
    def get_quota_allocation(self):
        """获取名额分配页面"""
        try:
            # 获取已通过资格审核的导师列表
            teachers = self.dao_factory.teacher_dao.get_qualified_teachers()
            return render_template('admin/quota_allocation.html', teachers=teachers)
        except Exception as e:
            return self.handle_error(e, '获取数据失败', 'admin_dashboard')
    
    def update_teacher_quota(self, teacher_id):
        """更新导师招生名额"""
        try:
            # 准备更新数据
            quota_data = {
                'max_students': int(request.form['max_students']),
                'quota_status': '已分配',
                'quota_year': datetime.now().year,
                'quota_comment': request.form.get('quota_comment', '')
            }
            
            # 更新导师名额
            self.dao_factory.teacher_dao.update_quota(teacher_id, quota_data)
            flash('招生名额已更新')
        except Exception as e:
            return self.handle_error(e, '更新失败', 'admin_quota_allocation')
        
        return redirect(url_for('admin_quota_allocation'))
    
    def batch_update_quota(self):
        """批量更新导师招生名额"""
        try:
            # 获取表单数据
            teacher_quotas = []
            for key, value in request.form.items():
                if key.startswith('quota_'):
                    teacher_id = int(key.split('_')[1])
                    teacher_quotas.append({
                        'teacher_id': teacher_id,
                        'max_students': int(value),
                        'quota_status': '已分配',
                        'quota_year': datetime.now().year
                    })
            
            # 批量更新
            self.dao_factory.teacher_dao.batch_update_quota(teacher_quotas)
            flash('招生名额已批量更新')
        except Exception as e:
            return self.handle_error(e, '批量更新失败', 'admin_quota_allocation')
        
        return redirect(url_for('admin_quota_allocation'))
    
    def get_majors(self):
        """获取专业管理页面"""
        try:
            majors = self.dao_factory.major_dao.get_all_with_teachers()
            teachers = self.dao_factory.teacher_dao.get_all_with_stats()
            
            # 处理教师ID列表
            for major in majors:
                if major['teacher_ids']:
                    major['teacher_ids'] = [int(id) for id in major['teacher_ids'].split(',')]
                else:
                    major['teacher_ids'] = []
            
            return render_template('admin/majors.html', 
                                 majors=majors,
                                 teachers=teachers)
        except Exception as e:
            return self.handle_error(e, '获取数据失败', 'admin_dashboard')
    
    def add_major(self):
        """添加专业"""
        try:
            major_data = {
                'name': request.form['name'].strip(),
                'code': request.form['code'].strip(),
                'description': request.form.get('description', '').strip()
            }
            self.dao_factory.major_dao.create(major_data)
            flash('专业添加成功')
        except Exception as e:
            return self.handle_error(e, '添加失败', 'admin_majors')
        return redirect(url_for('admin_majors'))
    
    def update_major(self, major_id):
        """更新专业信息"""
        try:
            major_data = {
                'name': request.form['name'].strip(),
                'code': request.form['code'].strip(),
                'description': request.form.get('description', '').strip()
            }
            
            # 使用事务更新专业信息和导师关联
            with self.dao_factory.major_dao.transaction_context() as cursor:
                # 更新专业基本信息
                self.dao_factory.major_dao.update(major_id, major_data)
                
                # 更新导师关联
                teacher_ids = request.form.getlist('teacher_ids[]')
                if teacher_ids:
                    # 删除原有关联
                    cursor.execute('DELETE FROM teacher_majors WHERE major_id = %s', (major_id,))
                    
                    # 添加新的关联
                    values = [(teacher_id, major_id) for teacher_id in teacher_ids]
                    cursor.executemany(
                        'INSERT INTO teacher_majors (teacher_id, major_id) VALUES (%s, %s)',
                        values
                    )
            
            flash('专业信息已更新')
        except Exception as e:
            return self.handle_error(e, '更新失败', 'admin_majors')
        return redirect(url_for('admin_majors'))
    
    def delete_major(self, major_id):
        """删除专业"""
        try:
            self.dao_factory.major_dao.delete(major_id)
            flash('专业已删除')
        except Exception as e:
            return self.handle_error(e, '删除失败', 'admin_majors')
        return redirect(url_for('admin_majors'))
    
    def update_teacher_majors(self, teacher_id):
        """更新导师的专业"""
        try:
            major_ids = request.form.getlist('major_ids[]')
            self.dao_factory.major_dao.update_teacher_majors(teacher_id, major_ids)
            flash('导师专业已更新')
        except Exception as e:
            return self.handle_error(e, '更新失败', 'admin_teachers')
        return redirect(url_for('admin_teachers'))
    
    def review_qualification(self, qual_id):
        """审核导师资格申请"""
        try:
            status = request.form['status']
            review_comment = request.form.get('review_comment', '')
            
            # 使用事务处理审核
            with self.dao_factory.qualification_dao.transaction_context() as cursor:
                # 更新审核状态
                self.dao_factory.qualification_dao.update_review(
                    qual_id, status, session['user_id'], review_comment)
                
                # 获取申请信息
                qual = self.dao_factory.qualification_dao.get_by_id(qual_id)
                if not qual:
                    raise Exception('申请记录不存在')
                
                # 更新导师状态
                if status == '已通过':
                    standards = self.dao_factory.qualification_dao.get_standards()
                    # 将中文评级转换为英文键名
                    level_map = {
                        '优秀': 'excellent',
                        '良好': 'good',
                        '合格': 'qualified',
                        '不合格': 'unqualified'
                    }
                    level_key = level_map.get(qual['review_level'], 'unqualified')
                    max_students = standards[level_key]['max_students']
                    
                    self.dao_factory.teacher_dao.update_qualification(
                        qual['teacher_id'],
                        qual_status='已通过',
                        review_level=qual['review_level'],
                        max_students=max_students
                    )
                else:
                    self.dao_factory.teacher_dao.update_qualification(
                        qual['teacher_id'],
                        qual_status='未通过',
                        max_students=0
                    )
            
            flash('审核完成')
        except Exception as e:
            print(f"审核资格申请错误: {e}")  # 添加错误日志
            return self.handle_error(e, '审核失败', 'admin_qualifications')
        
        return redirect(url_for('admin_qualifications'))
    
    def get_logs(self):
        """获取操作日志页面"""
        try:
            # 获取筛选参数
            table_name = request.args.get('table')
            operation_type = request.args.get('type')
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            
            # 获取日志数据
            logs = self.dao_factory.log_dao.get_logs_with_details(
                table_name=table_name,
                operation_type=operation_type,
                start_date=start_date,
                end_date=end_date
            )
            
            return render_template('admin/logs.html', 
                                 logs=logs,
                                 table_name=table_name,
                                 operation_type=operation_type,
                                 start_date=start_date,
                                 end_date=end_date)
        except Exception as e:
            return self.handle_error(e, '获取日志失败', 'admin_dashboard')
    
    def approve_admission(self, app_id):
        """审批录取结果"""
        try:
            status = request.form['status']
            comment = request.form.get('comment', '')
            
            # 更新审批状态
            with self.dao_factory.application_dao.transaction_context() as cursor:
                sql = '''
                    UPDATE student_applications 
                    SET approval_status = %s,
                        approval_comment = %s,
                        approval_time = CURRENT_TIMESTAMP,
                        approver_id = %s
                    WHERE id = %s
                '''
                cursor.execute(sql, (status, comment, session['user_id'], app_id))
            
            flash('审批完成')
        except Exception as e:
            return self.handle_error(e, '审批失败', 'admin_admissions')
        
        return redirect(url_for('admin_admissions'))
    
    def get_supervision(self):
        """获取过程监督页面"""
        try:
            # 获取当前阶段
            current_phase = self.dao_factory.supervision_dao.get_current_phase()
            
            # 获取所有阶段
            all_phases = self.dao_factory.supervision_dao.get_all_phases()
            
            # 获取统计数据
            stats = {}
            if current_phase:
                if current_phase['phase'] == '学生申请':
                    stats = {
                        'total_applications': len(self.dao_factory.application_dao.get_all_with_details()),
                        'pending_reviews': len([a for a in self.dao_factory.application_dao.get_all_with_details() 
                                             if a['status'] == '待处理'])
                    }
                elif current_phase['phase'] == '导师审核':
                    stats = {
                        'pending_reviews': len([a for a in self.dao_factory.application_dao.get_all_with_details() 
                                             if a['status'] == '待处理'])
                    }
                elif current_phase['phase'] == '管理员审批':
                    stats = {
                        'pending_approvals': len(self.dao_factory.application_dao.get_pending_approvals())
                    }
            
            return render_template('admin/supervision.html',
                                 current_phase=current_phase,
                                 all_phases=all_phases,
                                 stats=stats)
        except Exception as e:
            return self.handle_error(e, '获取数据失败', 'admin_dashboard')
    
    def add_supervision_phase(self):
        """添加监督阶段"""
        try:
            phase_data = {
                'phase': request.form['phase'],
                'start_time': request.form['start_time'],
                'end_time': request.form['end_time'],
                'supervisor_id': session['user_id'],
                'notes': request.form.get('notes', '')
            }
            
            # 检查时间冲突
            if self.dao_factory.supervision_dao.check_phase_conflicts(
                phase_data['start_time'], phase_data['end_time']):
                flash('时间段存在冲突')
                return redirect(url_for('admin_supervision'))
            
            # 创建阶段
            self.dao_factory.supervision_dao.create_phase(phase_data)
            flash('监督阶段已添加')
        except Exception as e:
            return self.handle_error(e, '添加失败', 'admin_supervision')
        
        return redirect(url_for('admin_supervision'))
    
    def update_supervision_status(self, phase_id):
        """更新监督阶段状态"""
        try:
            status = request.form['status']
            notes = request.form.get('notes', '')
            
            self.dao_factory.supervision_dao.update_phase_status(phase_id, status, notes)
            flash('状态已更新')
        except Exception as e:
            return self.handle_error(e, '更新失败', 'admin_supervision')
        
        return redirect(url_for('admin_supervision'))
    
    def get_admissions(self):
        """获取导师通过的申请页面"""
        try:
            # 获取需要审批的申请
            applications = self.dao_factory.application_dao.get_pending_approvals()
            
            # 获取统计信息
            stats = {
                'total': len(applications),
                'approved': len([a for a in applications if a['status'] == '已通过']),
                'pending': len([a for a in applications if a['approval_status'] == '待审批'])
            }
            
            return render_template('admin/admissions.html', 
                                 applications=applications,
                                 stats=stats)
        except Exception as e:
            return self.handle_error(e, '获取数据失败', 'admin_dashboard')