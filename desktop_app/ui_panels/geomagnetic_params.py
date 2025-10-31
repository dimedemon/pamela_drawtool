"""
Порт pan04_GeomagneticParams.m (ИСПРАВЛЕННЫЙ)
и pan04_set01_L.m, pan04_set02_pitch.m,
pan04_set03_E.m, pan04_set04_R.m

Исправлена логика конвертации E/R. 'app_state' всегда хранит GeV/GV.
"""
import numpy as np
from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QGroupBox, QVBoxLayout, QComboBox)
from PyQt5.QtCore import QSignalBlocker, Qt
from core import kinematics # Импорт кинематики
from core.state import ApplicationState
from desktop_app.qt_connector import QtConnector
from desktop_app.dialogs.l_bin_dialog import LBinDialog
from desktop_app.dialogs.pitch_bin_dialog import PitchBinDialog 
from desktop_app.dialogs.e_bin_dialog import EBinDialog

def _list_to_str(val_list, fmt=".3f"):
    """Вспомогательная функция: конвертирует [1.1, 1.2] в "1.100, 1.200" """
    if not val_list:
        return ""
    if val_list == [-1]:
        return "All"
    return ", ".join(f"{val:{fmt}}" for val in val_list)

def create_geomag_params_widget(app_state: ApplicationState, connector: QtConnector, parent_window):
    """
    Создает QGroupBox "Input parameters: Geomagnetic".
    """
    # 1. Создаем главный контейнер (pan04)
    widget = QGroupBox("Input parameters: Geomagnetic")
    main_layout = QVBoxLayout()
    widget.setLayout(main_layout)
    main_layout.setContentsMargins(5, 10, 5, 5)

    # --- Верхний макет (заголовки) ---
    header_layout = QHBoxLayout()
    header_layout.addWidget(QLabel(""), 1) # Пустое место
    header_layout.addWidget(QLabel("min value"), 4) # min
    header_layout.addWidget(QLabel("units / ..."), 2) # units/btn
    header_layout.addWidget(QLabel("max value"), 2) # max
    header_layout.addWidget(QLabel("Δ"), 1) # delta
    main_layout.addLayout(header_layout)

    # --- Макет 1: L-Shell (pan04_set01_L) ---
    l_layout = QH
