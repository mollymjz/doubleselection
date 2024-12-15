from typing import List, Dict, Optional
from .base_dao import BaseDAO
from datetime import datetime

class SupervisionDAO(BaseDAO):
    def create_phase(self, data: Dict) -> int:
        """创建监督阶段"""
        sql = '''
            INSERT INTO process_supervision (
                phase, start_time, end_time, status,
                supervisor_id, notes
            ) VALUES (
                %s, %s, %s, '进行中', %s, %s
            )
        '''
        return self.execute(sql, (
            data['phase'],
            data['start_time'],
            data['end_time'],
            data['supervisor_id'],
            data.get('notes', '')
        ))
    
    def get_current_phase(self) -> Optional[Dict]:
        """获取当前进行中的阶段"""
        sql = '''
            SELECT ps.*, u.username as supervisor_name
            FROM process_supervision ps
            LEFT JOIN users u ON ps.supervisor_id = u.id
            WHERE ps.status = '进行中'
            ORDER BY ps.start_time DESC
            LIMIT 1
        '''
        return self.query_one(sql)
    
    def get_all_phases(self) -> List[Dict]:
        """获取所有阶段"""
        sql = '''
            SELECT ps.*, u.username as supervisor_name,
                   (SELECT COUNT(*) FROM supervision_logs sl WHERE sl.supervision_id = ps.id) as log_count,
                   (SELECT GROUP_CONCAT(sl.comment SEPARATOR '\\n') 
                    FROM supervision_logs sl 
                    WHERE sl.supervision_id = ps.id
                    ORDER BY sl.action_time DESC) as logs
            FROM process_supervision ps
            LEFT JOIN users u ON ps.supervisor_id = u.id
            ORDER BY ps.start_time DESC
        '''
        phases = self.query_all(sql)
        
        # 处理日志文本
        for phase in phases:
            if phase.get('logs'):
                phase['logs'] = phase['logs'].split('\n')
            else:
                phase['logs'] = []
        
        return phases
    
    def update_phase_status(self, phase_id: int, status: str, notes: str = None) -> None:
        """更新阶段状态"""
        sql = '''
            UPDATE process_supervision 
            SET status = %s,
                notes = CASE WHEN %s IS NOT NULL THEN %s ELSE notes END
            WHERE id = %s
        '''
        self.execute(sql, (status, notes, notes, phase_id))
    
    def check_phase_conflicts(self, start_time: str, end_time: str) -> bool:
        """检查时间段是否有冲突"""
        sql = '''
            SELECT COUNT(*) as count
            FROM process_supervision
            WHERE (start_time BETWEEN %s AND %s
                   OR end_time BETWEEN %s AND %s
                   OR %s BETWEEN start_time AND end_time
                   OR %s BETWEEN start_time AND end_time)
            AND status != '已结束'
        '''
        result = self.query_one(sql, (
            start_time, end_time,
            start_time, end_time,
            start_time, end_time
        ))
        return result['count'] > 0
    
    def get_phase_logs(self, phase_id: int) -> List[Dict]:
        """获取阶段日志"""
        sql = '''
            SELECT sl.*, u.username as operator_name
            FROM supervision_logs sl
            LEFT JOIN users u ON sl.operator_id = u.id
            WHERE sl.supervision_id = %s
            ORDER BY sl.action_time DESC
        '''
        return self.query_all(sql, (phase_id,)) 