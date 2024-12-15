from typing import List, Dict, Optional
from .base_dao import BaseDAO
import json

class LogDAO(BaseDAO):
    def get_logs_with_details(self, table_name=None, operation_type=None, 
                            start_date=None, end_date=None) -> List[Dict]:
        """获取操作日志及相关详情"""
        sql = '''
            SELECT l.*,
                   u.username as operator_name,
                   CASE l.table_name
                       WHEN 'student_applications' THEN (
                           SELECT CONCAT(s.name, ' -> ', t.name)
                           FROM student_applications sa
                           JOIN students s ON sa.student_id = s.id
                           JOIN teachers t ON sa.teacher_id = t.id
                           WHERE sa.id = l.record_id
                       )
                       WHEN 'teacher_qualifications' THEN (
                           SELECT t.name
                           FROM teacher_qualifications tq
                           JOIN teachers t ON tq.teacher_id = t.id
                           WHERE tq.id = l.record_id
                       )
                       WHEN 'teachers' THEN (
                           SELECT name FROM teachers WHERE id = l.record_id
                       )
                       WHEN 'students' THEN (
                           SELECT name FROM students WHERE id = l.record_id
                       )
                       ELSE NULL
                   END as record_name
            FROM operation_logs l
            LEFT JOIN users u ON l.operator_id = u.id
            WHERE 1=1
        '''
        params = []
        
        if table_name:
            sql += ' AND l.table_name = %s'
            params.append(table_name)
        
        if operation_type:
            sql += ' AND l.operation_type = %s'
            params.append(operation_type)
        
        if start_date:
            sql += ' AND DATE(l.operation_time) >= %s'
            params.append(start_date)
        
        if end_date:
            sql += ' AND DATE(l.operation_time) <= %s'
            params.append(end_date)
        
        sql += ' ORDER BY l.operation_time DESC'
        
        logs = self.query_all(sql, tuple(params) if params else None)
        
        # 处理JSON数据
        for log in logs:
            if log['old_data']:
                try:
                    log['old_data'] = json.loads(log['old_data'])
                except:
                    log['old_data'] = {}
            
            if log['new_data']:
                try:
                    log['new_data'] = json.loads(log['new_data'])
                except:
                    log['new_data'] = {}
        
        return logs 