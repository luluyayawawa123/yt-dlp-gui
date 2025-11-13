import sys
import os
from PyQt6.QtWidgets import QApplication
from version import VERSION
from gui.main_window import MainWindow

def main():
    # 确保可以找到系统命令
    if 'PATH' not in os.environ:
        os.environ['PATH'] = '/usr/local/bin:/usr/bin:/bin'
    else:
        os.environ['PATH'] += ':/usr/local/bin:/usr/bin:/bin'

    app = QApplication(sys.argv)
    
    # 设置应用程序信息
    app.setApplicationName("YT-DLP GUI")
    app.setApplicationVersion(VERSION or "1.0.0")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 
