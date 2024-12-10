from flask import session, request, flash, redirect, url_for, render_template
from .base_controller import BaseController

class AuthController(BaseController):
    def login(self):
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            
            try:
                # 验证用户
                user = self.dao_factory.user_dao.authenticate(username, password)
                
                if user:
                    # 更新最后登录时间
                    self.dao_factory.user_dao.update_last_login(user['id'])
                    
                    # 设置session
                    session['user_id'] = user['id']
                    session['username'] = user['username']
                    session['role'] = user['role']
                    
                    if user.get('role_id'):
                        session['real_name'] = user.get('real_name')
                        if user['role'] == 'student':
                            session['student_id'] = user['role_id']
                            student = self.dao_factory.student_dao.get_by_user_id(user['id'])
                            if student:
                                session['student_status'] = student['status']
                        elif user['role'] == 'teacher':
                            session['teacher_id'] = user['role_id']
                    
                    flash('登录成功')
                    return redirect(url_for('index'))
                flash('用户名或密码错误')
            except Exception as e:
                return self.handle_error(e, '登录失败', 'login')
        
        return render_template('login.html')
    
    def register(self):
        if request.method == 'POST':
            username = request.form.get('username').strip()
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
            role = request.form.get('role')
            name = request.form.get('name').strip()
            
            # 验证输入
            if not all([username, password, confirm_password, role, name]):
                flash('请填写所有必填字段')
                return redirect(url_for('register'))
            
            if password != confirm_password:
                flash('两次输入的密码不一致')
                return redirect(url_for('register'))
            
            if role not in ['student', 'teacher']:
                flash('无效的用户角色')
                return redirect(url_for('register'))
            
            try:
                # 检查用户是否已存在
                if self.dao_factory.user_dao.get_by_username(username):
                    flash('用户名已存在')
                    return redirect(url_for('register'))
                
                # 使用事务创建用户
                with self.dao_factory.user_dao.transaction_context() as cursor:
                    # 创建用户账号
                    user_id = self.dao_factory.user_dao.create(username, password, role)
                    
                    # 根据角色创建相应的记录
                    if role == 'student':
                        self.dao_factory.student_dao.create(user_id, name)
                    else:  # teacher
                        self.dao_factory.teacher_dao.create(user_id, name)
                
                flash('注册成功，请登录')
                return redirect(url_for('login'))
            except Exception as e:
                return self.handle_error(e, '注册失败', 'register')
        
        return render_template('register.html')
    
    def logout(self):
        session.clear()
        return redirect(url_for('index')) 