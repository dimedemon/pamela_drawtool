"""
Главное приложение (Фаза 4) - SCROLLABLE LEFT PANEL
Исправлена проблема с исчезающей кнопкой PLOT.
"""

import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, 
                             QHBoxLayout, QVBoxLayout, QLabel,
                             QPushButton, QButtonGroup, QScrollArea) # <--- QScrollArea
from PyQt5.QtCore import Qt 

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.state import ApplicationState
from core import processing 
from desktop_app.qt_connector import QtConnector

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
        
        # --- ЛЕВАЯ ПАНЕЛЬ (С ПРОКРУТКОЙ) ---
        
        # 1. Создаем виджет-контейнер для контента левой панели
        left_content_widget = QWidget()
        left_layout = QVBoxLayout()
        left_content_widget.setLayout(left_layout)
        
        # 2. Наполняем контент виджетами
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

        # 3. Создаем ScrollArea и кладем в нее контент
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True) # Важно!
        scroll_area.setWidget(left_content_widget)
        scroll_area.setFixedWidth(350) # Фиксируем ширину левой панели
        
        # --- Правая Панель (Графики) ---
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        right_panel.setLayout(right_layout)
        
        view_controls_layout = QHBoxLayout()
        view_controls_layout.addWidget(QLabel("View Mode:"))
        btn_view_1 = QPushButton("Single (1x1)")
        btn_view_4 = QPushButton("Grid (2x2)")
        btn_view_1.setCheckable(True); btn_view_4.setCheckable(True); btn_view_1.setChecked(True)
        self.view_group = QButtonGroup(self)
        self.view_group.addButton(btn_view_1, 1); self.view_group.addButton(btn_view_4, 4)
        view_controls_layout.addWidget(btn_view_1); view_controls_layout.addWidget(btn_view_4)
        view_controls_layout.addStretch()
        right_layout.addLayout(view_controls_layout)

        self.plot_canvas = MplCanvas(self) 
        right_layout.addWidget(self.plot_canvas)
        
        # --- Собираем макет (Скролл слева, График справа) ---
        main_layout.addWidget(scroll_area, 1) 
        main_layout.addWidget(right_panel, 3) 
        
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        
        # --- Подключаем логику ---
        self.plot_button_widget.plot_button.clicked.connect(self.on_plot_button_clicked)
        self.view_group.buttonClicked[int].connect(self.on_view_changed)
        
        print("Главное Окно успешно создано.")

    def on_view_changed(self, mode_id):
        self.plot_canvas.set_layout_mode(mode_id)

    def on_plot_button_clicked(self):
        # ... (Код этой функции остается без изменений, см. прошлый ответ) ...
        # Для экономии места я его сократил, но вы вставьте полную версию
        print("Кнопка PLOT нажата!")
        try:
            self.plot_canvas.clear_all_axes()
            plot_data_list = processing.get_plot_data(self.app_state, ax_index=0)
            
            if not plot_data_list:
                if self.plot_canvas.axes_list:
                    self.plot_canvas.axes_list
