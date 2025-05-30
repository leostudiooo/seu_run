import requests
import logging

# 获取logger
logger = logging.getLogger(__name__)

class SEUSportsClient:
    """东南大学体育系统客户端"""
    
    BASE_URL = 'https://tyxsjpt.seu.edu.cn'
    
    def __init__(self, token, tenant, user_agent, student_id):
        """
        初始化客户端
        
        Args:
            token: 认证令牌
            tenant: 租户信息
            user_agent: 用户代理
            student_id: 学生ID
        """
        self.token = token
        self.tenant = tenant
        self.user_agent = user_agent
        self.student_id = student_id
        self.headers = self._get_default_headers()
    
    def _get_default_headers(self):
        """获取默认请求头"""
        return {
            'Host': 'tyxsjpt.seu.edu.cn',
            'charset': 'utf-8',
            'token': f'Bearer {self.token}',
            'content-type': 'application/json;charset=utf-8',
            'miniappversion': 'minappv3.0.1',
            'User-Agent': self.user_agent,
            'tenant': self.tenant,
            'Referer': 'https://servicewechat.com/wx5da07e9f6f45cabf/38/page-frame.html'
        }
    
    def save_start_record(self, route_name, rule_id, plan_id, record_date, start_time, 
                          start_image, route_rule, max_time=12, min_time=4, 
                          route_kilometre=1.2, rule_end_time='22:00', rule_start_time='6:00'):
        """
        保存运动开始记录
        
        Args:
            route_name: 路线名称
            rule_id: 规则ID
            plan_id: 计划ID
            record_date: 记录日期 (格式: YYYY-MM-DD)
            start_time: 开始时间 (格式: HH:MM:SS)
            start_image: 开始图片URL
            route_rule: 路线规则
            max_time: 最大时间(分钟)
            min_time: 最小时间(分钟)
            route_kilometre: 路线公里数
            rule_end_time: 规则结束时间
            rule_start_time: 规则开始时间
            
        Returns:
            响应对象
            
        Raises:
            requests.exceptions.RequestException: 当请求失败时抛出
        """
        url = f"{self.BASE_URL}/api/exercise/exerciseRecord/saveStartRecord"
        
        # 构建请求数据
        payload = {
            'routeName': route_name,
            'ruleId': rule_id,
            'planId': plan_id,
            'recordTime': record_date,
            'startTime': start_time,
            'startImage': start_image,
            'endTime': '',
            'exerciseTimes': '',
            'routeKilometre': '',
            'endImage': '',
            'strLatitudeLongitude': [],
            'routeRule': route_rule,
            'maxTime': max_time,
            'minTime': min_time,
            'orouteKilometre': route_kilometre,
            'ruleEndTime': rule_end_time,
            'ruleStartTime': rule_start_time,
            'calorie': 0,
            'speed': "0'00''",
            'dispTimeText': 0,
            'studentId': self.student_id
        }
        
        logger.debug(f"Sending request to {url} with payload: {payload}")
        
        try:
            # 发送POST请求
            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                verify=False  # 不验证SSL证书
            )
            
            # 检查是否有错误状态
            response.raise_for_status()
            
            logger.debug(f"Request successful: {response.json()}")
            return response
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            # 继续抛出异常供调用者处理
            raise