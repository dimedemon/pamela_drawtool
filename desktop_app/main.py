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
        
        self.plot_controls_widget = create_
