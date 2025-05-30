import sys
import yaml
import logging
import traceback
import requests
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QLineEdit,
    QPushButton, QVBoxLayout, QHBoxLayout, QFileDialog, QMessageBox,
    QGridLayout, QTextEdit, QSizePolicy, QDateEdit, QDateTimeEdit
)
from PyQt5.QtCore import QThread, pyqtSignal, QDate, QDateTime
from verify import LicenseClient
from main import main
from validate_conf import validate_conf_main

# 自定义日志处理器，将日志输出到QTextEdit控件
class QTextEditLogger(logging.Handler):
    def __init__(self, widget):
        super().__init__()
        self.widget = widget

    def emit(self, record):
        msg = self.format(record)
        self.widget.append(msg)

# 配置检查线程
class ConfigCheckThread(QThread):
    result_signal = pyqtSignal(bool)
    error_signal = pyqtSignal(str)

    def run(self):
        try:
            result = validate_conf_main()
            self.result_signal.emit(result)
        except Exception as e:
            self.error_signal.emit(str(e))

# 主线程用于运行主程序
class MainThread(QThread):
    log_signal = pyqtSignal(str)
    result_signal = pyqtSignal(bool)
    error_signal = pyqtSignal(str)

    def __init__(self, config_name):
        super().__init__()
        self.config_name = config_name

    def run(self):
        # 创建一个自定义日志处理器，用于将日志信息传递到GUI
        class SignalHandler(logging.Handler):
            def __init__(self, signal):
                super().__init__()
                self.signal = signal

            def emit(self, record):
                msg = self.format(record)
                self.signal.emit(msg)

        try:
            # 设置日志
            logger = logging.getLogger()
            log_handler = SignalHandler(self.log_signal)
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            log_handler.setFormatter(formatter)
            logger.handlers = []
            logger.addHandler(log_handler)
            
            # 调用主程序
            result = main(config_name=self.config_name)
            self.result_signal.emit(result)
        except requests.exceptions.SSLError:
            self.error_signal.emit("连接错误。请使用个人手机流量连接，使用校园网会出现证书问题。")
        except Exception as e:
            tb = traceback.format_exc()
            self.log_signal.emit(tb)
            self.log_signal.emit("主程序中出现未捕获的异常！")
            self.error_signal.emit(str(e))
            self.result_signal.emit(False)

# 主应用GUI
class APP_GUI_main(QMainWindow):
    def __init__(self):
        super().__init__()
        self.verify_key_client = LicenseClient()
        self.initUI()
        self.load_config()
        self.setup_logger()

    def setup_logger(self):
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        log_handler = QTextEditLogger(self.log_display)
        log_handler.setFormatter(formatter)
        self.logger.handlers = []
        self.logger.addHandler(log_handler)

    def initUI(self):
        self.setWindowTitle('东南大学体育锻炼')
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # 创建水平布局
        h_layout = QHBoxLayout()
        
        # 创建左侧表单
        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        grid_layout = QGridLayout()
        
        # 存储表单字段
        self.fields = {}
        
        # 创建表单字段
        self.create_field(grid_layout, 0, 'token', 'Token:')
        self.create_field(grid_layout, 2, 'student_id', '学号:')
        self.create_file_field(grid_layout, 3, 'start_image', '开始图片:')
        self.create_file_field(grid_layout, 4, 'finish_image', '结束图片:')
        
        # 日期字段
        date_label = QLabel('日期:')
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat('yyyy-MM-dd')
        self.date_edit.setDate(QDate.currentDate())
        grid_layout.addWidget(date_label, 5, 0)
        grid_layout.addWidget(self.date_edit, 5, 1)
        self.fields['date'] = self.date_edit
        
        # 开始时间字段
        start_time_label = QLabel('开始时间:')
        self.start_time_edit = QDateTimeEdit()
        self.start_time_edit.setDisplayFormat('HH:mm:ss')
        self.start_time_edit.setTime(QDateTime.currentDateTime().time())
        grid_layout.addWidget(start_time_label, 6, 0)
        grid_layout.addWidget(self.start_time_edit, 6, 1)
        self.fields['start_time'] = self.start_time_edit
        
        # 结束时间字段
        finish_time_label = QLabel('结束时间:')
        self.finish_time_edit = QDateTimeEdit()
        self.finish_time_edit.setDisplayFormat('HH:mm:ss')
        self.finish_time_edit.setTime(QDateTime.currentDateTime().time())
        grid_layout.addWidget(finish_time_label, 7, 0)
        grid_layout.addWidget(self.finish_time_edit, 7, 1)
        self.fields['finish_time'] = self.finish_time_edit
        
        # 距离字段
        self.create_field(grid_layout, 8, 'distance', '距离 (公里):')
        
        form_layout.addLayout(grid_layout)
        
        # 激活码字段
        key_layout = QHBoxLayout()
        key_label = QLabel('激活码:')
        self.key_input = QLineEdit()
        key_layout.addWidget(key_label)
        key_layout.addWidget(self.key_input)
        form_layout.addLayout(key_layout)
        
        # 按钮
        btn_layout = QHBoxLayout()
        save_btn = QPushButton('保存更改')
        save_btn.clicked.connect(self.save_config)
        btn_layout.addWidget(save_btn)
        
        check_config_btn = QPushButton('检查配置')
        check_config_btn.clicked.connect(self.check_config)
        btn_layout.addWidget(check_config_btn)
        
        run_btn = QPushButton('运行')
        run_btn.clicked.connect(self.run_main)
        btn_layout.addWidget(run_btn)
        
        form_layout.addLayout(btn_layout)
        
        h_layout.addWidget(form_widget)
        
        # 日志显示
        self.log_display = QTextEdit()
        self.log_display.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.log_display.setMinimumWidth(400)
        h_layout.addWidget(self.log_display)
        
        main_layout.addLayout(h_layout)

    def check_config(self, show_message=True):
        self.save_config()
        self.config_check_thread = ConfigCheckThread()
        self.config_check_thread.result_signal.connect(
            lambda result: self.handle_config_check_result(result, show_message)
        )
        self.config_check_thread.error_signal.connect(self.handle_config_check_error)
        self.config_check_thread.start()

    def handle_config_check_result(self, result, show_message):
        if result and show_message:
            QMessageBox.information(self, '配置检查', '配置检查通过！')
        elif not result:
            QMessageBox.warning(self, '配置检查', '配置检查未通过，请检查配置文件！')

    def handle_config_check_error(self, error_msg):
        QMessageBox.critical(self, '错误', f'配置检查时发生错误：{error_msg}')

    def load_config(self):
        try:
            with open('config.yaml', 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                basic = config['basic']
                
                # 为每个字段加载配置
                for field_name, field in self.fields.items():
                    if field_name in basic:
                        if field_name == 'date':
                            date = QDate.fromString(str(basic[field_name]), 'yyyy-MM-dd')
                            if date.isValid():
                                field.setDate(date)
                        elif field_name in ('start_time', 'finish_time'):
                            time = QDateTime.fromString(str(basic[field_name]), 'HH:mm:ss')
                            if time.isValid():
                                field.setTime(time.time())
                        else:
                            field.setText(str(basic[field_name]))
        except Exception as e:
            QMessageBox.critical(self, '错误', f'加载配置文件时出错：{str(e)}')

    def save_config(self):
        try:
            # 读取现有配置
            with open('config.yaml', 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # 更新配置
            for field_name, field in self.fields.items():
                if field_name == 'date':
                    config['basic'][field_name] = self.date_edit.date().toString('yyyy-MM-dd')
                elif field_name == 'start_time':
                    config['basic'][field_name] = self.start_time_edit.time().toString('HH:mm:ss')
                elif field_name == 'finish_time':
                    config['basic'][field_name] = self.finish_time_edit.time().toString('HH:mm:ss')
                else:
                    config['basic'][field_name] = field.text()
            
            # 保存配置
            with open('config.yaml', 'w', encoding='utf-8') as f:
                yaml.dump(config, f, allow_unicode=True)
            
            self.logger.info('配置保存成功！')
        except Exception as e:
            QMessageBox.critical(self, '错误', f'保存配置文件时出错：{str(e)}')

    def create_field(self, layout, row, field_name, label_text):
        label = QLabel(label_text)
        field = QLineEdit()
        layout.addWidget(label, row, 0)
        layout.addWidget(field, row, 1)
        self.fields[field_name] = field
        
    def create_file_field(self, layout, row, field_name, label_text):
        label = QLabel(label_text)
        field = QLineEdit()
        browse_button = QPushButton('浏览...')
        browse_button.clicked.connect(lambda: self.browse_file(field_name))
        
        layout.addWidget(label, row, 0)
        layout.addWidget(field, row, 1)
        layout.addWidget(browse_button, row, 2)
        self.fields[field_name] = field
        
    def browse_file(self, field_name):
        filename, _ = QFileDialog.getOpenFileName(self, '选择图片', '', '图片文件 (*.jpg *.png)')
        if filename:
            # 替换反斜杠
            filename = filename.replace('\\', '\\\\')
            self.fields[field_name].setText(filename)
            
    def run_main(self):
        # 清空日志显示
        self.log_display.clear()
        
        # 保存配置
        self.save_config()
        
        # 获取激活码
        key = self.key_input.text()
        if not key:
            QMessageBox.warning(self, '警告', '请输入激活码！')
            return
        
        # 验证激活码
        if self.verify_key_client.validate_key(key):
            # 创建并启动主线程
            self.main_thread = MainThread('config.yaml')
            self.main_thread.log_signal.connect(self.update_log)
            self.main_thread.result_signal.connect(self.handle_main_result)
            self.main_thread.error_signal.connect(self.handle_error)
            self.main_thread.start()
        else:
            # 显示错误消息
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setWindowTitle('错误')
            
            github_url = 'https://github.com/el739/SEU_exercise/blob/main/docs/%E8%8E%B7%E5%8F%96%E6%BF%80%E6%B4%BB%E7%A0%81.md'
            error_msg = f'激活码无效。请访问 {github_url} 获取更多信息。'
            msg_box.setText(error_msg)
            
            copy_button = msg_box.addButton('复制网址', QMessageBox.ActionRole)
            close_button = msg_box.addButton(QMessageBox.Close)
            
            msg_box.exec_()
            
            # 如果点击复制按钮，则复制URL到剪贴板
            if msg_box.clickedButton() == copy_button:
                clipboard = QApplication.clipboard()
                clipboard.setText(github_url)
            
    def handle_error(self, error_msg):
        QMessageBox.critical(self, '错误', f'发生错误：{error_msg}')
        
    def update_log(self, msg):
        self.log_display.append(msg)
        
    def handle_main_result(self, succeeded):
        if succeeded:
            self.verify_key_client.use_key(self.key_input.text())
            QMessageBox.information(self, '成功', '操作成功完成！')
        else:
            QMessageBox.warning(self, '警告', '操作失败！')

def main_gui():
    app = QApplication(sys.argv)
    window = APP_GUI_main()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main_gui()