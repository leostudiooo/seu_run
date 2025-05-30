import json
import yaml
import logging
import requests
from datetime import datetime
from upload_image import ImageUploader
from save_start_record import SEUSportsClient
from save_record import DataUploader
from verify import LicenseClient

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[],
    encoding='utf-8'
)
logger = logging.getLogger(__name__)

def calculate_seconds(start_time, finish_time):
    """计算两个时间字符串之间的秒数差"""
    start = datetime.strptime(start_time, '%H:%M:%S')
    finish = datetime.strptime(finish_time, '%H:%M:%S')
    return int((finish - start).total_seconds())

def calculate_speed(seconds, distance):
    """计算配速（分钟/公里）"""
    mins_per_km = (seconds / 60) / float(distance)
    minutes = int(mins_per_km)
    seconds = int((mins_per_km - minutes) * 60)
    return f"{minutes}'{seconds}''"

def format_display_time(seconds):
    """将秒数格式化为显示时间（HH:MM:SS）"""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"

def main(config_name='config.yaml'):
    try:
        with open(config_name, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            basic = config['basic']
            advanced = config['advanced']
            
            # 计算秒数（如果不存在）
            if 'seconds' not in basic:
                basic['seconds'] = str(calculate_seconds(basic['start_time'], basic['finish_time']))
            
            # 计算配速（如果不存在）
            if 'speed' not in basic:
                basic['speed'] = calculate_speed(int(basic['seconds']), float(basic['distance']))
            
            # 计算显示时间（如果不存在）
            if 'display_time' not in basic:
                basic['display_time'] = format_display_time(int(basic['seconds']))
            
            # 确保tenant存在
            if 'tenant' not in advanced:
                advanced['tenant'] = 'NDEzMjAxMDI4Ng=='
                
    except Exception as e:
        logging.error(f'Config file not found or bad config file, {e}')
        
    # 上传开始图片
    start_image = basic['start_image']
    finish_image = basic['finish_image']
    
    # 构建请求头
    headers = {
        'Host': advanced['baseUrl'],
        'token': f"Bearer {basic['token']}",
        'miniappversion': advanced['miniappversion'],
        'User-Agent': advanced['UA'],
        'tenant': advanced['tenant'],
        'Referer': 'https://servicewechat.com/wx5da07e9f6f45cabf/38/page-frame.html'
    }
    
    start_img_url = ''
    
    # 上传开始图片
    uploader = ImageUploader(f"https://{advanced['baseUrl']}/api/miniapp/exercise/uploadRecordImage", headers, start_image)
    try:
        response = uploader.upload()
        if response.status_code == 200:
            start_img_url = json.loads(response.text)['data']
            logger.info('Start image uploaded successfully')
        else:
            logger.error(f'Failed to upload start image. Status Code: {response.status_code}')
            logger.error(f'Response: {response.text}')
            exit()
    except requests.exceptions.SSLError:
        exit()
    except FileNotFoundError:
        exit()
    except Exception as e:
        logger.error(f'Exception occurred while uploading start image, {e}')
        exit()
    
    # 上传结束图片
    finish_img_url = ''
    uploader = ImageUploader(f"https://{advanced['baseUrl']}/api/miniapp/exercise/uploadRecordImage2", headers, finish_image)
    try:
        response = uploader.upload()
        if response.status_code == 200:
            finish_img_url = json.loads(response.text)['data']
            logger.info('Finish image uploaded successfully')
        else:
            logger.error(f'Failed to upload finish image. Status Code: {response.status_code}')
            logger.error(f'Response: {response.text}')
            exit()
    except FileNotFoundError:
        exit()
    except Exception as e:
        logger.error(f'Exception occurred while uploading finish image, {e}')
        exit()
    
    # 保存开始记录
    token = basic['token']
    tenant = advanced['tenant']
    ua = advanced['UA']
    student_id = basic['student_id']
    
    client = SEUSportsClient(token, tenant, ua, student_id)
    
    try:
        start_resp = client.save_start_record(
            route_name=advanced['route_name'],
            rule_id=advanced['rule_id'],
            plan_id=advanced['plan_id'],
            record_date=basic['date'],
            start_time=basic['start_time'],
            start_image=start_img_url,
            route_rule=advanced['route_rule']
        )
        
        if start_resp.status_code == 200:
            resp_data = json.loads(start_resp.text)
            record_id = resp_data['data']
            logger.info('Start record uploaded successfully')
        else:
            logger.error(f'Failed to save start record. Status Code: {start_resp.status_code}')
            logger.error(f'Response: {start_resp.text}')
            raise Exception(f'API request failed with status code {start_resp.status_code}')
            
    except requests.exceptions.SSLError:
        logger.error('连接错误。请使用个人手机流量连接，使用校园网会出现证书问题。\n如果确认已使用流量，请确认凭证确实正确。点击"验证凭证"来确认凭证是否正确。')
    except requests.exceptions.RequestException as e:
        logger.error(f'Network error occurred while saving start record: {e}')
    except json.JSONDecodeError as e:
        logger.error(f'Failed to parse response JSON: {e}')
    except KeyError as e:
        logger.error(f'Missing expected data in response: {e}')
    except Exception as e:
        logger.error(f'Unexpected error occurred while saving start record: {e}')
    
    # 保存最终记录
    try:
        with open(advanced['track_filename'], 'r', encoding='utf-8') as f:
            track_data = f.read()
        
        # 构建请求参数
        req_params = {
            'url': f"https://{advanced['baseUrl']}/api/exercise/exerciseRecord/saveRecord",
            'headers': {
                'Host': advanced['baseUrl'],
                'token': f"Bearer {basic['token']}",
                'miniappversion': advanced['miniappversion'],
                'User-Agent': advanced['UA'],
                'tenant': advanced['tenant']
            },
            'data': {
                'routeName': advanced['route_name'],
                'ruleId': advanced['rule_id'],
                'planId': advanced['plan_id'],
                'recordTime': basic['date'],
                'startTime': basic['start_time'],
                'startImage': start_img_url,
                'endTime': basic['finish_time'],
                'exerciseTimes': basic['seconds'],
                'routeKilometre': basic['distance'],
                'endImage': finish_img_url,
                'routeRule': advanced['route_rule'],
                'calorie': basic['calorie'],
                'speed': basic['speed'],
                'dispTimeText': basic['display_time'],
                'studentId': basic['student_id'],
                'id': record_id
            }
        }
        
        uploader = DataUploader(req_params, track_data)
        response = uploader.run()
        
        if response.status_code == 200:
            resp_data = json.loads(response.text)
            record_data = resp_data['data']
            logger.info('Final record saved successfully')
            logger.info('Record added successfully')
            return True
        else:
            logger.error(f'Failed to save final record. Status Code: {response.status_code}')
            logger.error(f'Response: {response.text}')
            raise Exception(f'API request failed with status code {response.status_code}')
            
    except FileNotFoundError as e:
        logger.error(f'Track file not found: {e}')
    except json.JSONDecodeError as e:
        logger.error(f'Failed to parse response JSON: {e}')
    except Exception as e:
        logger.error(f'Error occurred while saving final record: {e}')

if __name__ == "__main__":
    verify_key_client = LicenseClient()
    key = 1  # 这里似乎有一个硬编码的密钥
    
    if True or verify_key_client.validate_key(key):  # 总是为真，验证似乎被禁用了
        succeeded = main(config_name='config.yaml')
        if succeeded:
            verify_key_client.use_key(key)
    else:
        logging.error('Wrong key. Check your spelling.')
    
    input('Press enter to continue...')