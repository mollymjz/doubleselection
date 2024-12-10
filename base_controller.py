from flask import flash, redirect, url_for
from functools import wraps

class BaseController:
    def __init__(self, dao_factory):
        self.dao_factory = dao_factory
    
    def handle_error(self, e: Exception, error_msg: str, redirect_url: str):
        """统一错误处理"""
        flash(error_msg)
        print(f"{error_msg}: {e}")
        return redirect(url_for(redirect_url)) 