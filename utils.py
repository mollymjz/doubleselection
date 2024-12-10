from functools import wraps
from flask import session, redirect, url_for, flash

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('请先登录')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'role' not in session:
                flash('请先登录')
                return redirect(url_for('login'))
            
            allowed_roles = roles if isinstance(roles, (list, tuple)) else [roles]
            
            if session['role'] not in allowed_roles:
                flash('无权限访问')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def format_datetime(value, format='%Y-%m-%d %H:%M:%S'):
    """格式化日期时间"""
    if value is None:
        return ''
    return value.strftime(format)

def format_score(value):
    """格式化分数"""
    if value is None:
        return '0'
    return f'{value:.1f}'