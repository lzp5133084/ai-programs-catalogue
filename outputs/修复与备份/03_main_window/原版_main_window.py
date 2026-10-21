from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox, QFormLayout, QProgressBar, QMessageBox, QFileDialog)
from PyQt6.QtGui import QIcon, QFont, QColor, QPalette, QLinearGradient, QBrush, QPainter, QPen
from PyQt6.QtCore import Qt, QTimer, QDateTime, QSize
import os
import datetime
import psutil
from models import get_db, AppUsage, UsageRecord
from monitor import AppMonitor
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import random

# 设置matplotlib中文字体
plt.rcParams["font.family"] = ["SimHei", "WenQuanYi Micro Hei", "Heiti TC"]

class CuteProgressBar(QProgressBar):
    """自定义可爱风格进度条"""
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 绘制背景
        bg_rect = self.rect()
        bg_color = QColor(240, 240, 240)
        painter.fillRect(bg_rect, bg_color)

        # 绘制进度
        progress = self.value()
        if progress > 0:
            progress_rect = bg_rect.adjusted(2, 2, -2, -2)
            progress_width = int(progress_rect.width() * progress / 100)
            progress_rect.setWidth(progress_width)

            # 创建渐变颜色
            gradient = QLinearGradient(progress_rect.topLeft(), progress_rect.topRight())
            colors = [
                (QColor(255, 183, 197), 0.0),   # 粉色
                (QColor(255, 127, 80), 0.5),    # 珊瑚色
                (QColor(255, 193, 7), 1.0)      # 琥珀色
            ]
            for color, pos in colors:
                gradient.setColorAt(pos, color)

            painter.fillRect(progress_rect, QBrush(gradient))

        # 绘制文字
        font = painter.font()
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(bg_rect, Qt.AlignmentFlag.AlignCenter, f"{progress}%")

class UsageChartWidget(QWidget):
    """使用情况图表组件"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        self.figure = plt.Figure(figsize=(5, 4), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        self.setLayout(layout)

    def update_chart(self, data, title, x_label, y_label):
        """更新图表数据"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        # 生成可爱的颜色
        colors = [(random.uniform(0.5, 1), random.uniform(0.5, 1), random.uniform(0.8, 1)) for _ in data]

        labels = [item[0] for item in data]
        values = [item[1] for item in data]

        ax.bar(labels, values, color=colors)
        ax.set_title(title)
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        plt.xticks(rotation=45, ha='right')
        self.figure.tight_layout()
        self.canvas.draw()

class AppMonitorWindow(QMainWindow):
    """应用监控主窗口"""
    def __init__(self):
        super().__init__()
        self.monitor = AppMonitor()
        self.init_ui()
        self.update_file_info()
        self.start_auto_refresh()

    def init_ui(self):
        """初始化用户界面"""
        # 设置窗口基本属性
        self.setWindowTitle("应用使用监控助手")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(1000, 700)

        # 设置窗口样式
        self.setStyleSheet(""
            "QMainWindow {background-color: #f8f9fa;}"
            "QGroupBox {border: 2px solid #ffccd5; border-radius: 10px; margin-top: 10px; background-color: white;}"
            "QGroupBox::title {subcontrol-origin: margin; left: 10px; padding: 0 5px 0 5px; color: #e63946; font-weight: bold;}"
            "QPushButton {background-color: #ffb7c5; color: #333; border-radius: 20px; padding: 8px 16px; font-weight: bold; border: none;}"
            "QPushButton:hover {background-color: #ff8fa3;}"
            "QPushButton:pressed {background-color: #ff5c8a;}"
            "QLabel {color: #333;}"
            "QTabWidget::pane {border: 1px solid #ffccd5; border-radius: 8px; background-color: white;}"
            "QTabBar::tab {background-color: #ffe5ec; color: #333; padding: 8px 16px; border-radius: 8px 8px 0 0; margin-right: 2px;}"
            "QTabBar::tab:selected {background-color: white; border-top: 2px solid #e63946;}"
            "QTableWidget {border: 1px solid #ffccd5; border-radius: 8px;}"
            "QHeaderView::section {background-color: #ffe5ec; color: #333; padding: 6px; border-radius: 4px;}"
        )

        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # 创建标题区域
        title_layout = QHBoxLayout()
        title_label = QLabel("📱 应用使用监控助手")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_layout.addWidget(title_label)
        main_layout.addLayout(title_layout)

        # 创建控制区域
        control_group = QGroupBox("监控控制")
        control_layout = QHBoxLayout()

        self.start_btn = QPushButton("▶️ 开始监控")
        self.start_btn.clicked.connect(self.toggle_monitoring)
        self.start_btn.setMinimumHeight(40)

        self.save_btn = QPushButton("💾 保存记录")
        self.save_btn.clicked.connect(self.save_records)
        self.save_btn.setMinimumHeight(40)

        self.load_btn = QPushButton("📂 加载记录")
        self.load_btn.clicked.connect(self.load_records)
        self.load_btn.setMinimumHeight(40)

        self.ok_btn = QPushButton("✅ OK (另存为新文件)")
        self.ok_btn.clicked.connect(self.handle_ok_command)
        self.ok_btn.setMinimumHeight(40)

        control_layout.addWidget(self.start_btn)
        control_layout.addWidget(self.save_btn)
        control_layout.addWidget(self.load_btn)
        control_layout.addWidget(self.ok_btn)
        control_group.setLayout(control_layout)
        main_layout.addWidget(control_group)

        # 创建文件信息区域
        file_info_group = QGroupBox("文件信息")
        file_info_layout = QFormLayout()

        self.size_label = QLabel("计算中...")
        self.modified_label = QLabel("计算中...")

        file_info_layout.addRow("程序大小:", self.size_label)
        file_info_layout.addRow("上次修改时间:", self.modified_label)
        file_info_group.setLayout(file_info_layout)
        main_layout.addWidget(file_info_group)

        # 创建数据统计区域
        stats_group = QGroupBox("使用统计")
        stats_layout = QVBoxLayout()

        # 创建标签页
        self.tab_widget = QTabWidget()

        # 时长排行标签页
        self.duration_tab = QWidget()
        duration_layout = QVBoxLayout(self.duration_tab)
        self.duration_chart = UsageChartWidget()
        self.duration_table = QTableWidget()
        self.duration_table.setColumnCount(3)
        self.duration_table.setHorizontalHeaderLabels(["应用名称", "使用时长", "占比"])
        self.duration_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        duration_layout.addWidget(self.duration_chart)
        duration_layout.addWidget(self.duration_table)
        self.tab_widget.addTab(self.duration_tab, "⏱️ 使用时长排行")

        # 打开顺序标签页
        self.order_tab = QWidget()
        order_layout = QVBoxLayout(self.order_tab)
        self.order_table = QTableWidget()
        self.order_table.setColumnCount(4)
        self.order_table.setHorizontalHeaderLabels(["打开顺序", "应用名称", "打开时间", "关闭时间"])
        self.order_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        order_layout.addWidget(self.order_table)
        self.tab_widget.addTab(self.order_tab, "📊 打开时间顺序")

        # 频率排行标签页
        self.frequency_tab = QWidget()
        frequency_layout = QVBoxLayout(self.frequency_tab)
        self.frequency_chart = UsageChartWidget()
        self.frequency_table = QTableWidget()
        self.frequency_table.setColumnCount(2)
        self.frequency_table.setHorizontalHeaderLabels(["应用名称", "打开次数"])
        self.frequency_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        frequency_layout.addWidget(self.frequency_chart)
        frequency_layout.addWidget(self.frequency_table)
        self.tab_widget.addTab(self.frequency_tab, "🔄 打开频率排行")

        stats_layout.addWidget(self.tab_widget)
        stats_group.setLayout(stats_layout)
        main_layout.addWidget(stats_group)

        # 创建状态区域
        status_layout = QHBoxLayout()
        self.status_label = QLabel("监控未运行")
        self.status_label.setStyleSheet("color: #e63946; font-weight: bold;")

        self.progress_bar = CuteProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)

        status_layout.addWidget(self.status_label)
        status_layout.addWidget(self.progress_bar)
        main_layout.addLayout(status_layout)

    def toggle_monitoring(self):
        """切换监控状态"""
        if self.monitor.running:
            self.monitor.stop()
            self.start_btn.setText("▶️ 开始监控")
            self.status_label.setText("监控已停止")
            self.status_label.setStyleSheet("color: #e63946; font-weight: bold;")
        else:
            self.monitor.start()
            self.start_btn.setText("⏹️ 停止监控")
            self.status_label.setText("监控运行中...")
            self.status_label.setStyleSheet("color: #2a9d8f; font-weight: bold;")
        self.update_stats()

    def update_stats(self):
        """更新统计数据"""
        db = next(get_db())

        # 获取今日数据
        today = datetime.datetime.now().date()
        start_of_day = datetime.datetime.combine(today, datetime.time.min)

        # 更新时长排行
        duration_data = db.query(AppUsage.app_name, db.func.sum(AppUsage.active_duration).label('total_duration'))
                        .filter(AppUsage.start_time >= start_of_day)
                        .group_by(AppUsage.app_name)
                        .order_by(db.func.sum(AppUsage.active_duration).desc())
                        .all()

        # 转换为小时显示
        duration_data_with_hours = [(item[0], round(item[1]/3600, 2)) for item in duration_data]
        total_duration = sum(item[1] for item in duration_data_with_hours)

        self.duration_table.setRowCount(len(duration_data_with_hours))
        chart_data = []

        for i, (app_name, duration) in enumerate(duration_data_with_hours):
            self.duration_table.setItem(i, 0, QTableWidgetItem(app_name))
            self.duration_table.setItem(i, 1, QTableWidgetItem(f"{duration} 小时"))
            if total_duration > 0:
                percentage = round(duration / total_duration * 100, 1)
                self.duration_table.setItem(i, 2, QTableWidgetItem(f"{percentage}%"))
                chart_data.append((app_name, duration))

        self.duration_chart.update_chart(chart_data[:5], "应用使用时长排行", "应用名称", "使用时长(小时)")

        # 更新打开顺序
        order_data = db.query(AppUsage.app_name, AppUsage.start_time, AppUsage.end_time)
                      .filter(AppUsage.start_time >= start_of_day)
                      .order_by(AppUsage.start_time)
                      .all()

        self.order_table.setRowCount(len(order_data))
        for i, (app_name, start_time, end_time) in enumerate(order_data):
            self.order_table.setItem(i, 0, QTableWidgetItem(str(i+1)))
            self.order_table.setItem(i, 1, QTableWidgetItem(app_name))
            self.order_table.setItem(i, 2, QTableWidgetItem(start_time.strftime("%H:%M:%S")))
            end_time_str = end_time.strftime("%H:%M:%S") if end_time else "运行中"
            self.order_table.setItem(i, 3, QTableWidgetItem(end_time_str))

        # 更新频率排行
        frequency_data = db.query(AppUsage.app_name, db.func.count(AppUsage.id).label('count'))
                          .filter(AppUsage.start_time >= start_of_day)
                          .group_by(AppUsage.app_name)
                          .order_by(db.func.count(AppUsage.id).desc())
                          .all()

        self.frequency_table.setRowCount(len(frequency_data))
        chart_data = []
        for i, (app_name, count) in enumerate(frequency_data):
            self.frequency_table.setItem(i, 0, QTableWidgetItem(app_name))
            self.frequency_table.setItem(i, 1, QTableWidgetItem(str(count)))
            chart_data.append((app_name, count))

        self.frequency_chart.update_chart(chart_data[:5], "应用打开频率排行", "应用名称", "打开次数")

        db.close()

    def start_auto_refresh(self):
        """启动自动刷新"""
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_stats)
        self.timer.timeout.connect(self.update_progress)
        self.timer.start(5000)  # 每5秒刷新一次

    def update_progress(self):
        """更新进度条"""
        current_time = datetime.datetime.now()
        seconds_in_day = current_time.hour * 3600 + current_time.minute * 60 + current_time.second
        percentage = (seconds_in_day / 86400) * 100  # 86400秒 = 24小时
        self.progress_bar.setValue(int(percentage))

    def update_file_info(self):
        """更新文件信息"""
        # 计算程序大小
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(os.path.dirname(os.path.abspath(__file__))):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                total_size += os.path.getsize(fp)

        # 转换为MB
        size_mb = round(total_size / (1024 * 1024), 2)
        self.size_label.setText(f"{size_mb} MB")

        # 获取最后修改时间
        latest_modified = 0
        for dirpath, dirnames, filenames in os.walk(os.path.dirname(os.path.abspath(__file__))):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                modified_time = os.path.getmtime(fp)
                if modified_time > latest_modified:
                    latest_modified = modified_time

        modified_datetime = datetime.datetime.fromtimestamp(latest_modified)
        self.modified_label.setText(modified_datetime.strftime("%Y-%m-%d %H:%M:%S"))

    def save_records(self):
        """保存记录"""
        try:
            options = QFileDialog.Options()
            file_path, _ = QFileDialog.getSaveFileName(
                self, "保存记录", "", "数据库文件 (*.db);;所有文件 (*)", options=options)
            if file_path:
                # 这里简化处理，实际应该复制数据库文件
                import shutil
                shutil.copy2("app_monitor.db", file_path)
                QMessageBox.information(self, "成功", f"记录已保存到: {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存失败: {str(e)}")

    def load_records(self):
        """加载记录"""
        try:
            options = QFileDialog.Options()
            file_path, _ = QFileDialog.getOpenFileName(
                self, "加载记录", "", "数据库文件 (*.db);;所有文件 (*)", options=options)
            if file_path:
                # 这里简化处理，实际应该替换当前数据库
                import shutil
                # 先停止监控
                was_running = self.monitor.running
                if was_running:
                    self.monitor.stop()
                # 复制文件
                shutil.copy2(file_path, "app_monitor.db")
                # 重启监控
                if was_running:
                    self.monitor.start()
                # 更新界面
                self.update_stats()
                QMessageBox.information(self, "成功", f"记录已加载: {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载失败: {str(e)}")

    def handle_ok_command(self):
        """处理OK命令，另存为新文件"""
        try:
            # 查找最新的序号
            base_dir = os.path.dirname(os.path.abspath(__file__))
            max_num = 0
            for f in os.listdir(base_dir):
                if f.startswith("app_monitor(") and f.endswith(").db"):
                    try:
                        num = int(f[12:-3])
                        if num > max_num:
                            max_num = num
                    except ValueError:
                        continue

            # 创建新文件名
            new_num = max_num + 1
            new_file = f"app_monitor({new_num}).db"
            new_path = os.path.join(base_dir, new_file)

            # 复制当前数据库
            import shutil
            shutil.copy2("app_monitor.db", new_path)
            QMessageBox.information(self, "成功", f"已另存为新文件: {new_file}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"另存为失败: {str(e)}")

    def closeEvent(self, event):
        """窗口关闭事件"""
        if self.monitor.running:
            self.monitor.stop()
        event.accept()