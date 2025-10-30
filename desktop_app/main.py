"""
Главное приложение (Фаза 2) - ОБНОВЛЕНО
"""

import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, 
    QHBoxLayout, QVBoxLayout, QLabel
)

# Импортируем наши компоненты
# (Это будет работать при запуске через "python -m desktop_app.main")
from core.state import ApplicationState
from desktop_app.qt_connector import QtConnector
from desktop_app.ui_panels.input_data_source import create_input_data_source_widget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        print("Инициализация Главного Окна...")
        
        # 1. Инициализируем Ядро
        self.app_state = ApplicationState()
        
        # 2. Инициализируем "Клей"
        self.connector = QtConnector(self.app_state)

        # 3. Настраиваем GUI
        self.setWindowTitle(f"PAMELA DrawTool (Python/PyQt) - Фаза 2")
        self.setGeometry(100, 100, 1200, 800)
        
        main_layout = QHBoxLayout()
        
        # --- Левая Панель (Управление) ---
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        left_panel.setLayout(left_layout)
        
        # --- ЗАМЕНЯЕМ PLACEHOLDER'ы ---
        # left_layout.addWidget(QLabel("--- (ЛЕВАЯ ПАНЕЛЬ) ---"))
        # left_layout.addWidget(QLabel("Здесь будут pan00, pan01, pan02..."))
        
        # Добавляем наш первый портированный виджет!
        # Он создается и сразу подключается к app_state и connector
        self.input_data_source_widget = create_input_data_source_widget(
            self.app_state, self.connector
        )
        left_layout.addWidget(self.input_data_source_widget)
        
        left_layout.addStretch() # "Прибивает" все виджеты к верху
        
        
        # --- Правая Панель (Графики) ---
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        right_panel.setLayout(right_layout)
        
        # TODO: Заменить этот placeholder на холст Matplotlib
        right_layout.addWidget(QLabel("--- (ПРАВАЯ ПАНЕЛЬ) ---"))
        right_layout.addWidget(QLabel("Здесь будут графики (ax1, ax2, ax3, ax4)"))
        
        # --- Собираем макет ---
        main_layout.addWidget(left_panel, 1) 
        main_layout.addWidget(right_panel, 3) 
        
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        
        print("Главное Окно успешно создано.")

# --- (остальная часть __main__ остается без изменений) ---
if __name__ == "__main__":
    try:
        from PyQt5.QtCore import Qt
    except ImportError:
        print("Ошибка: PyQt5 не найден.")
        print("Пожалуйста, установите его: pip install PyQt5")
        sys.exit(1)

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
