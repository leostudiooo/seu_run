import requests
import os
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImageUploader:
    """图片上传类"""
    
    def __init__(self, url, headers, image_path):
        """
        初始化图片上传器
        
        Args:
            url: 上传目标URL
            headers: HTTP请求头
            image_path: 图片文件路径
        """
        self.url = url
        self.headers = headers
        self.image_path = image_path
        self.response = None
        self.error = None
    
    def validate_file(self):
        """验证图片文件是否存在"""
        if not os.path.exists(self.image_path):
            logger.error(f"File {self.image_path} does not exist")
            raise FileNotFoundError(f"File {self.image_path} does not exist")
        
        if not os.path.isfile(self.image_path):
            logger.error(f"{self.image_path} is not a file")
            raise ValueError(f"{self.image_path} is not a file")
    
    def prepare_payload(self):
        """准备上传的文件负载"""
        logger.info(f"Preparing payload for file: {self.image_path}")
        
        # 获取文件名
        filename = os.path.basename(self.image_path)
        
        # 打开文件并准备上传
        file_obj = open(self.image_path, 'rb')
        
        # 返回文件字典
        return {
            'file': (filename, file_obj, 'image/jpeg')
        }
    
    def upload(self):
        """执行文件上传"""
        try:
            # 验证文件是否存在
            self.validate_file()
            
            # 打开文件并上传
            with open(self.image_path, 'rb') as image_file:
                # 准备文件数据
                files = {
                    'file': (os.path.basename(self.image_path), image_file, 'image/jpeg')
                }
                
                # 记录日志
                logger.info(f"Sending POST request to {self.url}")
                
                # 发送请求
                self.response = requests.post(
                    url=self.url,
                    headers=self.headers,
                    files=files,
                    verify=False  # 不验证SSL证书
                )
                
                # 返回响应
                return self.response
                
        except FileNotFoundError:
            # 文件不存在异常处理
            logger.error(f"选择的图片{self.image_path}不存在，请检查路径。")
            # 不重新抛出异常，只记录
            
        except requests.exceptions.SSLError:
            # SSL证书错误处理
            logger.error("请使用个人手机流量连接，使用校园网会出现证书问题。")
            # 不重新抛出异常，只记录
            
        except Exception as e:
            # 其他异常处理
            logger.error(f"An error occurred during the upload process, {e}")
            # 不重新抛出异常，只记录