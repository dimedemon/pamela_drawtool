"""
Главное приложение (Фаза 2)

Это главный запускаемый файл для десктопного GUI.
Он создает окно, Ядро (ApplicationState) и Коннектор (QtConnector).
"""

import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, 
                             QHBoxLayout, QLabel, QVBoxLayout)

# Импортируем наши компоненты Ядра и Клея
from core.state import ApplicationState
from desktop_app.qt_connector import QtConnector

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        print("Инициализация Главного Окна...")
        
        # 1. Инициализируем Ядро (Модель Состояния)
        # app_state будет жить в памяти все время работы программы
        self.app_state = ApplicationState()
        
        # 2. Инициализируем "Клей"
        # Передаем ядро в коннектор, чтобы он мог на него подписаться
        self.connector = QtConnector(self.app_state)

        # 3. Настраиваем GUI
        self.setWindowTitle(f"PAMELA DrawTool (Python/PyQt) - Фаза 2")
        self.setGeometry(100, 100, 1200, 800) # x, y, width, height
        
        # --- Создаем главный макет ---
        # Горизонтальный макет: [Панель управления] | [Область графиков]
        main_layout = QHBoxLayout()
        
        # --- Левая Панель (Управление) ---
        # (Сюда мы будем добавлять наши pan*.m, портированные в PyQt)
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        left_panel.setLayout(left_layout)
        
        # TODO: Заменить этот placeholder на реальные виджеты
        left_layout.addWidget(QLabel("--- (ЛЕВАЯ ПАНЕЛЬ) ---"))
        left_layout.addWidget(QLabel("Здесь будут pan00, pan01, pan02..."))
        left_layout.addStretch() # "Прибивает" все виджеты к верху
        
        
        # --- Правая Панель (Графики) ---
        # (Сюда мы встроим Matplotlib)
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        right_panel.setLayout(right_layout)
        
        # TODO: Заменить этот placeholder на холст Matplotlib
        right_layout.addWidget(QLabel("--- (ПРАВАЯ ПАНЕЛЬ) ---"))
        right_layout.addWidget(QLabel("Здесь будут графики (ax1, ax2, ax3, ax4)"))
        
        # --- Собираем макет ---
        main_layout.addWidget(left_panel, 1) # 1 = доля ширины (узкая)
        main_layout.addWidget(right_panel, 3) # 3 = доля ширины (широкая)
        
        # Устанавливаем центральный виджет
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        
        print("Главное Окно успешно создано.")


if __name__ == "__main__":
    # Убедимся, что зависимости Qt установлены
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
