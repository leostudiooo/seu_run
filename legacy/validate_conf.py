import yaml
import os
import datetime
import re
import requests
import json
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()],
    encoding='utf-8'
)
logger = logging.getLogger(__name__)

class ConfigValidator:
    def __init__(self, config_path):
        """初始化配置验证器"""
        self.config_path = config_path
        self.config = None
        self.basic = None
        self.advanced = None
        self.errors = []
        logger.debug(f"初始化配置验证器，配置文件路径: {config_path}")

    def load_config(self):
        """加载并解析YAML配置文件"""
        logger.debug("开始加载配置文件...")
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
                self.basic = self.config.get('basic', {})
                self.advanced = self.config.get('advanced', {})
                
            logger.debug("配置文件加载成功")
            return True
            
        except Exception as e:
            error_msg = f"YAML格式错误: {e}"
            logger.error(error_msg)
            self.errors.append(error_msg)
            return False

    def validate_basic_fields(self):
        """验证所有必需的基本字段是否存在"""
        logger.debug("开始验证基础字段...")
        
        if not self.basic:
            error_msg = "缺少basic字段"
            logger.error(error_msg)
            self.errors.append(error_msg)
            return False
        
        # 检查必需字段
        required_fields = [
            'token', 'student_id', 'start_image', 'finish_image',
            'date', 'start_time', 'finish_time', 'distance', 'calorie'
        ]
        
        # 找出缺少的字段
        missing_fields = [field for field in required_fields if field not in self.basic]
        
        if missing_fields:
            error_msg = f"缺少以下必要字段: {', '.join(missing_fields)}"
            logger.error(error_msg)
            self.errors.append(error_msg)
            return False
            
        logger.debug("基础字段验证通过")
        return True

    def validate_file_paths(self):
        """验证图片文件路径是否存在"""
        logger.debug("开始验证文件路径...")
        
        is_valid = True
        
        # 检查图片文件
        for field_name in ['start_image', 'finish_image']:
            file_path = self.basic.get(field_name, '')
            
            if not os.path.isfile(file_path):
                error_msg = f"{field_name} 文件不存在: {file_path}"
                logger.error(error_msg)
                self.errors.append(error_msg)
                is_valid = False
            else:
                logger.debug(f"{field_name} 文件验证通过: {file_path}")
                
        return is_valid

    def validate_date_format(self):
        """验证日期格式"""
        date_str = self.basic.get('date', '')
        logger.debug(f"开始验证日期格式: {date_str}")
        
        try:
            # 尝试解析日期
            datetime.datetime.strptime(date_str, '%Y-%m-%d')
            logger.debug("日期格式验证通过")
            return True
            
        except ValueError:
            error_msg = f"日期格式错误，必须是 YYYY-MM-DD: {date_str}"
            logger.error(error_msg)
            self.errors.append(error_msg)
            return False

    def validate_time_formats(self):
        """验证时间格式"""
        logger.debug("开始验证时间格式...")
        
        is_valid = True
        
        # 检查时间字段
        for field_name in ['start_time', 'finish_time']:
            time_str = self.basic.get(field_name, '')
            logger.debug(f"验证 {field_name}: {time_str}")
            
            # 先用正则检查格式
            if not re.fullmatch(r'\d{2}:\d{2}:\d{2}', time_str):
                error_msg = f"{field_name} 时间格式错误，必须是 HH:MM:SS：{time_str}"
                logger.error(error_msg)
                self.errors.append(error_msg)
                is_valid = False
                continue
                
            # 再检查时间值是否合法
            try:
                datetime.datetime.strptime(time_str, '%H:%M:%S')
                logger.debug(f"{field_name} 时间格式验证通过")
            except ValueError:
                error_msg = f"{field_name} 时间值非法：{time_str}"
                logger.error(error_msg)
                self.errors.append(error_msg)
                is_valid = False
                
        return is_valid

    def validate_token(self):
        """通过向API发送请求来验证token"""
        token = self.basic.get('token', '')
        logger.debug("开始验证Token...")
        
        if not token:
            error_msg = "Token为空"
            logger.error(error_msg)
            self.errors.append(error_msg)
            return False
        
        # 从高级配置获取基础URL，或使用默认值
        base_url = self.advanced.get('baseUrl', 'tyxsjpt.seu.edu.cn')
        miniapp_version = self.advanced.get('miniappversion', 'minappv3.0.1')
        user_agent = self.advanced.get('UA', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        # 准备请求头
        headers = {
            'Host': base_url,
            'xweb_xhr': '1',
            'miniappversion': miniapp_version,
            'User-Agent': user_agent,
            'tenant': 'NDEzMjAxMDI4Ng==',
            'token': f'Bearer {token}',
            'Content-Type': 'application/json',
            'Accept': '*/*',
            'Sec-Fetch-Site': 'cross-site',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Dest': 'empty',
            'Referer': 'https://servicewechat.com/wx5da07e9f6f45cabf/38/page-frame.html',
            'Accept-Language': 'zh-CN,zh;q=0.9'
        }
        
        # API端点
        url = f"https://{base_url}/api/miniapp/studentMini/getStudentInfo"
        logger.debug(f"准备向API发送请求: {url}")
        
        try:
            # 发送请求
            response = requests.get(url, headers=headers)
            logger.debug(f"API响应状态码: {response.status_code}")
            
            # 解析响应
            data = response.json()
            logger.debug(f"API响应内容: {json.dumps(data, ensure_ascii=False)}")
            
            # 检查响应状态
            if response.status_code != 200 or data.get('code') != 0:
                error_msg = f"Token验证失败: {data.get('msg', '未知错误')}"
                logger.error(error_msg)
                self.errors.append(error_msg)
                return False
            
            # 检查学生ID是否匹配
            if 'data' in data and 'id' in data['data'] and data['data']['id'] != self.basic.get('student_id'):
                error_msg = f"学生ID不匹配: 配置文件中为 {self.basic.get('student_id')}, API返回为 {data['data']['id']}"
                logger.error(error_msg)
                self.errors.append(error_msg)
                return False
            
            # 输出学生信息
            logger.info(f"Token验证成功，学生信息: {data['data']['studentName']} ({data['data']['studentNo']})")
            return True
            
        except requests.exceptions.SSLError:
            logger.error("连接错误。请使用个人手机流量连接，使用校园网会出现证书问题。")
            return False
            
        except requests.exceptions.RequestException as e:
            error_msg = f"请求API出错: {e}"
            logger.error(error_msg)
            self.errors.append(error_msg)
            return False
            
        except json.JSONDecodeError:
            error_msg = "API返回的数据不是有效的JSON格式"
            logger.error(error_msg)
            self.errors.append(error_msg)
            return False
            
        except Exception as e:
            error_msg = f"验证Token时发生未知错误: {e}"
            logger.error(error_msg)
            self.errors.append(error_msg)
            return False

    def validate(self):
        """运行所有验证检查"""
        logger.debug("开始验证配置文件...")
        
        # 首先加载配置
        if not self.load_config():
            logger.error("配置文件加载失败")
            return False
        
        # 执行所有验证方法
        validation_functions = [
            self.validate_basic_fields,
            self.validate_file_paths,
            self.validate_date_format,
            self.validate_time_formats,
            self.validate_token
        ]
        
        all_valid = True
        for validate_func in validation_functions:
            if not validate_func():
                all_valid = False
        
        if all_valid:
            logger.debug("所有验证通过！")
        else:
            logger.error("验证失败")
            
        return all_valid

    def get_errors(self):
        """返回所有验证错误"""
        return self.errors

def validate_config(config_path):
    """兼容旧版本的函数"""
    validator = ConfigValidator(config_path)
    if validator.validate():
        logger.info("配置文件校验通过！")
        return True
    else:
        logger.error("配置文件校验失败！")
        for error in validator.get_errors():
            logger.error(f"- {error}")
        return False

def validate_conf_main():
    """主函数，用于命令行运行"""
    config_path = 'config.yaml'
    result = validate_config(config_path)
    return result

# 当作为脚本执行时运行主函数
if __name__ == "__main__":
    validate_conf_main()