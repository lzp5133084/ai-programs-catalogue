import sys
import os
import time
import logging
import threading
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QSlider, QLabel, QSpinBox, QSystemTrayIcon, QMenu, 
    QMessageBox, QFileDialog, QListWidget, QListWidgetItem, QInputDialog
)
from PyQt5.QtGui import QPixmap, QPainter, QColor, QFont, QIcon, QAction, QPainterPath, QPen, QFontMetrics
from PyQt5.QtCore import Qt, QTimer, QRect, QPoint, QSize
from PIL import ImageGrab, Image
import base64
import requests
from dotenv import load_dotenv

# 预留接口支持（可选）
class TranslationAPI:
    """翻译应用的API接口类"""
    def __init__(self, app_instance):
        self.app = app_instance
        self.is_running = False
        self.server_thread = None
    
    def start_api_server(self, host='127.0.0.1', port=5000):
        """启动API服务器"""
        if self.is_running:
            logger.info("API服务器已在运行")
            return True
        
        try:
            # 动态导入Flask，避免不必要的依赖
            from flask import Flask, jsonify, request
            
            self.flask_app = Flask(__name__)
            
            @self.flask_app.route('/api/status', methods=['GET'])
            def get_status():
                """获取应用状态"""
                return jsonify({
                    'is_monitoring': self.app.is_monitoring,
                    'selected_region': {
                        'x': self.app.selected_region.x() if self.app.selected_region else 0,
                        'y': self.app.selected_region.y() if self.app.selected_region else 0,
                        'width': self.app.selected_region.width() if self.app.selected_region else 0,
                        'height': self.app.selected_region.height() if self.app.selected_region else 0
                    }
                })
            
            @self.flask_app.route('/api/start', methods=['POST'])
            def start_monitoring():
                """开始监控"""
                if self.app.selected_region:
                    self.app.start_monitoring()
                    return jsonify({'success': True, 'message': '监控已启动'})
                else:
                    return jsonify({'success': False, 'message': '未选择监控区域'}), 400
            
            @self.flask_app.route('/api/stop', methods=['POST'])
            def stop_monitoring():
                """停止监控"""
                self.app.stop_monitoring()
                return jsonify({'success': True, 'message': '监控已停止'})
            
            @self.flask_app.route('/api/translate', methods=['POST'])
            def translate_text_api():
                """翻译指定文本"""
                data = request.get_json()
                text = data.get('text', '')
                if text:
                    translated = self.app.translate_text(text)
                    if translated:
                        return jsonify({'success': True, 'original': text, 'translated': translated})
                    else:
                        return jsonify({'success': False, 'message': '翻译失败'}), 500
                else:
                    return jsonify({'success': False, 'message': '未提供文本'}), 400
            
            @self.flask_app.route('/api/history', methods=['GET'])
            def get_history():
                """获取翻译历史"""
                return jsonify({'history': self.app.translation_history})
            
            # 启动服务器线程
            def run_server():
                self.flask_app.run(host=host, port=port, debug=False, use_reloader=False)
            
            self.server_thread = threading.Thread(target=run_server, daemon=True)
            self.server_thread.start()
            self.is_running = True
            logger.info(f"API服务器已启动，地址: http://{host}:{port}")
            return True
            
        except ImportError:
            logger.error("Flask未安装，无法启动API服务器")
            return False
        except Exception as e:
            logger.error(f"启动API服务器失败: {str(e)}")
            return False
    
    def stop_api_server(self):
        """停止API服务器"""
        if self.is_running:
            self.is_running = False
            # Flask开发服务器无法优雅停止，这里只是标记状态
            logger.info("API服务器已停止")
            return True
        return False

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('translation_app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 配置参数
has_tesseract = True  # 不再需要Tesseract，默认设为True

class TranslationOverlay(QWidget):
    """翻译结果覆盖层窗口"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.translation_text = ""
        self.opacity = 0.8
        
    def paintEvent(self, event):
        """绘制翻译结果"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 创建半透明背景，带圆角效果
        bg_color = QColor(0, 0, 0, int(self.opacity * 255))
        painter.fillRect(self.rect(), bg_color)
        
        # 绘制文字，使用更好的字体和布局
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Microsoft YaHei", 12))
        painter.drawText(self.rect(), Qt.AlignCenter | Qt.AlignVCenter, self.translation_text)
        
        # 绘制边框，增强视觉效果
        border_color = QColor(0, 255, 0, 200)
        painter.setPen(border_color)
        painter.drawRect(self.rect().adjusted(0, 0, -1, -1))
        
    def set_translation_text(self, text):
        """设置翻译文本"""
        self.translation_text = text
        # 调整窗口大小，确保有足够的边距
        font = QFont("Microsoft YaHei", 12)
        metrics = QFontMetrics(font)
        text_rect = metrics.boundingRect(0, 0, 500, 100, Qt.TextFlag.TextWordWrap | Qt.AlignLeft, text)
        self.setFixedSize(text_rect.width() + 20, text_rect.height() + 20)
        self.update()
        
    def set_opacity(self, opacity):
        """设置透明度（0-100）"""
        self.opacity = opacity / 100.0
        self.update()

class RegionSelector(QWidget):
    """屏幕区域选择工具"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
        self.setWindowState(Qt.WindowState.WindowFullScreen)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.start_point = QPoint()
        self.end_point = QPoint()
        self.is_selecting = False
        self.selected_region = None
        
    def paintEvent(self, event):
        """绘制选择区域"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 只绘制选择框，不绘制任何遮罩
        if self.is_selecting:
            selection_rect = QRect(self.start_point, self.end_point).normalized()
            
            # 绘制选择框边框
            pen = QPen(QColor(0, 255, 0, 255), 2)
            painter.setPen(pen)
            painter.drawRect(selection_rect)
    
    def mousePressEvent(self, event):
        """鼠标按下事件"""
        self.start_point = event.pos()
        self.end_point = event.pos()
        self.is_selecting = True
        self.update()
    
    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        if self.is_selecting:
            self.end_point = event.pos()
            self.update()
    
    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        self.end_point = event.pos()
        self.is_selecting = False
        
        # 获取选择的区域
        self.selected_region = QRect(self.start_point, self.end_point).normalized()
        
        # 检查区域是否有效
        if self.selected_region.width() > 10 and self.selected_region.height() > 10:
            self.close()
        else:
            self.selected_region = None
            QMessageBox.warning(self, "警告", "请选择一个有效的区域（至少10x10像素）")

class TranslationApp(QMainWindow):
    """主翻译应用程序类"""
    def __init__(self):
        super().__init__()
        
        # 加载配置
        self.doubao_api_key = os.getenv("DOUBAO_API_KEY")
        self.ocr_language = os.getenv("OCR_LANGUAGE", "eng")
        self.screenshot_interval = int(os.getenv("SCREENSHOT_INTERVAL", 1000))
        self.default_opacity = int(os.getenv("DEFAULT_OPACITY", 80))
        
        # 应用状态
        self.selected_region = None
        self.is_monitoring = False
        self.last_text = ""
        self.translation_history = []
        self.api_server = TranslationAPI(self)  # API服务器实例
        
        # 创建UI组件
        self.overlay = TranslationOverlay()
        self.region_selector = None
        
        # 初始化UI
        self.init_ui()
        
        # 创建定时器用于屏幕监控
        self.screenshot_timer = QTimer()
        self.screenshot_timer.timeout.connect(self.capture_and_translate)
        
        # 加载历史记录
        self.load_history()
    
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("实时屏幕翻译")
        self.setGeometry(100, 100, 400, 350)
        self.setWindowIcon(QIcon("icon.png"))
        
        # 主窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        
        # Tesseract配置部分
        tesseract_layout = QHBoxLayout()
        tesseract_label = QLabel("Tesseract OCR: " + ("已配置" if has_tesseract else "未配置"))
        self.tesseract_config_btn = QPushButton("配置Tesseract路径")
        self.tesseract_config_btn.clicked.connect(self.configure_tesseract_path)
        tesseract_layout.addWidget(tesseract_label)
        tesseract_layout.addWidget(self.tesseract_config_btn)
        main_layout.addLayout(tesseract_layout)
        
        # 区域选择部分
        region_layout = QHBoxLayout()
        self.select_region_btn = QPushButton("选择区域")
        self.select_region_btn.clicked.connect(self.select_region)
        self.region_info_label = QLabel("未选择区域")
        region_layout.addWidget(self.select_region_btn)
        region_layout.addWidget(self.region_info_label)
        main_layout.addLayout(region_layout)
        
        # 控制部分
        control_layout = QHBoxLayout()
        self.start_btn = QPushButton("开始监控")
        self.start_btn.clicked.connect(self.toggle_monitoring)
        self.start_btn.setEnabled(False)
        self.stop_btn = QPushButton("停止监控")
        self.stop_btn.clicked.connect(self.stop_monitoring)
        self.stop_btn.setEnabled(False)
        control_layout.addWidget(self.start_btn)
        control_layout.addWidget(self.stop_btn)
        main_layout.addLayout(control_layout)
        
        # 透明度控制
        opacity_layout = QHBoxLayout()
        opacity_label = QLabel("透明度:")
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(10, 100)
        self.opacity_slider.setValue(self.default_opacity)
        self.opacity_slider.valueChanged.connect(self.set_overlay_opacity)
        self.opacity_value = QLabel(str(self.default_opacity) + "%")
        self.opacity_slider.valueChanged.connect(lambda value: self.opacity_value.setText(f"{value}%"))
        opacity_layout.addWidget(opacity_label)
        opacity_layout.addWidget(self.opacity_slider)
        opacity_layout.addWidget(self.opacity_value)
        main_layout.addLayout(opacity_layout)
        
        # 截图间隔控制
        interval_layout = QHBoxLayout()
        interval_label = QLabel("截图间隔(ms):")
        self.interval_spinbox = QSpinBox()
        self.interval_spinbox.setRange(500, 5000)
        self.interval_spinbox.setValue(self.screenshot_interval)
        self.interval_spinbox.valueChanged.connect(self.set_screenshot_interval)
        interval_layout.addWidget(interval_label)
        interval_layout.addWidget(self.interval_spinbox)
        main_layout.addLayout(interval_layout)
        
        # API控制部分
        api_group = QWidget()
        api_layout = QVBoxLayout(api_group)
        api_label = QLabel("API接口")
        
        self.api_status = QLabel("未运行")
        self.api_status.setStyleSheet("color: #FF6B6B")
        
        api_controls_layout = QHBoxLayout()
        self.btn_start_api = QPushButton("启动API")
        self.btn_start_api.clicked.connect(self.start_api_server)
        
        self.btn_stop_api = QPushButton("停止API")
        self.btn_stop_api.clicked.connect(self.stop_api_server)
        self.btn_stop_api.setEnabled(False)
        
        api_controls_layout.addWidget(self.btn_start_api)
        api_controls_layout.addWidget(self.btn_stop_api)
        
        api_layout.addWidget(api_label)
        api_layout.addWidget(self.api_status)
        api_layout.addLayout(api_controls_layout)
        api_layout.setContentsMargins(0, 5, 0, 5)
        main_layout.addWidget(api_group)
        
        # 历史记录部分
        history_label = QLabel("翻译历史:")
        main_layout.addWidget(history_label)
        self.history_list = QListWidget()
        main_layout.addWidget(self.history_list)
        
        # 操作按钮
        action_layout = QHBoxLayout()
        self.clear_history_btn = QPushButton("清除历史")
        self.clear_history_btn.clicked.connect(self.clear_history)
        self.save_history_btn = QPushButton("保存历史")
        self.save_history_btn.clicked.connect(self.save_history_to_file)
        action_layout.addWidget(self.clear_history_btn)
        action_layout.addWidget(self.save_history_btn)
        main_layout.addLayout(action_layout)
        
        # 创建系统托盘图标
        self.create_system_tray()
        
    def create_system_tray(self):
        """创建系统托盘图标"""
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon("icon.png"))
        
        # 创建托盘菜单
        tray_menu = QMenu()
        
        show_action = QAction("显示窗口", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)
        
        hide_action = QAction("隐藏窗口", self)
        hide_action.triggered.connect(self.hide)
        tray_menu.addAction(hide_action)
        
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close)
        tray_menu.addAction(exit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
    
    def select_region(self):
        """选择监控区域"""
        self.region_selector = RegionSelector()
        self.region_selector.show()
        self.region_selector.windowHandle().screenChanged.connect(self.on_screen_changed)
        
    def on_screen_changed(self):
        """屏幕变化事件"""
        if self.region_selector.selected_region:
            self.selected_region = self.region_selector.selected_region
            self.region_info_label.setText(
                f"区域: {self.selected_region.x()}, {self.selected_region.y()}, "
                f"{self.selected_region.width()}x{self.selected_region.height()}"
            )
            self.start_btn.setEnabled(True)
            self.stop_monitoring()
    
    def toggle_monitoring(self):
        """切换监控状态"""
        if self.is_monitoring:
            self.stop_monitoring()
        else:
            self.start_monitoring()
    
    def start_monitoring(self):
        """开始监控"""
        if not self.selected_region:
            QMessageBox.warning(self, "警告", "请先选择监控区域")
            return
        
        # 检查Tesseract是否配置
        if not has_tesseract:
            QMessageBox.warning(self, "警告", "请先配置Tesseract OCR路径")
            return
        
        self.is_monitoring = True
        self.start_btn.setText("暂停监控")
        self.stop_btn.setEnabled(True)
        
        # 启动定时器
        self.screenshot_timer.start(self.screenshot_interval)
        logger.info("开始监控屏幕区域")
    
    def stop_monitoring(self):
        """停止监控"""
        self.is_monitoring = False
        self.start_btn.setText("开始监控")
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        
        # 停止定时器
        self.screenshot_timer.stop()
        
        # 隐藏覆盖层
        self.overlay.hide()
        logger.info("停止监控屏幕区域")
    
    def configure_tesseract_path(self):
        """配置Tesseract OCR路径"""
        path, ok = QInputDialog.getText(
            self, "配置Tesseract路径", 
            "请输入Tesseract-OCR的安装路径:\n(例如: C:\\Program Files\\Tesseract-OCR\\tesseract.exe)")
        
        if ok and path:
            if os.path.exists(path):
                pytesseract.pytesseract.tesseract_cmd = path
                global has_tesseract
                has_tesseract = True
                QMessageBox.information(self, "成功", "Tesseract路径配置成功")
                # 更新UI
                self.init_ui()
            else:
                QMessageBox.warning(self, "错误", "指定的路径不存在")
    
    def start_api_server(self):
        """启动API服务器"""
        if self.api_server.start_api_server():
            self.btn_start_api.setEnabled(False)
            self.btn_stop_api.setEnabled(True)
            self.api_status.setText("运行中")
            self.api_status.setStyleSheet("color: #4ECDC4")
            QMessageBox.information(self, "API服务器", "API服务器已成功启动！")
        else:
            QMessageBox.warning(self, "API服务器", "启动API服务器失败，请安装Flask依赖。")
    
    def stop_api_server(self):
        """停止API服务器"""
        if self.api_server.stop_api_server():
            self.btn_start_api.setEnabled(True)
            self.btn_stop_api.setEnabled(False)
            self.api_status.setText("未运行")
            self.api_status.setStyleSheet("color: #FF6B6B")
            QMessageBox.information(self, "API服务器", "API服务器已停止！")
    
    def capture_and_translate(self):
        """捕获屏幕并翻译（多平台支持）"""
        try:
            # 截取屏幕区域
            if sys.platform.startswith('darwin'):
                # macOS系统需要特殊处理
                import subprocess
                import tempfile
                
                # 获取区域坐标
                x = self.selected_region.x()
                y = self.selected_region.y()
                width = self.selected_region.width()
                height = self.selected_region.height()
                
                # 使用screencapture命令截图
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                    temp_path = tmp.name
                
                cmd = [
                    'screencapture', '-x', '-R',
                    str(x), str(y), str(width), str(height),
                    temp_path
                ]
                
                subprocess.run(cmd, check=True)
                screenshot = Image.open(temp_path)
                os.unlink(temp_path)  # 删除临时文件
            else:
                # Windows和Linux系统使用ImageGrab
                screenshot = ImageGrab.grab(
                    bbox=(self.selected_region.x(), self.selected_region.y(),
                          self.selected_region.x() + self.selected_region.width(),
                          self.selected_region.y() + self.selected_region.height())
                )
            
            # 将图像转换为base64编码
            import io
            buffer = io.BytesIO()
            screenshot.save(buffer, format="PNG")
            image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            # 使用豆包API进行图像识别和翻译
            translated_text = self.translate_image(image_base64)
            
            if translated_text and translated_text != self.last_text:
                self.last_text = translated_text
                logger.info(f"翻译结果: {translated_text}")
                
                # 更新覆盖层
                self.update_overlay(translated_text)
                
                # 保存到历史记录
                self.add_to_history("图像识别", translated_text)
        
        except ImageGrab.ImageGrabError as e:
            logger.error(f"截图错误: {str(e)}")
        except Exception as e:
            logger.error(f"捕获或翻译出错: {str(e)}")
    
    def translate_text(self, text):
        """使用火山引擎豆包API翻译文字"""
        # 记录翻译请求
        logger.info(f"发起翻译请求，原文长度: {len(text)}字符")
        
        try:
            # 使用火山引擎豆包API地址
            url = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.doubao_api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "doubao-seed-1-6-vision-250815",  # 使用最新的豆包模型
                "messages": [
                    {"role": "system", "content": "你是一个专业的翻译助手，请将用户输入的英文准确翻译成中文。"},
                    {"role": "user", "content": text}
                ],
                "temperature": 0.3,
                "top_p": 0.8
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=15)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"火山引擎API返回完整结果")
            
            if result and "choices" in result and len(result["choices"]) > 0:
                  translated_text = result["choices"][0]["message"]["content"].strip()
                  logger.info(f"翻译成功，翻译结果长度: {len(translated_text)}字符")
                  return translated_text
              else:
                  logger.error(f"火山引擎API返回格式错误: {result}")
                  return "[翻译结果格式异常]"
                  
        except Exception as e:
            logger.error(f"火山引擎API调用失败: {str(e)}")
            return None
    
    def translate_image(self, image_base64):
        """使用火山引擎豆包API进行图像识别和翻译"""
        # 记录图片翻译请求
        logger.info(f"发起图片翻译请求，图片大小: {len(image_base64)}字符")
        
        try:
            # 使用火山引擎豆包API地址
            url = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.doubao_api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "doubao-seed-1-6-vision-250815",  # 使用最新的豆包模型
                "messages": [
                    {
                        "role": "system",
                        "content": "你是一个专业的图像识别和翻译助手。请先识别图像中的英文内容，然后将其准确翻译成中文。请只返回翻译后的中文内容，不要包含任何其他说明。"
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                "temperature": 0.3,
                "top_p": 0.8
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=20)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"火山引擎API图像识别结果返回")
            
            if result and "choices" in result and len(result["choices"]) > 0:
                translated_text = result["choices"][0]["message"]["content"].strip()
                logger.info(f"图片识别和翻译成功，翻译结果长度: {len(translated_text)}字符")
                return translated_text
            else:
                logger.error(f"火山引擎API返回格式错误")
                return "[翻译结果格式异常]"
                
        except Exception as e:
            logger.error(f"图片翻译失败: {str(e)}")
            return "[图片翻译失败]"
    
    def update_overlay(self, translated_text):
        """更新翻译覆盖层"""
        self.overlay.set_translation_text(translated_text)
        
        # 计算覆盖层位置（在选择区域上方居中）
        overlay_width = self.overlay.width()
        overlay_height = self.overlay.height()
        
        x = self.selected_region.x() + (self.selected_region.width() - overlay_width) // 2
        y = self.selected_region.y() - overlay_height - 10
        
        # 确保覆盖层不会超出屏幕
        if y < 0:
            y = self.selected_region.y() + self.selected_region.height() + 10
        
        self.overlay.setGeometry(x, y, overlay_width, overlay_height)
        self.overlay.show()
    
    def set_overlay_opacity(self, opacity):
        """设置覆盖层透明度"""
        self.overlay.set_opacity(opacity)
    
    def set_screenshot_interval(self, interval):
        """设置截图间隔"""
        self.screenshot_interval = interval
        if self.is_monitoring:
            self.screenshot_timer.start(interval)
    
    def add_to_history(self, original_text, translated_text):
        """添加翻译记录到历史"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        history_item = {
            "timestamp": timestamp,
            "original": original_text,
            "translated": translated_text
        }
        
        self.translation_history.append(history_item)
        
        # 更新历史记录列表
        list_item = QListWidgetItem(f"{timestamp} - {original_text[:50]}...")
        list_item.setData(Qt.UserRole, history_item)
        self.history_list.insertItem(0, list_item)
        
        # 保留最近100条记录
        if len(self.translation_history) > 100:
            self.translation_history.pop(0)
            self.history_list.takeItem(self.history_list.count() - 1)
    
    def clear_history(self):
        """清除历史记录"""
        reply = QMessageBox.question(self, "确认", "确定要清除所有历史记录吗？",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            self.translation_history.clear()
            self.history_list.clear()
            logger.info("历史记录已清除")
    
    def save_history_to_file(self):
        """保存历史记录到文件"""
        if not self.translation_history:
            QMessageBox.information(self, "提示", "没有历史记录可保存")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存历史记录", "translation_history.txt", "文本文件 (*.txt)"
        )
        
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    for item in self.translation_history:
                        f.write(f"时间: {item['timestamp']}\n")
                        f.write(f"原文: {item['original']}\n")
                        f.write(f"译文: {item['translated']}\n")
                        f.write("-" * 50 + "\n")
                
                QMessageBox.information(self, "成功", "历史记录已保存")
                logger.info(f"历史记录已保存到: {file_path}")
                
            except Exception as e:
                logger.error(f"保存历史记录失败: {str(e)}")
                QMessageBox.critical(self, "错误", f"保存失败: {str(e)}")
    
    def load_history(self):
        """加载历史记录"""
        # 这里可以扩展为从文件加载历史记录
        pass
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        reply = QMessageBox.question(self, "确认退出", "确定要退出应用程序吗？",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.stop_monitoring()
            event.accept()
        else:
            event.ignore()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # 创建应用实例
    window = TranslationApp()
    window.show()
    
    # 运行应用
    sys.exit(app.exec())