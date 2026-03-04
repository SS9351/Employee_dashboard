# QSS StyleSheet for professional Sahastra Finnovations UI

MAIN_STYLE = """
/* Global Config */
QWidget {
    font-family: 'Segoe UI', Arial, sans-serif;
    background-color: #F4F7FB;
    color: #2C3E50;
    font-size: 14px;
}

/* Titles & Headers */
QLabel#MainTitle {
    font-size: 28px;
    font-weight: bold;
    color: #0F3460;
}

QLabel#Subtitle {
    font-size: 16px;
    color: #16A085;
    margin-bottom: 20px;
}

/* Inputs */
QLineEdit {
    background-color: #FFFFFF;
    border: 1px solid #BDC3C7;
    border-radius: 6px;
    padding: 10px;
    color: #34495E;
    font-size: 14px;
}
QLineEdit:focus {
    border: 1px solid #16A085;
    background-color: #FFFFFF;
}

/* Buttons */
QPushButton#PrimaryButton {
    background-color: #0F3460;
    color: #FFFFFF;
    border-radius: 6px;
    padding: 12px;
    font-weight: bold;
    font-size: 14px;
}
QPushButton#PrimaryButton:hover {
    background-color: #16A085;
}
QPushButton#PrimaryButton:pressed {
    background-color: #0B2545;
}

QPushButton#DangerButton {
    background-color: #E74C3C;
    color: #FFFFFF;
    border-radius: 6px;
    padding: 12px;
    font-weight: bold;
}
QPushButton#DangerButton:hover {
    background-color: #C0392B;
}

/* Cards / Panels */
QFrame#Card {
    background-color: #FFFFFF;
    border-radius: 10px;
    border: 1px solid #E0E6ED;
}

/* Tabs */
QTabWidget::pane {
    border: 1px solid #E0E6ED;
    background: #FFFFFF;
    border-radius: 6px;
}

QTabBar::tab {
    background: #E0E6ED;
    color: #34495E;
    padding: 10px 20px;
    margin-right: 2px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    font-weight: bold;
}

QTabBar::tab:selected {
    background: #FFFFFF;
    color: #0F3460;
    border-bottom: 2px solid #16A085;
}

/* Dropdown */
QComboBox {
    background-color: #FFFFFF;
    border: 1px solid #BDC3C7;
    border-radius: 6px;
    padding: 5px;
    color: #34495E;
}
QComboBox::drop-down {
    border: none;
}

/* Login Specific */
QWidget#LoginBackground {
    background-color: #0B192C;
}

QFrame#LoginCard {
    background-color: #EBEFF3;
    border-radius: 15px;
}

QLabel#LogoCircle {
    background: transparent;
}


QLabel#LoginTitle {
    font-size: 26px;
    font-weight: bold;
    color: #2C3E50;
    margin-top: 10px;
    background: transparent;
}

QLabel#LoginSubtitle {
    font-size: 13px;
    color: #7F8C8D;
    background: transparent;
}

QLineEdit#LoginInput {
    background-color: #FFFFFF;
    border: 1px solid #D0D7DE;
    border-radius: 8px;
    padding: 12px 15px;
    color: #34495E;
    font-size: 14px;
}
QLineEdit#LoginInput:focus {
    border: 1px solid #4A6B9C;
}

QPushButton#LoginButton {
    background-color: #4A6B9C;
    color: #FFFFFF;
    border-radius: 20px;
    padding: 14px;
    font-weight: bold;
    font-size: 14px;
}
QPushButton#LoginButton:hover {
    background-color: #3A557C;
}
QPushButton#LoginButton:pressed {
    background-color: #2C4263;
}

QPushButton#LinkButton {
    background: transparent;
    color: #85A5CC;
    font-size: 12px;
    text-decoration: underline;
    border: none;
}
QPushButton#LinkButton:hover {
    color: #A0C0E8;
}

QLabel#StatusText {
    color: #85A5CC;
    font-size: 12px;
}
"""
