import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QFrame, QSpacerItem, QSizePolicy, QMessageBox,
    QGraphicsDropShadowEffect, QDialog
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QColor, QPainter
from utils.api_client import APIClient
from utils.paths import get_asset_path

class ForgotPasswordDialog(QDialog):
    def __init__(self, api_client: APIClient, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.setWindowTitle("Password Reset")
        self.setFixedSize(350, 250)
        self.setStyleSheet("""
            QDialog { background-color: #F4F7FB; }
            QLabel { color: #2C3E50; font-size: 13px; }
            QLineEdit { padding: 8px; border: 1px solid #BDC3C7; border-radius: 4px; }
            QPushButton { background-color: #4A6B9C; color: white; padding: 8px; border-radius: 4px; font-weight: bold; }
            QPushButton:hover { background-color: #3A557C; }
        """)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        self.info_label = QLabel("Enter your Employee ID to request a password reset\nor enter a new password if already approved by your Admin.")
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("👤 Employee ID")
        layout.addWidget(self.username_input)
        
        self.new_password_input = QLineEdit()
        self.new_password_input.setPlaceholderText("🔒 New Password (Leave empty if just requesting)")
        self.new_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.new_password_input)
        
        self.request_btn = QPushButton("Request Reset")
        self.request_btn.clicked.connect(self.on_request)
        layout.addWidget(self.request_btn)
        
        self.submit_new_btn = QPushButton("Submit New Password")
        self.submit_new_btn.clicked.connect(self.on_submit)
        layout.addWidget(self.submit_new_btn)
        
    def on_request(self):
        username = self.username_input.text().strip()
        if not username:
            QMessageBox.warning(self, "Error", "Please enter your Employee ID.")
            return
        
        # Test connection / create client if needed
        data, status = self.api_client.request_password_reset(username)
        if status == 200:
            QMessageBox.information(self, "Success", data.get("message", "Request sent."))
        else:
            QMessageBox.warning(self, "Error", f"Failed to request reset: {data.get('detail', data.get('error', 'Unknown Error'))}")
            
    def on_submit(self):
        username = self.username_input.text().strip()
        new_password = self.new_password_input.text()
        
        if not username or not new_password:
            QMessageBox.warning(self, "Error", "Please enter both Employee ID and your New Password.")
            return
            
        data, status = self.api_client.reset_password(username, new_password)
        if status == 200:
            QMessageBox.information(self, "Success", data.get("message", "Password Reset Successfully."))
            self.accept()
        else:
            QMessageBox.warning(self, "Error", f"Could not reset password: {data.get('detail', data.get('error', 'Unknown Error'))}")

class LoginWindow(QWidget):
    # Emits username, password when login is clicked
    login_attempted = pyqtSignal(str, str)

    def __init__(self):
        super().__init__()
        self.setObjectName("LoginBackground")
        self.bg_pixmap = None
        bg_path = get_asset_path("login_bg.png")
        if os.path.exists(bg_path):
            self.bg_pixmap = QPixmap(bg_path)
            
        self.init_ui()

    def paintEvent(self, event):
        if self.bg_pixmap and not self.bg_pixmap.isNull():
            painter = QPainter(self)
            # Scale background to fit window size smoothly
            scaled_bg = self.bg_pixmap.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            
            # Center the image
            x = (self.width() - scaled_bg.width()) // 2
            y = (self.height() - scaled_bg.height()) // 2
            painter.drawPixmap(x, y, scaled_bg)
        else:
            super().paintEvent(event)

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setLayout(main_layout)

        # Main Card Frame
        card = QFrame()
        card.setObjectName("LoginCard")
        card.setFixedWidth(420)
        
        # Add drop shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 10)
        card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(40, 40, 40, 40)
        card_layout.setSpacing(15)

        # Company Logo & Name Header
        header_layout = QVBoxLayout()
        header_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.setSpacing(5)
        
        # Logo Container
        self.logo_label = QLabel()
        self.logo_label.setFixedSize(160, 100)
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_label.setObjectName("LogoCircle")
        self.logo_label.setStyleSheet("background: transparent;")
        
        logo_path = get_asset_path("logo.png")
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path).scaled(140, 100, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.logo_label.setPixmap(pixmap)
        else:
            self.logo_label.setText("S")
            self.logo_label.setStyleSheet("font-size: 28px; color: white; font-weight: bold;")
        
        header_layout.addWidget(self.logo_label, alignment=Qt.AlignmentFlag.AlignHCenter)

        title = QLabel("Welcome!")
        title.setObjectName("LoginTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title)
        
        subtitle = QLabel("Good morning! Please clock in")
        subtitle.setObjectName("LoginSubtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(subtitle)
        
        card_layout.addLayout(header_layout)
        card_layout.addSpacing(15)

        # Username Input
        self.username_input = QLineEdit()
        self.username_input.setObjectName("LoginInput")
        self.username_input.setPlaceholderText("👤 Employee ID")
        card_layout.addWidget(self.username_input)

        # Password Input
        self.password_input = QLineEdit()
        self.password_input.setObjectName("LoginInput")
        self.password_input.setPlaceholderText("🔒 Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        card_layout.addWidget(self.password_input)

        card_layout.addSpacing(10)

        # Login Button
        self.login_btn = QPushButton("LOGIN & CLOCK IN")
        self.login_btn.setObjectName("LoginButton")
        self.login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login_btn.clicked.connect(self.on_login_click)
        card_layout.addWidget(self.login_btn)
        
        # Loader status
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #E74C3C; font-size: 13px;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(self.status_label)

        main_layout.addWidget(card, alignment=Qt.AlignmentFlag.AlignHCenter)

        # Footer Layout (below card)
        footer_container = QWidget()
        footer_container.setFixedWidth(420)
        footer_inner = QHBoxLayout(footer_container)
        footer_inner.setContentsMargins(10, 10, 10, 0)

        # Forgot Password Link
        self.forgot_btn = QPushButton("Forgot Password?")
        self.forgot_btn.setObjectName("LinkButton")
        self.forgot_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.forgot_btn.clicked.connect(self.on_forgot_password)
        footer_inner.addWidget(self.forgot_btn, alignment=Qt.AlignmentFlag.AlignLeft)
        
        footer_inner.addStretch()

        # System Status
        status_layout = QHBoxLayout()
        status_text = QLabel("System Status: Offline")
        status_text.setObjectName("StatusText")
        
        status_dot = QLabel()
        status_dot.setFixedSize(8, 8)
        status_dot.setStyleSheet("background-color: #E74C3C; border-radius: 4px;") # Red dot
        
        status_layout.addWidget(status_text)
        status_layout.addWidget(status_dot)
        status_layout.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        footer_inner.addLayout(status_layout)
        main_layout.addWidget(footer_container, alignment=Qt.AlignmentFlag.AlignHCenter)

    def on_login_click(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()
        if not username or not password:
            self.show_error("Please enter both username and password.")
            return

        self.login_btn.setEnabled(False)
        self.login_btn.setText("Authenticating...")
        self.login_attempted.emit(username, password)

    def reset_state(self):
        self.login_btn.setEnabled(True)
        self.login_btn.setText("LOGIN & CLOCK IN")
        self.password_input.clear()
        
    def show_error(self, message):
        self.status_label.setText(message)
        self.reset_state()

    def on_forgot_password(self):
        # We spawn the dialog and pass it a fresh APIClient so it can hit endpoints regardless of logged in state
        dialog = ForgotPasswordDialog(APIClient(), self)
        dialog.exec()
