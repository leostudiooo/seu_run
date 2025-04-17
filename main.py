import aiohttp
import asyncio
import json
import time
import base64
from datetime import datetime, timedelta
import random
import ssl
from typing import Optional
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from ttkthemes import ThemedTk  # 添加主题支持

# 全局配置
BASE_URL = "https://tyxsjpt.seu.edu.cn"
RULE_ID = "4021863683095029882"
PLAN_ID = "4036401245454917492"

# GPS轨迹数据
GPS_TRACK_DATA = [
    [118.82066, 31.88869],
    [118.82066, 31.88868],
    [118.82066, 31.88867],
    [118.82066, 31.88866],
    [118.82066, 31.88865],
    [118.82066, 31.88864],
    [118.82066, 31.88863],
    [118.82066, 31.88862],
    [118.82066, 31.88861],
    [118.82066, 31.8886],
    [118.82066, 31.88859],
    [118.82066, 31.88858],
    [118.82066, 31.88857],
    [118.82066, 31.88856],
    [118.82066, 31.88855],
    [118.82066, 31.88854],
    [118.82066, 31.88853],
    [118.82066, 31.88852],
    [118.82066, 31.88851],
    [118.82066, 31.8885]
]

# 创建SSL上下文
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# 通用请求头
def get_headers(token: str, content_type="application/json;charset=utf-8"):
    return {
        "User-Agent": "Mozilla/5.0 (Linux; Android 7.1.2; V2284A Build/N2G47H; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/116.0.0.0 Mobile Safari/537.36 XWEB/1160253 MMWEBSDK/20240301 MMWEBID/4107 MicroMessenger/8.0.48.2580(0x28003036) WeChat/arm64 Weixin NetType/WIFI Language/zh_CN ABI/arm64 MiniProgramEnv/android",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept": "*/*",
        "token": token,
        "miniappversion": "minappv3.0.1",
        "tenant": "NDEzMjAxMDI4Ng==",
        "content-type": content_type,
        "Referer": "https://servicewechat.com/wx5da07e9f6f45cabf/38/page-frame.html",
        "charset": "utf-8"
    }

async def make_request(method: str, url: str, token: str, headers: dict, data: Optional[dict] = None, files: Optional[dict] = None, max_retries: int = 3) -> Optional[dict]:
    headers = get_headers(token, headers.get("content-type", "application/json;charset=utf-8"))
    async with aiohttp.ClientSession() as session:
        for attempt in range(max_retries):
            try:
                if method == "POST":
                    if files:
                        form_data = aiohttp.FormData()
                        for key, value in files.items():
                            form_data.add_field(key, value[1], filename=value[0], content_type=value[2])
                        async with session.post(url, headers=headers, data=form_data, ssl=ssl_context) as response:
                            if response.status == 200:
                                return await response.json()
                    else:
                        async with session.post(url, headers=headers, json=data, ssl=ssl_context) as response:
                            if response.status == 200:
                                return await response.json()
                else:
                    async with session.get(url, headers=headers, ssl=ssl_context) as response:
                        if response.status == 200:
                            return await response.json()
                
                print(f"请求失败，状态码: {response.status}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # 指数退避
            except Exception as e:
                print(f"请求出错 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
    return None

# 1. 发送开始运动请求
async def start_exercise(token: str, student_id: str, record_time: str, start_time: str) -> Optional[str]:
    url = f"{BASE_URL}/api/exercise/exerciseRecord/saveStartRecord"

    data = {
        "routeName": "橘园田径场",
        "ruleId": "402186368309502988",
        "planId": "403640124545491749",
        "recordTime": record_time,
        "startTime": start_time,
        "startImage": "",
        "endTime": "",
        "exerciseTimes": "",
        "routeKilometre": "",
        "endImage": "",
        "strLatitudeLongitude": [],
        "routeRule": "九龙湖校区",
        "maxTime": 12,
        "minTime": 4,
        "orouteKilometre": 1.2,
        "ruleEndTime": "22:00",
        "ruleStartTime": "6:00",
        "calorie": 0,
        "speed": "0'00''",
        "dispTimeText": 0,
        "studentId": student_id
    }

    result = await make_request("POST", url, token, get_headers(token), data)
    if result:
        print("开始运动成功:", result)
        return result.get("data")
    else:
        print("开始运动失败")
        return None

# 2. 上传开始图片
async def upload_start_image(token: str, image_path: str) -> Optional[str]:
    url = f"{BASE_URL}/api/miniapp/exercise/uploadRecordImage"
    
    try:
        # 创建FormData
        form_data = aiohttp.FormData()
        form_data.add_field('file',
                          open(image_path, 'rb'),
                          filename='exercise_start.jpg',
                          content_type='image/jpeg')
        
        headers = get_headers(token, None)
        headers.pop('content-type', None)
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=form_data, ssl=ssl_context) as response:
                if response.status == 200:
                    result = await response.json()
                    print("上传开始图片成功:", result)
                    return result.get("data")
                else:
                    print(f"上传开始图片失败，状态码: {response.status}")
                    return None
    except Exception as e:
        print(f"上传开始图片时出错: {str(e)}")
        return None

# 3. 上传结束图片
async def upload_end_image(token: str, image_path: str) -> Optional[str]:
    url = f"{BASE_URL}/api/miniapp/exercise/uploadRecordImage2"
    
    try:
        # 创建FormData
        form_data = aiohttp.FormData()
        form_data.add_field('file',
                          open(image_path, 'rb'),
                          filename='exercise_end.jpg',
                          content_type='image/jpeg')
        
        headers = get_headers(token, None)
        headers.pop('content-type', None)
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=form_data, ssl=ssl_context) as response:
                if response.status == 200:
                    result = await response.json()
                    print("上传结束图片成功:", result)
                    return result.get("data")
                else:
                    print(f"上传结束图片失败，状态码: {response.status}")
                    return None
    except Exception as e:
        print(f"上传结束图片时出错: {str(e)}")
        return None

# 4. 完成运动并提交记录
async def finish_exercise(token: str, student_id: str, record_id: str, start_image_url: str, end_image_url: str, 
                         start_time: str, end_time: str, distance: float) -> bool:
    url = f"{BASE_URL}/api/exercise/exerciseRecord/saveRecord"

    # 计算运动时间（分钟）
    start = datetime.strptime(start_time, "%H:%M:%S")
    end = datetime.strptime(end_time, "%H:%M:%S")
    duration = (end - start).total_seconds() / 60  # 转换为分钟
    disp_time_text = int(duration * 60)  # 转换为秒

    # 计算卡路里（假设体重为60kg）
    calorie = int(60 * distance * 1.036)  # 卡路里

    # 计算配速（分钟/公里）
    pace_minutes = duration / distance  # 每公里所需分钟数
    pace_seconds = int((pace_minutes - int(pace_minutes)) * 60)  # 转换为秒
    pace_minutes = int(pace_minutes)
    speed = f"{pace_minutes}'{pace_seconds:02d}''"  # 格式化为 5'30'' 的形式

    data = {
        "routeName": "橘园田径场",
        "ruleId": "402186368309502988",
        "planId": "403640124545491749",
        "recordTime": datetime.now().strftime("%Y-%m-%d"),
        "startTime": start_time,
        "startImage": start_image_url,
        "endTime": end_time,
        "exerciseTimes": "449",
        "routeKilometre": str(distance),
        "endImage": end_image_url,
        "routeRule": "九龙湖校区",
        "calorie": calorie,
        "speed": speed,
        "dispTimeText": disp_time_text,
        "studentId": student_id,
        "id": record_id,
        "strLatitudeLongitude": json.dumps(GPS_TRACK_DATA),  # 使用内置的GPS数据
        "maxTime": 12,
        "minTime": 4,
        "orouteKilometre": 1.2,
        "ruleEndTime": "22:00",
        "ruleStartTime": "06:00",
        "nowStatus": 2
    }

    result = await make_request("POST", url, token, get_headers(token), data)
    if result:
        print("完成运动成功:", result)
        return True
    else:
        print("完成运动失败")
        return False

class ExerciseApp:
    def __init__(self, root):
        self.root = root
        self.root.title("东南大学自动跑操程序")
        self.root.geometry("800x1000")
        
        # 设置主题样式
        style = ttk.Style()
        style.configure("Title.TLabel", font=("微软雅黑", 16, "bold"))
        style.configure("Section.TLabel", font=("微软雅黑", 12))
        style.configure("Custom.TButton", font=("微软雅黑", 10), padding=5)
        style.configure("Submit.TButton", font=("微软雅黑", 12, "bold"), padding=10)
        
        # 创建主框架
        main_frame = ttk.Frame(root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 标题
        title_label = ttk.Label(main_frame, text="东南大学自动跑操程序", style="Title.TLabel")
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # 创建信息输入区域框架
        info_frame = ttk.LabelFrame(main_frame, text="基本信息", padding="10")
        info_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 20))
        
        # Token输入
        ttk.Label(info_frame, text="Token:", style="Section.TLabel").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.token_entry = ttk.Entry(info_frame, width=50)
        self.token_entry.grid(row=0, column=1, columnspan=2, sticky=tk.W, pady=5, padx=5)
        
        # 学生ID输入
        ttk.Label(info_frame, text="学生ID:", style="Section.TLabel").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.student_id_entry = ttk.Entry(info_frame, width=50)
        self.student_id_entry.grid(row=1, column=1, columnspan=2, sticky=tk.W, pady=5, padx=5)
        
        # 创建图片选择区域框架
        image_frame = ttk.LabelFrame(main_frame, text="图片选择", padding="10")
        image_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 20))
        
        # 开始图片选择
        ttk.Label(image_frame, text="开始图片:", style="Section.TLabel").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.start_image_path = tk.StringVar()
        ttk.Entry(image_frame, textvariable=self.start_image_path, width=40).grid(row=0, column=1, sticky=tk.W, pady=5, padx=5)
        ttk.Button(image_frame, text="浏览", command=lambda: self.select_file(self.start_image_path), style="Custom.TButton").grid(row=0, column=2, sticky=tk.W, pady=5, padx=5)
        
        # 结束图片选择
        ttk.Label(image_frame, text="结束图片:", style="Section.TLabel").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.end_image_path = tk.StringVar()
        ttk.Entry(image_frame, textvariable=self.end_image_path, width=40).grid(row=1, column=1, sticky=tk.W, pady=5, padx=5)
        ttk.Button(image_frame, text="浏览", command=lambda: self.select_file(self.end_image_path), style="Custom.TButton").grid(row=1, column=2, sticky=tk.W, pady=5, padx=5)
        
        # 创建时间设置区域框架
        time_frame = ttk.LabelFrame(main_frame, text="时间设置", padding="10")
        time_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 20))
        
        # 日期选择
        ttk.Label(time_frame, text="运动日期:", style="Section.TLabel").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.date_entry = ttk.Entry(time_frame, width=20)
        self.date_entry.grid(row=0, column=1, sticky=tk.W, pady=5, padx=5)
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        
        # 开始时间
        ttk.Label(time_frame, text="开始时间:", style="Section.TLabel").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.start_time_entry = ttk.Entry(time_frame, width=20)
        self.start_time_entry.grid(row=1, column=1, sticky=tk.W, pady=5, padx=5)
        self.start_time_entry.insert(0, "18:30:00")
        
        # 结束时间
        ttk.Label(time_frame, text="结束时间:", style="Section.TLabel").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.end_time_entry = ttk.Entry(time_frame, width=20)
        self.end_time_entry.grid(row=2, column=1, sticky=tk.W, pady=5, padx=5)
        self.end_time_entry.insert(0, "18:40:00")
        
        # 距离输入
        ttk.Label(time_frame, text="运动距离(km):", style="Section.TLabel").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.distance_entry = ttk.Entry(time_frame, width=20)
        self.distance_entry.grid(row=3, column=1, sticky=tk.W, pady=5, padx=5)
        self.distance_entry.insert(0, "1.21")
        
        # 创建日志区域框架
        log_frame = ttk.LabelFrame(main_frame, text="运行日志", padding="10")
        log_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 20))
        
        # 日志文本框
        self.log_text = tk.Text(log_frame, width=70, height=15, font=("Consolas", 10))
        self.log_text.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        scrollbar.grid(row=0, column=3, sticky=(tk.N, tk.S))
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        # 提交按钮
        submit_button = ttk.Button(main_frame, text="开始自动跑操", command=self.start_exercise_process, style="Submit.TButton")
        submit_button.grid(row=5, column=0, columnspan=3, pady=20)
        
        # 配置网格权重
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # 添加状态栏
        self.status_var = tk.StringVar()
        self.status_var.set("就绪")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E))

    def select_file(self, path_var):
        filename = filedialog.askopenfilename(
            title="选择图片文件",
            filetypes=[("图片文件", "*.jpg *.jpeg *.png")]
        )
        if filename:
            path_var.set(filename)
    
    def log(self, message):
        self.log_text.insert(tk.END, f"{datetime.now().strftime('%H:%M:%S')} - {message}\n")
        self.log_text.see(tk.END)
    
    async def run_exercise(self):
        try:
            # 获取输入值
            token = self.token_entry.get()
            student_id = self.student_id_entry.get()
            start_image = self.start_image_path.get()
            end_image = self.end_image_path.get()
            date = self.date_entry.get()
            start_time = self.start_time_entry.get()
            end_time = self.end_time_entry.get()
            distance = float(self.distance_entry.get())
            
            self.log("开始自动跑操流程...")
            self.log(f"日期: {date}")
            self.log(f"开始时间: {start_time}")
            self.log(f"结束时间: {end_time}")
            self.log(f"距离: {distance}km")
            
            # 1. 开始运动
            record_id = await start_exercise(token, student_id, date, start_time)
            if not record_id:
                self.log("无法获取运动记录ID，退出")
                return
            
            # 2. 上传开始图片
            start_image_url = await upload_start_image(token, start_image)
            if not start_image_url:
                self.log("上传开始图片失败，退出")
                return
            
            # 3. 上传结束图片
            end_image_url = await upload_end_image(token, end_image)
            if not end_image_url:
                self.log("上传结束图片失败，退出")
                return
            
            # 4. 完成运动
            if await finish_exercise(token, student_id, record_id, start_image_url, end_image_url, 
                                  start_time, end_time, distance):
                self.log("自动跑操完成！")
            else:
                self.log("自动跑操失败")
                
        except Exception as e:
            self.log(f"发生错误: {str(e)}")
    
    def start_exercise_process(self):
        # 在新线程中运行异步任务
        thread = threading.Thread(target=lambda: asyncio.run(self.run_exercise()))
        thread.daemon = True
        thread.start()

if __name__ == "__main__":
    root = ThemedTk(theme="arc")  # 使用arc主题
    app = ExerciseApp(root)
    root.mainloop()