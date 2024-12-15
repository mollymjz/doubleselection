from typing import Optional, Dict, List
from .base_dao import BaseDAO

class ApplicationDAO(BaseDAO):
    def create(self, student_id: int, teacher_id: int, priority: int,
              personal_statement: str = '', research_interest: str = '',
              apply_reason: str = '') -> int:
        sql = '''
            INSERT INTO student_applications (
                student_id, teacher_id, priority,
                personal_statement, research_interest, apply_reason,
                status
            ) VALUES (
                %s, %s, %s, %s, %s, %s, '待处理'
            )
        '''
        return self.execute(sql, (
            student_id, teacher_id, priority,
            personal_statement, research_interest, apply_reason
        ))
    
    def get_by_id(self, app_id: int) -> Optional[Dict]:
        sql = '''
            SELECT sa.*, s.name as student_name, t.name as teacher_name
            FROM student_applications sa
            JOIN students s ON sa.student_id = s.id
            JOIN teachers t ON sa.teacher_id = t.id
            WHERE sa.id = %s
        '''
        return self.query_one(sql, (app_id,))
    
    def update_status(self, app_id: int, status: str, comment: str = None) -> None:
        sql = '''
            UPDATE student_applications 
            SET status = %s,
                process_comment = %s,
                process_time = CURRENT_TIMESTAMP
            WHERE id = %s
        '''
        self.execute(sql, (status, comment, app_id)) 
    
    def get_by_student_teacher(self, student_id: int, teacher_id: int) -> Optional[Dict]:
        sql = '''
            SELECT * FROM student_applications 
            WHERE student_id = %s AND teacher_id = %s
        '''
        return self.query_one(sql, (student_id, teacher_id))
    
    def get_all_with_details(self) -> List[Dict]:
        sql = '''
            SELECT sa.*, 
                   s.name as student_name,
                   t.name as teacher_name,
                   s.initial_score,
                   s.retest_score
            FROM student_applications sa
            JOIN students s ON sa.student_id = s.id
            JOIN teachers t ON sa.teacher_id = t.id
            ORDER BY sa.create_time DESC
        '''
        return self.query_all(sql)
    
    def reject_other_applications(self, student_id: int, except_id: int) -> None:
        sql = '''
            UPDATE student_applications 
            SET status = '未通过',
                process_time = CURRENT_TIMESTAMP,
                process_comment = '已被其他导师录取'
            WHERE student_id = %s AND id != %s
        '''
        self.execute(sql, (student_id, except_id))
    
    def delete(self, app_id: int) -> None:
        sql = 'DELETE FROM student_applications WHERE id = %s'
        self.execute(sql, (app_id,)) 
    
    def get_statistics(self) -> Dict:
        """获取申请统计信息"""
        sql = '''
            SELECT 
                COUNT(*) as total_applications,
                SUM(CASE WHEN status = '待处理' THEN 1 ELSE 0 END) as pending_count,
                SUM(CASE WHEN status = '已通过' THEN 1 ELSE 0 END) as approved_count,
                SUM(CASE WHEN status = '未通过' THEN 1 ELSE 0 END) as rejected_count
            FROM student_applications
        '''
        return self.query_one(sql) or {}
    
    def get_teacher_applications(self, teacher_id: int) -> List[Dict]:
        """获取导师的所有申请"""
        sql = '''
            SELECT sa.*, s.name as student_name, s.initial_score, s.retest_score
            FROM student_applications sa
            JOIN students s ON sa.student_id = s.id
            WHERE sa.teacher_id = %s
            ORDER BY sa.priority ASC, sa.create_time DESC
        '''
        return self.query_all(sql, (teacher_id,))
    
    def get_pending_approvals(self) -> List[Dict]:
        """获取导师通过的申请"""
        sql = '''
            SELECT sa.*, 
                   s.name as student_name,
                   s.initial_score,
                   s.retest_score,
                   t.name as teacher_name,
                   t.title as teacher_title,
                   t.max_students
            FROM student_applications sa
            JOIN students s ON sa.student_id = s.id
            JOIN teachers t ON sa.teacher_id = t.id
            WHERE sa.status = '已通过'
            ORDER BY sa.create_time DESC
        '''
        return self.query_all(sql)