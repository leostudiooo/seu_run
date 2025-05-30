import requests
import time
import json
import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes
import logging
import warnings

# 忽略警告
warnings.filterwarnings('ignore')

# 配置日志记录器
logger = logging.getLogger(__name__)

class LicenseClient:
    """
    激活码验证客户端
    用于验证和使用运行程序的激活码
    """
    def __init__(self, server_url="http://47.121.216.109:45134", secret_key=b'f4b1b9c1e7a5f2c816d7e183b44e6c92'):
        """
        初始化许可客户端
        
        Args:
            server_url: 验证服务器URL
            secret_key: 加密通信的密钥
        """
        self.server_url = server_url.rstrip('/')
        self.secret_key = secret_key

    def encrypt_payload(self, data):
        """
        加密请求数据，添加时间戳和随机数以防止重放攻击
        
        Args:
            data: 要加密的数据字典
            
        Returns:
            str: Base64编码的加密数据
        """
        # 添加时间戳
        data['timestamp'] = int(time.time())
        
        # 添加随机数
        data['nonce'] = base64.b64encode(get_random_bytes(16)).decode()
        
        # 序列化数据并加密
        json_data = json.dumps(data).encode()
        padded_data = pad(json_data, AES.block_size)
        iv = get_random_bytes(AES.block_size)
        cipher = AES.new(self.secret_key, AES.MODE_CBC, iv)
        encrypted_data = cipher.encrypt(padded_data)
        
        # 将IV和加密数据组合并Base64编码
        combined_data = iv + encrypted_data
        return base64.b64encode(combined_data).decode()

    def decrypt_response(self, encrypted_response):
        """
        解密服务器响应
        
        Args:
            encrypted_response: 加密的响应数据
            
        Returns:
            dict: 解密后的响应数据，或None(如果解密失败)
        """
        try:
            # 解码Base64
            data = base64.b64decode(encrypted_response)
            
            # 分离IV和加密数据
            iv = data[:AES.block_size]
            encrypted_data = data[AES.block_size:]
            
            # 解密
            cipher = AES.new(self.secret_key, AES.MODE_CBC, iv)
            decrypted_data = unpad(cipher.decrypt(encrypted_data), AES.block_size)
            
            # 解析JSON
            response = json.loads(decrypted_data)
            
            # 验证时间戳，确保响应不是过时的(300秒内有效)
            if abs(int(time.time()) - response['timestamp']) > 300:
                logger.warning('Response timestamp expired: %d', response['timestamp'])
                raise ValueError('Response timestamp expired')
                
            return response
            
        except Exception as e:
            logger.error('Failed to decrypt response: %s', e)
            return None

    def validate_key(self, key):
        """
        验证激活码是否有效
        
        Args:
            key: 激活码
            
        Returns:
            bool: 如果激活码有效则返回True，否则返回False
        """
        try:
            # 准备验证请求
            encrypted_payload = self.encrypt_payload({
                'action': 'validate',
                'key': key
            })
            
            # 发送请求到服务器
            response = requests.post(
                f"{self.server_url}/api/secure",
                json={'payload': encrypted_payload},
                verify=False  # 不验证SSL证书
            )
            
            # 检查响应状态码
            if response.status_code == 200:
                # 解密响应
                decrypted = self.decrypt_response(response.json().get('payload'))
                return decrypted.get('valid', False) if decrypted else False
            
            return False
            
        except Exception as e:
            logger.error('Error during key validation: %s', e)
            return False

    def use_key(self, key):
        """
        标记激活码为已使用
        
        Args:
            key: 激活码
            
        Returns:
            bool: 如果操作成功则返回True，否则返回False
        """
        try:
            # 准备使用请求
            encrypted_payload = self.encrypt_payload({
                'action': 'use',
                'key': key
            })
            
            # 发送请求到服务器
            response = requests.post(
                f"{self.server_url}/api/secure",
                json={'payload': encrypted_payload},
                verify=False  # 不验证SSL证书
            )
            
            # 检查响应状态码
            if response.status_code == 200:
                # 解密响应
                decrypted = self.decrypt_response(response.json().get('payload'))
                return decrypted.get('success', False) if decrypted else False
            else:
                logger.warning('Unexpected response status code: %d', response.status_code)
            
            return False
            
        except Exception as e:
            logger.error('Error during key usage: %s', e)
            return False