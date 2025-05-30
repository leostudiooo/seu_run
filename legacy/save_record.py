import requests
import logging

# 获取logger
logger = logging.getLogger(__name__)

class DataUploader:
    """
    用于将运动数据上传到服务器的类
    """
    def __init__(self, config, data_content):
        """
        初始化数据上传器
        
        Args:
            config: 包含配置信息的字典
            data_content: 包含数据内容的字典
        """
        self.config = config
        self.data_content = data_content
        logger.debug(f"DataUploader initialized with config: {config}")
    
    def prepare_payload(self):
        """
        准备要发送的数据负载
        """
        logger.debug(f"Preparing payload with data_content: {self.data_content}")
        
        # 复制配置中的data字段
        payload = self.config['data'].copy()
        
        # 设置位置信息
        payload['strLatitudeLongitude'] = self.data_content
        
        logger.debug(f"Prepared payload: {payload}")
        return payload
    
    def send_request(self):
        """
        发送请求到服务器
        """
        # 获取配置中的URL和headers
        url = self.config['url']
        headers = self.config['headers']
        
        # 设置请求头
        headers['content-type'] = 'application/json;charset=utf-8'
        headers['Referer'] = 'https://servicewechat.com/wx5da07e9f6f45cabf/38/page-frame.html'
        headers['charset'] = 'utf-8'
        
        logger.debug(f"Sending request to URL: {url}")
        
        # 准备数据
        data = self.prepare_payload()
        
        # 设置运动参数
        data['maxTime'] = 12
        data['minTime'] = 4
        data['orouteKilometre'] = 1.2
        data['ruleEndTime'] = '22:00'
        data['ruleStartTime'] = '06:00'
        data['nowStatus'] = 2
        
        logger.debug(f"Request data: {data}")
        
        try:
            # 发送POST请求
            response = requests.post(
                url,
                headers=headers,
                json=data,
                verify=False
            )
            
            logger.info(f"Request sent successfully. Status Code: {response.status_code}")
            logger.debug(f"Response: {response.text}")
            
            return response
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise
    
    def run(self):
        """
        执行数据上传操作
        """
        try:
            return self.send_request()
        except Exception as e:
            logger.error(f"Failed to send request: {e}")
            raise