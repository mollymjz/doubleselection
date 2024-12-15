from typing import Optional, Dict, List
from .base_dao import BaseDAO

class StudentDAO(BaseDAO):
    def get_by_user_id(self, user_id: int) -> Optional[Dict]:
        sql = '''
            SELECT s.*, u.username 
            FROM students s
            JOIN users u ON s.user_id = u.id
            WHERE s.user_id = %s
        '''
        return self.query_one(sql, (user_id,))
    
    def get_by_id(self, student_id: int) -> Optional[Dict]:
        sql = 'SELECT * FROM students WHERE id = %s'
        return self.query_one(sql, (student_id,))
    
    def create(self, user_id: int, name: str, status: str = '待审核') -> int:
        sql = '''
            INSERT INTO students (user_id, name, status)
            VALUES (%s, %s, %s)
        '''
        return self.execute(sql, (user_id, name, status))
    
    def update(self, student_id: int, data: Dict) -> None:
        set_clause = ', '.join(f'{k} = %s' for k in data.keys())
        sql = f'UPDATE students SET {set_clause} WHERE id = %s'
        params = tuple(data.values()) + (student_id,)
        self.execute(sql, params)
    
    def get_applications(self, student_id: int) -> List[Dict]:
        sql = '''
            SELECT sa.*, t.name as teacher_name, t.title,
                   t.research_direction
            FROM student_applications sa
            JOIN teachers t ON sa.teacher_id = t.id
            WHERE sa.student_id = %s
            ORDER BY sa.create_time DESC
        '''
        return self.query_all(sql, (student_id,)) 
    
    def get_all_with_stats(self) -> List[Dict]:
        sql = '''
            SELECT s.*, u.username,
                   (SELECT COUNT(*) FROM student_applications sa 
                    WHERE sa.student_id = s.id AND sa.status = '已通过') as matched_count,
                   (SELECT COUNT(*) FROM student_applications sa 
                    WHERE sa.student_id = s.id AND sa.status = '待处理') as pending_count
            FROM students s
            JOIN users u ON s.user_id = u.id
            ORDER BY s.name
        '''
        return self.query_all(sql)
    
    def delete(self, student_id: int) -> None:
        """删除学生及相关记录"""
        operations = [
            ('DELETE FROM student_applications WHERE student_id = %s', (student_id,)),
            ('DELETE FROM draw_lots WHERE student_id = %s', (student_id,)),
            ('DELETE FROM students WHERE id = %s', (student_id,))
        ]
        self.transaction(operations)
    
    def check_application_count(self, student_id: int) -> int:
        sql = '''
            SELECT COUNT(*) as count 
            FROM student_applications 
            WHERE student_id = %s
        '''
        result = self.query_one(sql, (student_id,))
        return result['count'] if result else 0 