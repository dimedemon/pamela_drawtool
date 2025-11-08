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
from desktop_app.ui_panels.selections import create_selections_widget
from desktop_app.ui_panels.versions import create_versions_widget
from desktop_app.ui_panels.binnings import create_binnings_widget
from desktop_app.ui_panels.periods import create_periods_widget
from desktop_app.ui_panels.geomagnetic_params import create_geomag_params_widget
from desktop_app.ui_panels.plot_controls import create_plot_controls_widget 
from desktop_app.ui_panels.geomagnetic_params import create_geomag_params_widget
from desktop_app.ui_panels.plot_button import create_plot_button_widget

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
        
        self.input_data_source_widget = create_input_data_source_widget(
            self.app_state, self.connector
        )
        left_layout.addWidget(self.input_data_source_widget)
        
        self.versions_widget = create_versions_widget(
            self.app_state, self.connector, self
        )
        left_layout.addWidget(self.versions_widget)
        
        self.selections_widget = create_selections_widget(
            self.app_state, self.connector
        )
        left_layout.addWidget(self.selections_widget)
        
        self.binnings_widget = create_binnings_widget(
            self.app_state, self.connector
        )
        left_layout.addWidget(self.binnings_widget)
        
        self.periods_widget = create_periods_widget(
            self.app_state, self.connector, self
        )
        left_layout.addWidget(self.periods_widget)
        
        
        self.plot_controls_widget = create_plot_controls_widget(
            self.app_state, self.connector, self
        )
        left_layout.addWidget(self.plot_controls_widget)

        # (pan04 - Geomagnetic Parameters)
        self.geomag_params_widget = create_geomag_params_widget(
            self.app_state, self.connector, self
        )
        left_layout.addWidget(self.geomag_params_widget)
        
        left_layout.addStretch()

        # 1. Мы получаем WIDGET (контейнер)
        self.plot_button_widget = create_plot_button_widget() 
        # 2. Мы добавляем WIDGET в макет
        left_layout.addWidget(self.plot_button_widget)
        # --- Правая Панель (Графики) ---
        # (Пока заглушка)
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        right_panel.setLayout(right_layout)
        self.plot_placeholder = QLabel("--- (ПРАВАЯ ПАНЕЛЬ) ---\nНажмите 'PLOT DATA', чтобы сгенерировать данные.")
        self.plot_placeholder.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(self.plot_placeholder)
        
        # --- Собираем макет ---
        main_layout.addWidget(left_panel, 1) 
        main_layout.addWidget(right_panel, 3) 
        
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        # Мы подключаемся к кнопке .plot_button *внутри* виджета
        self.plot_button_widget.plot_button.clicked.connect(self.on_plot_button_clicked)
        
        print("Главное Окно успешно создано и готово к работе.")
        
    def on_plot_button_clicked(self):
        """
        Главный триггер! Вызывается при нажатии на "PLOT DATA".
        """
        print("\n===================================")
        print("Кнопка PLOT нажата!")
        print("Собираем данные из app_state...")
        
        try:
            # 1. Вызываем наш научный бэкенд
            # (Пока мы передаем ax_index=0, т.к. у нас одна область)
            plot_data_list = processing.get_plot_data(self.app_state, ax_index=0)
            
            # 2. Отображаем результат (пока в консоли)
            if not plot_data_list:
                print(">>> processing.py вернул ПУСТОЙ список.")
                print("   (Возможно, этот тип графика еще не портирован в core/processing.py)")
                self.plot_placeholder.setText("Данные не сгенерированы.\n(Этот тип графика еще не портирован в processing.py)")
            else:
                print(f">>> processing.py успешно вернул {len(plot_data_list)} набор(а) данных.")
                # (Просто выводим первый)
                print(plot_data_list[0]) 
                self.plot_placeholder.setText(f"Данные успешно сгенерированы!\n\n{plot_data_list[0]['label']}\n...")
        
        except Exception as e:
            print(f"!!! КРИТИЧЕСКАЯ ОШИБКА в core/processing.py: {e}")
            # TODO: Показать эту ошибку в GUI
            self.plot_placeholder.setText(f"ОШИБКА:\n{e}")
            
        print("===================================\n")
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
