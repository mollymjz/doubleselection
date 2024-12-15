from typing import List, Dict, Optional
from .base_dao import BaseDAO

class MajorDAO(BaseDAO):
    def get_all(self) -> List[Dict]:
        """获取所有专业"""
        sql = 'SELECT * FROM majors ORDER BY code'
        return self.query_all(sql)
    
    def get_with_teachers(self) -> List[Dict]:
        """获取所有专业及其导师"""
        sql = '''
            SELECT m.*, 
                   COALESCE(
                       JSON_ARRAYAGG(
                           IF(t.id IS NOT NULL,
                               JSON_OBJECT(
                                   'id', t.id,
                                   'name', t.name,
                                   'title', t.title,
                                   'research_direction', t.research_direction,
                                   'max_students', t.max_students,
                                   'qual_status', t.qual_status
                               ),
                               NULL
                           )
                       ),
                       '[]'
                   ) as teachers
            FROM majors m
            LEFT JOIN teacher_majors tm ON m.id = tm.major_id
            LEFT JOIN teachers t ON tm.teacher_id = t.id AND t.qual_status = '已通过'
            GROUP BY m.id, m.name, m.code, m.description
            ORDER BY m.code
        '''
        result = self.query_all(sql)
        
        # 处理 teachers 字段
        for major in result:
            if major['teachers'] is None:
                major['teachers'] = '[]'
            elif isinstance(major['teachers'], str):
                # 确保是有效的 JSON 字符串
                try:
                    import json
                    teachers = json.loads(major['teachers'])
                    # 过滤掉 NULL 值
                    teachers = [t for t in teachers if t is not None]
                    major['teachers'] = json.dumps(teachers)
                except:
                    major['teachers'] = '[]'
        
        return result
    
    def get_teacher_majors(self, teacher_id: int) -> List[Dict]:
        """获取导师的专业列表"""
        sql = '''
            SELECT m.* 
            FROM majors m
            JOIN teacher_majors tm ON m.id = tm.major_id
            WHERE tm.teacher_id = %s
            ORDER BY m.code
        '''
        return self.query_all(sql, (teacher_id,)) 

    def create(self, data: Dict) -> int:
        """创建专业"""
        sql = '''
            INSERT INTO majors (name, code, description)
            VALUES (%s, %s, %s)
        '''
        return self.execute(sql, (data['name'], data['code'], data['description']))

    def update(self, major_id: int, data: Dict) -> None:
        """更新专业信息"""
        sql = '''
            UPDATE majors 
            SET name = %s,
                code = %s,
                description = %s
            WHERE id = %s
        '''
        self.execute(sql, (data['name'], data['code'], data['description'], major_id))

    def delete(self, major_id: int) -> None:
        """删除专业"""
        sql = 'DELETE FROM majors WHERE id = %s'
        self.execute(sql, (major_id,))

    def update_teacher_majors(self, teacher_id: int, major_ids: List[int]) -> None:
        """更新导师的专业"""
        with self.transaction_context() as cursor:
            # 删除原有关联
            cursor.execute('DELETE FROM teacher_majors WHERE teacher_id = %s', (teacher_id,))
            
            # 添加新的关联
            if major_ids:
                values = [(teacher_id, major_id) for major_id in major_ids]
                cursor.executemany(
                    'INSERT INTO teacher_majors (teacher_id, major_id) VALUES (%s, %s)',
                    values
                )

    def get_major_teachers(self, major_id: int) -> List[Dict]:
        """获取专业的导师列表"""
        sql = '''
            SELECT t.id, t.name, t.title
            FROM teachers t
            JOIN teacher_majors tm ON t.id = tm.teacher_id
            WHERE tm.major_id = %s
            ORDER BY t.name
        '''
        return self.query_all(sql, (major_id,))

    def get_all_with_teachers(self) -> List[Dict]:
        """获取所有专业及其导师"""
        sql = '''
            SELECT m.*, 
                   (SELECT GROUP_CONCAT(t.id) 
                    FROM teacher_majors tm 
                    JOIN teachers t ON tm.teacher_id = t.id 
                    WHERE tm.major_id = m.id) as teacher_ids
            FROM majors m
            ORDER BY m.code
        '''
        return self.query_all(sql)