from typing import Optional, Dict, List
from .base_dao import BaseDAO

class DrawLotsDAO(BaseDAO):
    def create(self, teacher_id: int, student_id: int, result: str) -> int:
        sql = '''
            INSERT INTO draw_lots (teacher_id, student_id, result)
            VALUES (%s, %s, %s)
        '''
        return self.execute(sql, (teacher_id, student_id, result))
    
    def get_draw_history(self, teacher_id: int, student_id: int) -> List[Dict]:
        sql = '''
            SELECT * FROM draw_lots
            WHERE teacher_id = %s AND student_id = %s
            ORDER BY draw_time DESC
        '''
        return self.query_all(sql, (teacher_id, student_id))
    
    def get_available_students(self, teacher_id: int) -> List[Dict]:
        sql = '''
            SELECT DISTINCT s.*, 
                   s.initial_score + s.retest_score as total_score,
                   (SELECT COUNT(*) FROM draw_lots dl 
                    WHERE dl.student_id = s.id 
                    AND dl.teacher_id = %s) as draw_count,
                   (SELECT result FROM draw_lots dl 
                    WHERE dl.student_id = s.id 
                    AND dl.teacher_id = %s 
                    ORDER BY draw_time DESC LIMIT 1) as last_result
            FROM students s
            LEFT JOIN student_applications sa ON s.id = sa.student_id
            WHERE s.status = '已通过'
            AND NOT EXISTS (
                SELECT 1 FROM student_applications sa2 
                WHERE sa2.student_id = s.id 
                AND sa2.status = '已通过'
            )
            AND NOT EXISTS (
                SELECT 1 FROM student_applications sa3 
                WHERE sa3.student_id = s.id 
                AND sa3.teacher_id = %s
            )
            ORDER BY total_score DESC
        '''
        return self.query_all(sql, (teacher_id, teacher_id, teacher_id)) 