from typing import Optional, Dict, List
from .base_dao import BaseDAO
import json

class QualificationDAO(BaseDAO):
    def create(self, teacher_id: int, data: Dict) -> int:
        """创建资格申请"""
        sql = '''
            INSERT INTO teacher_qualifications (
                teacher_id, year, sci_papers, ei_papers, core_papers,
                national_projects, province_projects, other_projects,
                research_funds, awards, students_count,
                score, score_detail, review_level, status
            ) VALUES (
                %s, YEAR(CURRENT_DATE), %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s, '待审核'
            )
        '''
        params = (
            teacher_id,
            data['sci_papers'], 
            data['ei_papers'], 
            data['core_papers'],
            data['national_projects'], 
            data['province_projects'], 
            data['other_projects'],
            data['research_funds'], 
            data['awards'], 
            data['students_count'],
            data['score'], 
            json.dumps(data['score_detail']),  # 将字典转换为JSON字符串
            data['review_level']
        )
        return self.execute(sql, params)
    
    def get_by_id(self, qual_id: int) -> Optional[Dict]:
        sql = '''
            SELECT tq.*, t.name as teacher_name,
                   t.title, u.username as reviewer_name
            FROM teacher_qualifications tq
            JOIN teachers t ON tq.teacher_id = t.id
            LEFT JOIN users u ON tq.reviewer_id = u.id
            WHERE tq.id = %s
        '''
        return self.query_one(sql, (qual_id,))
    
    def get_pending_reviews(self) -> List[Dict]:
        sql = '''
            SELECT tq.*, t.name as teacher_name, t.title
            FROM teacher_qualifications tq
            JOIN teachers t ON tq.teacher_id = t.id
            WHERE tq.status = '待审核'
            ORDER BY tq.create_time DESC
        '''
        return self.query_all(sql)
    
    def update_review(self, qual_id: int, status: str, reviewer_id: int, 
                     comment: str = None) -> None:
        sql = '''
            UPDATE teacher_qualifications 
            SET status = %s,
                review_comment = %s,
                reviewer_id = %s,
                review_time = CURRENT_TIMESTAMP
            WHERE id = %s
        '''
        self.execute(sql, (status, comment, reviewer_id, qual_id))
    
    def check_year_application(self, teacher_id: int, year: int) -> bool:
        sql = '''
            SELECT id FROM teacher_qualifications 
            WHERE teacher_id = %s AND year = %s
        '''
        result = self.query_one(sql, (teacher_id, year))
        return bool(result)
    
    def get_all_with_details(self) -> List[Dict]:
        """获取所有资格申请及详情"""
        sql = '''
            SELECT tq.*, 
                   t.name as teacher_name,
                   t.title,
                   u.username as reviewer_name,
                   CAST(tq.score_detail AS CHAR) as score_detail_str
            FROM teacher_qualifications tq
            JOIN teachers t ON tq.teacher_id = t.id
            LEFT JOIN users u ON tq.reviewer_id = u.id
            ORDER BY tq.create_time DESC
        '''
        result = self.query_all(sql)
        
        # 处理 score_detail 字段
        for qual in result:
            if qual['score_detail_str']:
                try:
                    qual['score_detail'] = json.loads(qual['score_detail_str'])
                except:
                    qual['score_detail'] = {}
            else:
                qual['score_detail'] = {}
            del qual['score_detail_str']  # 删除临时字段
        
        return result
    
    def calculate_score(self, data: Dict) -> Dict:
        """计算资格评分"""
        score_detail = {
            '论文分': {
                'SCI论文': data['sci_papers'] * 20,
                'EI论文': data['ei_papers'] * 15,
                '核心期刊': data['core_papers'] * 10
            },
            '项目分': {
                '国家级项目': data['national_projects'] * 30,
                '省部级项目': data['province_projects'] * 20,
                '其他项目': data['other_projects'] * 10
            },
            '其他分': {
                '科研经费': min(int(data['research_funds'] * 2), 50),
                '研究生培养': data['students_count'] * 5
            }
        }
        
        total_score = sum([sum(v.values()) for v in score_detail.values()])
        return {
            'score': total_score,
            'score_detail': score_detail
        }
    
    def get_review_level(self, score: int) -> str:
        """根据分数获取评级等级"""
        standards = self.get_standards()
        if score >= standards['excellent']['min_score']:
            return '优秀'
        elif score >= standards['good']['min_score']:
            return '良好'
        elif score >= standards['qualified']['min_score']:
            return '合格'
        return '不合格'
    
    def get_standards(self) -> Dict:
        """获取评级标准"""
        sql = '''
            SELECT config_value 
            FROM system_configs 
            WHERE config_key = 'qualification_standards'
        '''
        result = self.query_one(sql)
        if result:
            standards = json.loads(result['config_value'])
            # 创建评级等级映射
            level_map = {
                'excellent': '优秀',
                'good': '良好',
                'qualified': '合格',
                'unqualified': '不合格'
            }
            # 添加中文名称到标准中
            for key, value in standards.items():
                value['name_zh'] = level_map.get(key, key)
            return standards
        return {}
    
    def get_teacher_status(self, teacher_id: int) -> Dict:
        """获取教师资格状态信息"""
        sql = '''
            SELECT t.qual_status, t.review_level, t.qual_year, t.qual_expire_time,
                   q.* 
            FROM teachers t
            LEFT JOIN teacher_qualifications q ON q.teacher_id = t.id 
            AND q.year = YEAR(CURRENT_DATE)
            WHERE t.id = %s
        '''
        return self.query_one(sql, (teacher_id,))
    
    def update(self, qual_id: int, data: Dict) -> None:
        """更新资格申请信息"""
        sql = '''
            UPDATE teacher_qualifications 
            SET sci_papers = %s,
                ei_papers = %s,
                core_papers = %s,
                national_projects = %s,
                province_projects = %s,
                other_projects = %s,
                research_funds = %s,
                awards = %s,
                students_count = %s,
                score = %s,
                score_detail = %s,
                review_level = %s,
                update_time = CURRENT_TIMESTAMP
            WHERE id = %s
        '''
        self.execute(sql, (
            data['sci_papers'], data['ei_papers'], data['core_papers'],
            data['national_projects'], data['province_projects'], data['other_projects'],
            data['research_funds'], data['awards'], data['students_count'],
            data['score'], json.dumps(data['score_detail']), data['review_level'],
            qual_id
        ))