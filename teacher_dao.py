from typing import Optional, Dict, List
from .base_dao import BaseDAO

class TeacherDAO(BaseDAO):
    def get_by_user_id(self, user_id: int) -> Optional[Dict]:
        sql = '''
            SELECT t.*, u.username,
                   (SELECT COUNT(*) FROM student_applications sa 
                    WHERE sa.teacher_id = t.id AND sa.status = '已通过') as approved_count,
                   (SELECT COUNT(*) FROM student_applications sa 
                    WHERE sa.teacher_id = t.id AND sa.status = '待处理') as pending_count
            FROM teachers t
            JOIN users u ON t.user_id = u.id
            WHERE t.user_id = %s
        '''
        return self.query_one(sql, (user_id,))
    
    def get_by_id(self, teacher_id: int) -> Optional[Dict]:
        sql = 'SELECT * FROM teachers WHERE id = %s'
        return self.query_one(sql, (teacher_id,))
    
    def get_all_qualified(self) -> List[Dict]:
        sql = '''
            SELECT t.*, 
                   (SELECT COUNT(*) FROM student_applications sa 
                    WHERE sa.teacher_id = t.id AND sa.status = '已通过') as approved_count,
                   (SELECT COUNT(*) FROM student_applications sa 
                    WHERE sa.teacher_id = t.id AND sa.status = '待处理') as pending_count
            FROM teachers t
            WHERE t.qual_status = '已通过'
            AND t.qual_expire_time > CURRENT_TIMESTAMP
            ORDER BY t.name
        '''
        return self.query_all(sql)
    
    def create(self, user_id: int, name: str, title: str = None) -> int:
        sql = '''
            INSERT INTO teachers (user_id, name, title)
            VALUES (%s, %s, %s)
        '''
        return self.execute(sql, (user_id, name, title)) 
    
    def get_students(self, teacher_id: int) -> List[Dict]:
        sql = '''
            SELECT sa.*, 
                   s.name as student_name,
                   s.initial_score,
                   s.retest_score,
                   s.phone,
                   s.email
            FROM student_applications sa
            JOIN students s ON sa.student_id = s.id
            JOIN teachers t ON sa.teacher_id = t.id
            WHERE t.id = %s
            ORDER BY sa.priority ASC, sa.create_time ASC
        '''
        return self.query_all(sql, (teacher_id,))
    
    def update_qualification(self, teacher_id: int, qual_status: str, 
                            review_level: str = None, max_students: int = 0) -> None:
        sql = '''
            UPDATE teachers 
            SET qual_status = %s,
                review_level = %s,
                qual_year = YEAR(CURRENT_DATE),
                qual_expire_time = DATE_ADD(CURRENT_TIMESTAMP, INTERVAL 3 YEAR),
                max_students = %s
            WHERE id = %s
        '''
        self.execute(sql, (qual_status, review_level, max_students, teacher_id)) 
    
    def get_all_with_stats(self) -> List[Dict]:
        """获取所有导师信息及统计数据"""
        sql = '''
            SELECT t.*, u.username,
                   (SELECT COUNT(*) FROM student_applications sa 
                    WHERE sa.teacher_id = t.id AND sa.status = '已通过') as approved_students,
                   (SELECT COUNT(*) FROM student_applications sa 
                    WHERE sa.teacher_id = t.id AND sa.status = '待处理') as pending_students
            FROM teachers t
            JOIN users u ON t.user_id = u.id
            ORDER BY t.name
        '''
        return self.query_all(sql)
    
    def update_profile(self, teacher_id: int, data: Dict) -> None:
        """更新教师信息"""
        sql = '''
            UPDATE teachers 
            SET introduction = %s,
                research_direction = %s,
                title = %s,
                name = %s
            WHERE id = %s
        '''
        with self.transaction_context() as cursor:
            # 更新基本信息
            cursor.execute(sql, (
                data.get('introduction'),
                data.get('research_direction'),
                data.get('title'),
                data.get('name'),
                teacher_id
            ))
            
            # 如果提供了专业信息，更新专业关联
            if 'major_ids' in data:
                # 删除原有关联
                cursor.execute('DELETE FROM teacher_majors WHERE teacher_id = %s', (teacher_id,))
                
                # 添加新的关联
                if data['major_ids']:
                    values = [(teacher_id, major_id) for major_id in data['major_ids']]
                    cursor.executemany(
                        'INSERT INTO teacher_majors (teacher_id, major_id) VALUES (%s, %s)',
                        values
                    )
    
    def check_student_count(self, teacher_id: int) -> int:
        sql = '''
            SELECT COUNT(*) as count 
            FROM student_applications 
            WHERE teacher_id = %s AND status = '已通过'
        '''
        result = self.query_one(sql, (teacher_id,))
        return result['count'] if result else 0
    
    def get_all_with_applications(self) -> Dict[str, List[Dict]]:
        """获取所有教师信息及待审核的资格申请"""
        teachers = self.get_all_with_stats()
        
        # 获取待审核的资格申请
        sql = '''
            SELECT tq.*, t.name as teacher_name
            FROM teacher_qualifications tq
            JOIN teachers t ON tq.teacher_id = t.id
            WHERE tq.status = '待审核'
            ORDER BY tq.create_time DESC
        '''
        qualifications = self.query_all(sql)
        
        return {
            'teachers': teachers,
            'qualifications': qualifications
        }
    
    def delete(self, teacher_id: int) -> None:
        """删除教师及相关记录"""
        operations = [
            ('DELETE FROM student_applications WHERE teacher_id = %s', (teacher_id,)),
            ('DELETE FROM draw_lots WHERE teacher_id = %s', (teacher_id,)),
            ('DELETE FROM teacher_qualifications WHERE teacher_id = %s', (teacher_id,)),
            ('DELETE FROM teachers WHERE id = %s', (teacher_id,))
        ]
        self.transaction(operations)
    
    def get_qualified_teachers(self) -> List[Dict]:
        """获取已通过资格审核的导师列表"""
        sql = '''
            SELECT t.*, u.username,
                   (SELECT COUNT(*) FROM student_applications sa 
                    WHERE sa.teacher_id = t.id AND sa.status = '已通过') as approved_count,
                   (SELECT COUNT(*) FROM student_applications sa 
                    WHERE sa.teacher_id = t.id AND sa.status = '待处理') as pending_count,
                   tq.review_level, tq.score
            FROM teachers t
            JOIN users u ON t.user_id = u.id
            JOIN teacher_qualifications tq ON t.id = tq.teacher_id
            WHERE t.qual_status = '已通过'
            AND t.qual_expire_time > CURRENT_TIMESTAMP
            AND tq.status = '已通过'
            AND tq.year = YEAR(CURRENT_DATE)
            ORDER BY t.name
        '''
        return self.query_all(sql)
    
    def update_quota(self, teacher_id: int, data: Dict) -> None:
        """更新导师招生名额"""
        sql = '''
            UPDATE teachers 
            SET max_students = %s,
                quota_status = %s,
                quota_year = %s,
                quota_comment = %s
            WHERE id = %s
        '''
        self.execute(sql, (
            data['max_students'],
            data['quota_status'],
            data['quota_year'],
            data.get('quota_comment'),
            teacher_id
        ))
    
    def batch_update_quota(self, teacher_quotas: List[Dict]) -> None:
        """批量更新导师招生名额"""
        operations = []
        for quota in teacher_quotas:
            operations.append((
                '''UPDATE teachers 
                   SET max_students = %s,
                       quota_status = %s,
                       quota_year = %s
                   WHERE id = %s''',
                (quota['max_students'], quota['quota_status'], 
                 quota['quota_year'], quota['teacher_id'])
            ))
        self.transaction(operations)