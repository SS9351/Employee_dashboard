import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget,
    QFrame, QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox, QDateEdit, QTextEdit, QPushButton, QMessageBox
)
from PyQt6.QtCore import Qt, QDate, QRectF
from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont, QPen
from utils.paths import get_asset_path

class AttendanceChartWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(400, 250)
        self.stats = {"present": 0, "absent": 0, "approved_leaves": 0}

    def update_stats(self, present, absent, leaves):
        self.stats = {"present": present, "absent": absent, "approved_leaves": leaves}
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        total = sum(self.stats.values())
        if total == 0:
            painter.setPen(QPen(QColor("#7f8c8d"), 2))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No Data Available Yet For This Month")
            return
            
        colors = {
            "present": QColor(46, 204, 113),         # Green
            "absent": QColor(231, 76, 60),           # Red
            "approved_leaves": QColor(241, 196, 15)  # Yellow
        }
        
        rect = QRectF(20, 20, 210, 210)
        start_angle = 0
        
        for key, val in self.stats.items():
            if val > 0:
                span_angle = int((val / total) * 360 * 16)
                painter.setBrush(colors[key])
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawPie(rect, start_angle, span_angle)
                start_angle += span_angle
                
        # Draw Legend
        legend_x = 250
        legend_y = 60
        for key, color in colors.items():
            painter.setBrush(color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRect(legend_x, legend_y, 15, 15)
            painter.setPen(QPen(Qt.GlobalColor.black))
            painter.setFont(QFont("Arial", 11, QFont.Weight.Bold))
            readable_key = key.replace("_", " ").title()
            painter.drawText(legend_x + 25, legend_y + 13, f"{readable_key}: {self.stats[key]} Days")
            legend_y += 35

class DashboardWindow(QWidget):
    def __init__(self, api_client, device_info, user_info=None):
        super().__init__()
        self.api_client = api_client
        self.device_info = device_info
        self.user_info = user_info or {}
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Header Panel
        header = QFrame()
        header.setObjectName("Card")
        header.setFixedHeight(100)
        h_layout = QHBoxLayout(header)

        # Logo
        logo_label = QLabel()
        logo_path = get_asset_path("logo.png")
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path).scaledToHeight(60, Qt.TransformationMode.SmoothTransformation)
            logo_label.setPixmap(pixmap)
        else:
            logo_label.setText("LOGO")
            logo_label.setStyleSheet("color: #16A085; font-weight: bold; font-size: 20px;")
        
        h_layout.addWidget(logo_label)

        # Welcome Text
        welcome = QLabel(f"Sahastra Finnovations Pvt. Ltd.\nWelcome, {self.user_info.get('name', 'Employee')}!")
        welcome.setObjectName("MainTitle")
        welcome.setStyleSheet("font-size: 20px;")
        h_layout.addWidget(welcome)

        h_layout.addStretch()
        
        # Logout Button
        self.logout_btn = QPushButton("Logout Securely")
        self.logout_btn.setObjectName("DangerButton")
        self.logout_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        h_layout.addWidget(self.logout_btn)

        layout.addWidget(header)

        # Tab Widget
        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_dashboard_tab(), "Overview")
        self.tabs.addTab(self.create_leaves_tab(), "Leave Management")
        
        if self.user_info.get("is_admin", False):
            self.tabs.addTab(self.create_admin_tab(), "Admin Portal")
            
        layout.addWidget(self.tabs)

    def create_dashboard_tab(self):
        tab = QWidget()
        vbox = QVBoxLayout()

        # System Info Card
        card = QFrame()
        card.setObjectName("Card")
        cl = QVBoxLayout()
        cl.addWidget(QLabel("<b>Your Active Session Info (Monitored):</b>"))
        cl.addWidget(QLabel(f"Hostname: {self.device_info.get('hostname')}"))
        cl.addWidget(QLabel(f"OS: {self.device_info.get('os_info')}"))
        cl.addWidget(QLabel(f"MAC: {self.device_info.get('mac_address')}"))
        cl.addWidget(QLabel(f"IP: {self.device_info.get('local_ip')}"))
        cl.addWidget(QLabel("Status: \u2705 ONLINE & LOGGED IN"))
        card.setLayout(cl)
        vbox.addWidget(card)

        # Attendance Chart Card
        chart_card = QFrame()
        chart_card.setObjectName("Card")
        cl2 = QVBoxLayout()
        cl2.addWidget(QLabel("<b>My Monthly Attendance Overview:</b>"))
        
        self.chart_widget = AttendanceChartWidget()
        cl2.addWidget(self.chart_widget)
        
        ref_stats = QPushButton("Refresh Stats")
        ref_stats.clicked.connect(self.load_attendance_stats)
        cl2.addWidget(ref_stats)
        
        chart_card.setLayout(cl2)
        vbox.addWidget(chart_card)

        vbox.addStretch()
        tab.setLayout(vbox)
        
        # Trigger chart load
        self.load_attendance_stats()
        
        return tab

    def load_attendance_stats(self):
        data, status = self.api_client.get_attendance_stats()
        if status == 200:
            self.chart_widget.update_stats(
                data.get("present", 0),
                data.get("absent", 0),
                data.get("approved_leaves", 0)
            )

    def create_leaves_tab(self):
        tab = QWidget()
        vbox = QVBoxLayout()

        # Apply Leave Form Card
        form_card = QFrame()
        form_card.setObjectName("Card")
        form_layout = QVBoxLayout()
        form_layout.addWidget(QLabel("<b>Apply for Leave</b>"))

        hbox1 = QHBoxLayout()
        hbox1.addWidget(QLabel("Leave Type:"))
        self.leave_type_combo = QComboBox()
        self.leave_type_combo.addItems(["LONG (Multi-day)", "PRIOR (One day prior)", "EMERGENCY (Same day)"])
        hbox1.addWidget(self.leave_type_combo)
        form_layout.addLayout(hbox1)

        hbox2 = QHBoxLayout()
        hbox2.addWidget(QLabel("Start Date:"))
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate())
        hbox2.addWidget(self.start_date)

        hbox2.addWidget(QLabel("End Date:"))
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())
        hbox2.addWidget(self.end_date)
        form_layout.addLayout(hbox2)

        form_layout.addWidget(QLabel("Reason for leave:"))
        self.reason_input = QTextEdit()
        self.reason_input.setFixedHeight(80)
        form_layout.addWidget(self.reason_input)

        self.apply_btn = QPushButton("Submit Leave Request")
        self.apply_btn.setObjectName("PrimaryButton")
        self.apply_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.apply_btn.clicked.connect(self.submit_leave)
        form_layout.addWidget(self.apply_btn)

        form_card.setLayout(form_layout)
        vbox.addWidget(form_card)

        # Leave History Table
        history_card = QFrame()
        history_card.setObjectName("Card")
        hist_layout = QVBoxLayout()
        hist_layout.addWidget(QLabel("<b>Your Recent Leaves</b>"))
        self.history_table = QTableWidget(0, 4)
        self.history_table.setHorizontalHeaderLabels(["Date Range", "Type", "Reason", "Status"])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        hist_layout.addWidget(self.history_table)
        
        self.refresh_btn = QPushButton("Refresh History")
        self.refresh_btn.clicked.connect(self.load_leave_history)
        hist_layout.addWidget(self.refresh_btn)
        
        history_card.setLayout(hist_layout)
        vbox.addWidget(history_card)

        tab.setLayout(vbox)
        return tab

    def load_leave_history(self):
        data, status = self.api_client.get_leaves()
        if status == 200:
            leaves = data.get("leaves", [])
            self.history_table.setRowCount(len(leaves))
            for i, lv in enumerate(leaves):
                self.history_table.setItem(i, 0, QTableWidgetItem(f"{lv.get('start_date')} to {lv.get('end_date')}"))
                self.history_table.setItem(i, 1, QTableWidgetItem(lv.get('type')))
                self.history_table.setItem(i, 2, QTableWidgetItem(lv.get('reason')))
                self.history_table.setItem(i, 3, QTableWidgetItem(lv.get('status')))
        else:
            QMessageBox.warning(self, "Error", "Failed to fetch leave history")

    def submit_leave(self):
        l_type = self.leave_type_combo.currentText().split()[0]
        start = self.start_date.date().toString(Qt.DateFormat.ISODate)
        end = self.end_date.date().toString(Qt.DateFormat.ISODate)
        reason = self.reason_input.toPlainText().strip()
        
        if not reason:
            QMessageBox.warning(self, "Error", "Reason is required.")
            return
            
        self.apply_btn.setEnabled(False)
        self.apply_btn.setText("Submitting...")
        
        # Simulating API Call
        data, status = self.api_client.apply_leave(l_type, reason, start, end)
        self.apply_btn.setEnabled(True)
        self.apply_btn.setText("Submit Leave Request")
        
        if status == 200:
            QMessageBox.information(self, "Success", "Leave request submitted successfully.")
            self.reason_input.clear()
            self.load_leave_history()
        else:
            QMessageBox.warning(self, "Error", f"Failed to submit leave: {data.get('error', 'Unknown Error')}")

    def create_admin_tab(self):
        tab = QWidget()
        vbox = QVBoxLayout()
        vbox.setSpacing(10)

        # Internal Admin Tabs
        self.admin_tabs = QTabWidget()
        
        # 1. Leaves & Approvals
        leaves_tab = QWidget()
        leaves_lay = QVBoxLayout(leaves_tab)
        
        hdr1 = QHBoxLayout()
        hdr1.addWidget(QLabel("<b>Pending & Recent Leave Requests</b>"))
        hdr1.addStretch()
        hdr1.addWidget(QLabel("Filter by Employee:"))
        self.leaves_emp_filter = QComboBox()
        self.leaves_emp_filter.currentIndexChanged.connect(self.filter_admin_leaves)
        hdr1.addWidget(self.leaves_emp_filter)
        leaves_lay.addLayout(hdr1)
        
        self.admin_leaves_table = QTableWidget(0, 5)
        self.admin_leaves_table.setHorizontalHeaderLabels(["Employee", "Type", "Reason", "Status", "Action"])
        self.admin_leaves_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.admin_leaves_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)
        self.admin_leaves_table.setColumnWidth(4, 180)
        leaves_lay.addWidget(self.admin_leaves_table)
        
        refresh_l = QPushButton("Refresh Leaves")
        refresh_l.clicked.connect(self.load_admin_leaves)
        leaves_lay.addWidget(refresh_l)
        
        self.admin_tabs.addTab(leaves_tab, "Leave Management")

        # 2. Live Attendance
        att_tab = QWidget()
        att_lay = QVBoxLayout(att_tab)
        
        hdr2 = QHBoxLayout()
        hdr2.addWidget(QLabel("<b>Today's Live Attendance Platform</b>"))
        hdr2.addStretch()
        hdr2.addWidget(QLabel("Filter by Employee:"))
        self.att_emp_filter = QComboBox()
        self.att_emp_filter.currentIndexChanged.connect(self.filter_admin_attendance)
        hdr2.addWidget(self.att_emp_filter)
        att_lay.addLayout(hdr2)
        
        self.admin_att_table = QTableWidget(0, 5)
        self.admin_att_table.setHorizontalHeaderLabels(["Employee", "Login Time", "Logout Time", "IP Address", "MAC Address"])
        self.admin_att_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        att_lay.addWidget(self.admin_att_table)
        
        refresh_a = QPushButton("Refresh Attendance")
        refresh_a.clicked.connect(self.load_admin_attendance)
        att_lay.addWidget(refresh_a)
        
        self.admin_tabs.addTab(att_tab, "Attendance Tracker")

        # 3. Activity Logs
        logs_tab = QWidget()
        logs_lay = QVBoxLayout(logs_tab)
        
        hdr3 = QHBoxLayout()
        hdr3.addWidget(QLabel("<b>Recent Activity Logs</b>"))
        hdr3.addStretch()
        hdr3.addWidget(QLabel("Filter by Employee:"))
        self.logs_emp_filter = QComboBox()
        self.logs_emp_filter.currentIndexChanged.connect(self.filter_admin_logs)
        hdr3.addWidget(self.logs_emp_filter)
        logs_lay.addLayout(hdr3)
        
        self.admin_logs_table = QTableWidget(0, 4)
        self.admin_logs_table.setHorizontalHeaderLabels(["Employee", "Time", "Application", "Window Title"])
        self.admin_logs_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        logs_lay.addWidget(self.admin_logs_table)
        
        refresh_lg = QPushButton("Refresh Logs")
        refresh_lg.clicked.connect(self.load_admin_logs)
        logs_lay.addWidget(refresh_lg)
        
        self.admin_tabs.addTab(logs_tab, "Application Logs")
        
        # 4. Users & Resets
        sys_tab = QWidget()
        sys_lay = QVBoxLayout(sys_tab)
        
        hdr4 = QHBoxLayout()
        hdr4.addWidget(QLabel("<b>Password Reset Requests</b>"))
        hdr4.addStretch()
        hdr4.addWidget(QLabel("Filter by Employee:"))
        self.resets_emp_filter = QComboBox()
        self.resets_emp_filter.currentIndexChanged.connect(self.filter_admin_resets)
        hdr4.addWidget(self.resets_emp_filter)
        sys_lay.addLayout(hdr4)
        
        self.admin_resets_table = QTableWidget(0, 5)
        self.admin_resets_table.setHorizontalHeaderLabels(["ID", "Employee", "Username", "Status", "Action"])
        self.admin_resets_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        sys_lay.addWidget(self.admin_resets_table)
        
        refresh_sys = QPushButton("Refresh Requests")
        refresh_sys.clicked.connect(self.load_admin_resets)
        sys_lay.addWidget(refresh_sys)
        
        self.admin_tabs.addTab(sys_tab, "User Management")

        # 5. Actual Attendance (Duration >= 6 hrs)
        actual_tab = QWidget()
        act_lay = QVBoxLayout(actual_tab)
        
        hdr5 = QHBoxLayout()
        hdr5.addWidget(QLabel("<b>Actual Attendance Metrics (> 6 Hrs = Present)</b>"))
        hdr5.addStretch()
        hdr5.addWidget(QLabel("Filter by Employee:"))
        self.actual_emp_filter = QComboBox()
        self.actual_emp_filter.currentIndexChanged.connect(self.filter_actual_attendance)
        hdr5.addWidget(self.actual_emp_filter)
        act_lay.addLayout(hdr5)
        
        self.admin_actual_table = QTableWidget(0, 6)
        self.admin_actual_table.setHorizontalHeaderLabels(["Date", "Employee", "Login Time", "Logout Time", "Duration", "Final Status"])
        self.admin_actual_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        act_lay.addWidget(self.admin_actual_table)
        
        refresh_act = QPushButton("Refresh Actual Attendance")
        refresh_act.clicked.connect(self.load_actual_attendance)
        act_lay.addWidget(refresh_act)
        
        self.admin_tabs.addTab(actual_tab, "Actual Attendance")

        vbox.addWidget(self.admin_tabs)
        tab.setLayout(vbox)
        
        # Initial Load
        self.populate_employee_filters()
        self.load_admin_leaves()
        self.load_admin_attendance()
        self.load_admin_logs()
        self.load_admin_resets()
        self.load_actual_attendance()
        
        return tab

    def populate_employee_filters(self):
        data, status = self.api_client.get_all_users()
        if status == 200:
            users = data.get("users", [])
            for combo in [self.leaves_emp_filter, self.att_emp_filter, self.logs_emp_filter, self.resets_emp_filter, self.actual_emp_filter]:
                combo.blockSignals(True)
                combo.clear()
                combo.addItem("All Employees")
                for u in users:
                    name = u.get("full_name") or u.get("username")
                    combo.addItem(name)
                combo.blockSignals(False)

    def filter_table_by_employee(self, table, combo, emp_col=0):
        selected_emp = combo.currentText()
        if not selected_emp: return
        for row in range(table.rowCount()):
            if selected_emp == "All Employees":
                table.setRowHidden(row, False)
            else:
                item = table.item(row, emp_col)
                if item:
                    table.setRowHidden(row, item.text() != selected_emp)

    def filter_admin_leaves(self):
        self.filter_table_by_employee(self.admin_leaves_table, self.leaves_emp_filter, 0)
        
    def filter_admin_attendance(self):
        self.filter_table_by_employee(self.admin_att_table, self.att_emp_filter, 0)
        
    def filter_admin_logs(self):
        self.filter_table_by_employee(self.admin_logs_table, self.logs_emp_filter, 0)

    def filter_admin_resets(self):
        self.filter_table_by_employee(self.admin_resets_table, self.resets_emp_filter, 1)

    def filter_actual_attendance(self):
        self.filter_table_by_employee(self.admin_actual_table, self.actual_emp_filter, 1)

    def load_admin_leaves(self):
        data, status = self.api_client.get_admin_leaves()
        if status == 200:
            leaves = data.get("leaves", [])
            self.admin_leaves_table.setRowCount(0)
            self.admin_leaves_table.setRowCount(len(leaves))
            
            for i, lv in enumerate(leaves):
                self.admin_leaves_table.setItem(i, 0, QTableWidgetItem(lv.get("employee_name", "")))
                self.admin_leaves_table.setItem(i, 1, QTableWidgetItem(lv.get("type", "")))
                self.admin_leaves_table.setItem(i, 2, QTableWidgetItem(lv.get("reason", "")))
                
                status_item = QTableWidgetItem(lv.get("status", ""))
                self.admin_leaves_table.setItem(i, 3, status_item)
                
                # Action Buttons
                if lv.get("status") == "PENDING":
                    action_widget = QWidget()
                    btn_lay = QHBoxLayout()
                    btn_lay.setContentsMargins(0, 0, 0, 0)
                    
                    btn_appr = QPushButton("Approve")
                    btn_appr.setMaximumWidth(80)
                    btn_appr.setStyleSheet("background-color: #2ecc71; color: white;")
                    btn_appr.clicked.connect(lambda checked, lid=lv.get("id"): self.admin_update_leave(lid, "APPROVED"))
                    
                    btn_rej = QPushButton("Reject")
                    btn_rej.setMaximumWidth(80)
                    btn_rej.setStyleSheet("background-color: #e74c3c; color: white;")
                    btn_rej.clicked.connect(lambda checked, lid=lv.get("id"): self.admin_update_leave(lid, "REJECTED"))
                    
                    btn_lay.addWidget(btn_appr)
                    btn_lay.addWidget(btn_rej)
                    action_widget.setLayout(btn_lay)
                    self.admin_leaves_table.setCellWidget(i, 4, action_widget)
                else:
                    self.admin_leaves_table.setItem(i, 4, QTableWidgetItem("-"))
            self.filter_admin_leaves()

    def admin_update_leave(self, leave_id, status):
        data, req_status = self.api_client.update_leave_status(leave_id, status)
        if req_status == 200:
            QMessageBox.information(self, "Success", f"Leave {status.lower()} successfully.")
            self.load_admin_leaves()
        else:
            QMessageBox.warning(self, "Error", "Failed to update leave request")

    def load_admin_attendance(self):
        data, status = self.api_client.get_admin_attendance()
        if status == 200:
            att = data.get("attendance", [])
            self.admin_att_table.setRowCount(0)
            self.admin_att_table.setRowCount(len(att))
            for i, r in enumerate(att):
                self.admin_att_table.setItem(i, 0, QTableWidgetItem(r.get("employee_name")))
                self.admin_att_table.setItem(i, 1, QTableWidgetItem(r.get("login_time")))
                self.admin_att_table.setItem(i, 2, QTableWidgetItem(r.get("logout_time")))
                self.admin_att_table.setItem(i, 3, QTableWidgetItem(r.get("ip")))
                self.admin_att_table.setItem(i, 4, QTableWidgetItem(r.get("mac_address", "")))
            self.filter_admin_attendance()

    def load_admin_logs(self):
        data, status = self.api_client.get_admin_logs()
        if status == 200:
            logs = data.get("logs", [])
            self.admin_logs_table.setRowCount(0)
            self.admin_logs_table.setRowCount(len(logs))
            for i, log in enumerate(logs):
                self.admin_logs_table.setItem(i, 0, QTableWidgetItem(log.get("employee_name")))
                self.admin_logs_table.setItem(i, 1, QTableWidgetItem(log.get("time")))
                self.admin_logs_table.setItem(i, 2, QTableWidgetItem(log.get("app_name")))
                self.admin_logs_table.setItem(i, 3, QTableWidgetItem(log.get("raw_title")))
            self.filter_admin_logs()

    def load_admin_resets(self):
        data, status = self.api_client.get_reset_requests()
        if status == 200:
            reqs = data.get("requests", [])
            self.admin_resets_table.setRowCount(0)
            self.admin_resets_table.setRowCount(len(reqs))
            for i, r in enumerate(reqs):
                self.admin_resets_table.setItem(i, 0, QTableWidgetItem(str(r.get("id"))))
                self.admin_resets_table.setItem(i, 1, QTableWidgetItem(r.get("employee_name")))
                self.admin_resets_table.setItem(i, 2, QTableWidgetItem(r.get("username")))
                
                status_item = QTableWidgetItem(r.get("status"))
                self.admin_resets_table.setItem(i, 3, status_item)
                
                if r.get("status") == "PENDING":
                    action_widget = QWidget()
                    btn_lay = QHBoxLayout(action_widget)
                    btn_lay.setContentsMargins(0, 0, 0, 0)
                    btn_appr = QPushButton("Approve Reset")
                    btn_appr.setMaximumWidth(120)
                    btn_appr.setStyleSheet("background-color: #2ecc71; color: white;")
                    btn_appr.clicked.connect(lambda checked, rid=r.get("id"): self.admin_approve_reset(rid))
                    btn_lay.addWidget(btn_appr)
                    self.admin_resets_table.setCellWidget(i, 4, action_widget)
                else:
                    self.admin_resets_table.setItem(i, 4, QTableWidgetItem("-"))
            self.filter_admin_resets()

    def load_actual_attendance(self):
        data, status = self.api_client.get_admin_actual_attendance()
        if status == 200:
            att = data.get("actual_attendance", [])
            self.admin_actual_table.setRowCount(0)
            self.admin_actual_table.setRowCount(len(att))
            for i, r in enumerate(att):
                self.admin_actual_table.setItem(i, 0, QTableWidgetItem(r.get("date")))
                self.admin_actual_table.setItem(i, 1, QTableWidgetItem(r.get("employee_name")))
                self.admin_actual_table.setItem(i, 2, QTableWidgetItem(r.get("login_time")))
                self.admin_actual_table.setItem(i, 3, QTableWidgetItem(r.get("logout_time")))
                self.admin_actual_table.setItem(i, 4, QTableWidgetItem(str(r.get("duration"))))
                
                status_str = r.get("status", "")
                status_item = QTableWidgetItem(status_str)
                if "Present" in status_str:
                    status_item.setForeground(QColor(46, 204, 113)) # Green
                elif "Absent" in status_str:
                    status_item.setForeground(QColor(231, 76, 60)) # Red
                self.admin_actual_table.setItem(i, 5, status_item)
            self.filter_actual_attendance()

    def admin_approve_reset(self, request_id):
        data, req_status = self.api_client.approve_reset_request(request_id)
        if req_status == 200:
            QMessageBox.information(self, "Success", "Password reset approved.")
            self.load_admin_resets()
        else:
            QMessageBox.warning(self, "Error", "Failed to approve request.")
