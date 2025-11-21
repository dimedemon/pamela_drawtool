"""
Главное приложение (Фаза 4) - Интеграция Matplotlib + View Controls
"""

import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, 
                             QHBoxLayout, QVBoxLayout, QLabel,
                             QPushButton, QButtonGroup) 
from PyQt5.QtCore import Qt 

# Добавляем путь к корню проекта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.state import ApplicationState
from core import processing 
from desktop_app.qt_connector import QtConnector

# --- Импорты виджетов ---
from desktop_app.ui_panels.input_data_source import create_input_data_source_widget
from desktop_app.ui_panels.selections import create_selections_widget
from desktop_app.ui_panels.versions import create_versions_widget
from desktop_app.ui_panels.binnings import create_binnings_widget 
from desktop_app.ui_panels.periods import create_periods_widget
from desktop_app.ui_panels.plot_controls import create_plot_controls_widget 
from desktop_app.ui_panels.geomagnetic_params import create_geomag_params_widget
from desktop_app.ui_panels.plot_button import create_plot_button_widget 
from desktop_app.matplotlib_widget import MplCanvas

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        print("Инициализация Главного Окна...")
        
        self.app_state = ApplicationState()
        self.connector = QtConnector(self.app_state)

        self.setWindowTitle(f"PAMELA DrawTool (Python/PyQt) - Фаза 4")
        self.setGeometry(100, 100, 1200, 800)
        
        main_layout = QHBoxLayout()
        
        # --- Левая Панель (Управление) ---
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        left_panel.setLayout(left_layout)
        
        self.input_data_source_widget = create_input_data_source_widget(self.app_state, self.connector)
        left_layout.addWidget(self.input_data_source_widget)
        
        self.versions_widget = create_versions_widget(self.app_state, self.connector, self)
        left_layout.addWidget(self.versions_widget)
        
        self.selections_widget = create_selections_widget(self.app_state, self.connector)
        left_layout.addWidget(self.selections_widget)
        
        self.binnings_widget = create_binnings_widget(self.app_state, self.connector)
        left_layout.addWidget(self.binnings_widget)
        
        self.periods_widget = create_periods_widget(self.app_state, self.connector, self)
        left_layout.addWidget(self.periods_widget)
        
        self.plot_controls_widget = create_plot_controls_widget(self.app_state, self.connector, self)
        left_layout.addWidget(self.plot_controls_widget)

        self.geomag_params_widget = create_geomag_params_widget(self.app_state, self.connector, self)
        left_layout.addWidget(self.geomag_params_widget)
        
        left_layout.addStretch()
        
        self.plot_button_widget = create_plot_button_widget() 
        left_layout.addWidget(self.plot_button_widget)
        
        
        # --- Правая Панель (Графики) ---
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        right_panel.setLayout(right_layout)
        
        # Панель управления видом (View Controls)
        view_controls_layout = QHBoxLayout()
        view_controls_layout.addWidget(QLabel("View Mode:"))
        
        btn_view_1 = QPushButton("Single (1x1)")
        btn_view_4 = QPushButton("Grid (2x2)")
        
        btn_view_1.setCheckable(True)
        btn_view_4.setCheckable(True)
        btn_view_1.setChecked(True)
        
        self.view_group = QButtonGroup(self)
        self.view_group.addButton(btn_view_1, 1)
        self.view_group.addButton(btn_view_4, 4)
        
        view_controls_layout.addWidget(btn_view_1)
        view_controls_layout.addWidget(btn_view_4)
        view_controls_layout.addStretch()
        
        right_layout.addLayout(view_controls_layout)

        # Холст Matplotlib
        self.plot_canvas = MplCanvas(self) 
        right_layout.addWidget(self.plot_canvas)
        
        
        # --- Собираем макет ---
        main_layout.addWidget(left_panel, 1) 
        main_layout.addWidget(right_panel, 3) 
        
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        
        # --- Подключаем логику ---
        # Кнопка PLOT
        self.plot_button_widget.plot_button.clicked.connect(self.on_plot_button_clicked)
        # Переключатель видов
        self.view_group.buttonClicked[int].connect(self.on_view_changed)
        
        print("Главное Окно успешно создано и готово к работе.")

    # --- ВОТ ЭТОТ МЕТОД БЫЛ ПРОПУЩЕН ---
    def on_view_changed(self, mode_id):
        """Переключает режим отображения графиков (1 или 4)."""
        print(f"Переключение режима просмотра на: {mode_id} график(ов)")
        self.plot_canvas.set_layout_mode(mode_id)

    def on_plot_button_clicked(self):
        """
        Главный триггер! Вызывается при нажатии на "PLOT DATA".
        """
        print("\n===================================")
        print("Кнопка PLOT нажата!")
        print("Собираем данные из app_state...")
        
        try:
            # 1. Очищаем старые графики (но сохраняем лейаут 1x1 или 2x2)
            self.plot_canvas.clear_all_axes()
            
            # 2. Вызываем наш научный бэкенд
            plot_data_list = processing.get_plot_data(self.app_state, ax_index=0)
            
            # 3. Рисуем результат
            if not plot_data_list:
                print(">>> processing.py вернул ПУСТОЙ список.")
                # Если список пуст (например, файл не найден), пишем это на первом графике
                # Используем 'ax_index=0' по умолчанию или текущий активный
                # Важно: MplCanvas всегда имеет список axes_list
                if self.plot_canvas.axes_list:
                    ax = self.plot_canvas.axes_list[0]
                    ax.text(0.5, 0.5, 
                            "Данные не сгенерированы.\n(processing.py вернул пустой список)", 
                            ha='center', va='center', 
                            transform=ax.transAxes)
                    self.plot_canvas.canvas.draw()
            else:
                print(f">>> processing.py успешно вернул {len(plot_data_list)} набор(а) данных.")
                # Рисуем каждый набор данных
                for plot_data in plot_data_list:
                    self.plot_canvas.draw_plot(plot_data)
        
        except Exception as e:
            print(f"!!! КРИТИЧЕСКАЯ ОШИБКА в core/processing.py: {e}")
            # Рисуем ошибку на первом графике
            if self.plot_canvas.axes_list:
                ax = self.plot_canvas.axes_list[0]
                ax.text(0.5, 0.5, f"ОШИБКА:\n{e}", 
                        ha='center', va='center', color='red',
                        transform=ax.transAxes)
                self.plot_canvas.canvas.draw()
            
        print("===================================\n")


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
