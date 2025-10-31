"""
Порт pan04_GeomagneticParams.m (ОБНОВЛЕННЫЙ)
и pan04_set01_L.m, pan04_set02_pitch.m,
pan04_set03_E.m, pan04_set04_R.m
"""
import numpy as np
from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QGroupBox, QVBoxLayout, QComboBox)
from PyQt5.QtCore import QSignalBlocker, Qt
from core import kinematics # <--- ИМПОРТ КИНЕМАТИКИ
from core.state import ApplicationState
from desktop_app.qt_connector import QtConnector
from desktop_app.dialogs.l_bin_dialog import LBinDialog
from desktop_app.dialogs.pitch_bin_dialog import PitchBinDialog 
from desktop_app.dialogs.e_bin_dialog import EBinDialog # <--- НОВЫЙ ИМПОРТ

def _list_to_str(val_list, fmt=".3f"):
    """Вспомогательная функция: конвертирует [1.1, 1.2] в "1.100, 1.200" """
    if not val_list:
        return ""
    if val_list == [-1]:
        return "All"
    # f-string formatting
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
    l_layout = QHBoxLayout()
    edit_l_min = QLineEdit()
    button_show_l = QPushButton("...")
    button_show_l.setFixedWidth(30)
    edit_l_max = QLineEdit()
    edit_delta_l = QLineEdit()
    
    l_layout.addWidget(QLabel("L:"), 1)
    l_layout.addWidget(edit_l_min, 4)
    l_layout.addWidget(button_show_l, 2) # Кнопка занимает место "units"
    l_layout.addWidget(edit_l_max, 2)
    l_layout.addWidget(edit_delta_l, 1)
    main_layout.addLayout(l_layout)

    # --- Макет 2: Pitch (pan04_set02_pitch) ---
    pitch_layout = QHBoxLayout()
    edit_pitch_min = QLineEdit()
    button_show_pitch = QPushButton("...")
    button_show_pitch.setFixedWidth(30)
    edit_pitch_max = QLineEdit()
    edit_delta_alpha = QLineEdit()

    pitch_layout.addWidget(QLabel("α:"), 1)
    pitch_layout.addWidget(edit_pitch_min, 4)
    pitch_layout.addWidget(button_show_pitch, 2) # Кнопка занимает место "units"
    pitch_layout.addWidget(edit_pitch_max, 2)
    pitch_layout.addWidget(edit_delta_alpha, 1)
    main_layout.addLayout(pitch_layout)
    
    # --- Макет 3: Energy (pan04_set03_E) ---
    e_layout = QHBoxLayout()
    edit_e_min = QLineEdit()
    combo_e_units = QComboBox()
    combo_e_units.addItems(['MeV', 'GeV'])
    combo_e_units.setCurrentIndex(1) # GeV по умолчанию
    button_show_e = QPushButton("...")
    button_show_e.setFixedWidth(30)
    edit_e_max = QLineEdit()
    edit_delta_e = QLineEdit()
    
    # Собираем E units + button в один sub-layout
    e_units_layout = QHBoxLayout()
    e_units_layout.setContentsMargins(0,0,0,0)
    e_units_layout.addWidget(combo_e_units)
    e_units_layout.addWidget(button_show_e)
    
    e_layout.addWidget(QLabel("E:"), 1)
    e_layout.addWidget(edit_e_min, 4)
    e_layout.addLayout(e_units_layout, 2) # Добавляем sub-layout
    e_layout.addWidget(edit_e_max, 2)
    e_layout.addWidget(edit_delta_e, 1)
    main_layout.addLayout(e_layout)

    # --- Макет 4: Rigidity (pan04_set04_R) ---
    r_layout = QHBoxLayout()
    edit_r_min = QLineEdit()
    combo_r_units = QComboBox()
    combo_r_units.addItems(['MV', 'GV'])
    combo_r_units.setCurrentIndex(1) # GV по умолчанию
    edit_r_max = QLineEdit()
    
    r_layout.addWidget(QLabel("R:"), 1)
    r_layout.addWidget(edit_r_min, 4)
    r_layout.addWidget(combo_r_units, 2) # Просто QComboBox
    r_layout.addWidget(edit_r_max, 2)
    r_layout.addWidget(QLabel(""), 1) # Пустая заглушка для Δ
    main_layout.addLayout(r_layout)

    # -----------------------------------------------------------------
    # 3. Связывание (Binding)
    # -----------------------------------------------------------------

    # --- L-Shell (без изменений) ---
    def on_l_min_changed():
        txt = edit_l_min.text()
        if txt.lower() == 'all': app_state.l = [-1]
        else:
            try:
                app_state.l = [float(val.strip()) for val in txt.split(',') if val.strip()]
            except ValueError: on_core_l_changed(app_state.l)
    def on_l_max_changed():
        try: app_state.l_max = float(edit_l_max.text())
        except ValueError: on_core_l_max_changed(app_state.l_max)
    edit_l_min.editingFinished.connect(on_l_min_changed)
    edit_l_max.editingFinished.connect(on_l_max_changed)
    def on_core_l_changed(new_l_list):
        with QSignalBlocker(edit_l_min): edit_l_min.setText(_list_to_str(new_l_list, ".3f"))
    def on_core_l_max_changed(new_l_max):
        with QSignalBlocker(edit_l_max): edit_l_max.setText(f"{new_l_max:.3f}")
    connector.l_changed.connect(on_core_l_changed)
    connector.l_max_changed.connect(on_core_l_max_changed)
    def on_show_l_bin():
        dialog = LBinDialog(app_state, parent_window); dialog.exec_()
    button_show_l.clicked.connect(on_show_l_bin)

    # --- Pitch (без изменений) ---
    def on_pitch_min_changed():
        txt = edit_pitch_min.text()
        if txt.lower() == 'all': app_state.pitch = [-1]
        else:
            try: app_state.pitch = [float(val.strip()) for val in txt.split(',') if val.strip()]
            except ValueError: on_core_pitch_changed(app_state.pitch)
    def on_pitch_max_changed():
        txt = edit_pitch_max.text()
        try: app_state.pitch_max = [float(val.strip()) for val in txt.split(',') if val.strip()]
        except ValueError: on_core_pitch_max_changed(app_state.pitch_max)
    def on_d_alpha_changed():
        try: app_state.d_alpha = float(edit_delta_alpha.text())
        except ValueError: on_core_d_alpha_changed(app_state.d_alpha)
    edit_pitch_min.editingFinished.connect(on_pitch_min_changed)
    edit_pitch_max.editingFinished.connect(on_pitch_max_changed)
    edit_delta_alpha.editingFinished.connect(on_d_alpha_changed)
    def on_core_pitch_changed(new_pitch_list):
        with QSignalBlocker(edit_pitch_min): edit_pitch_min.setText(_list_to_str(new_pitch_list, ".1f"))
    def on_core_pitch_max_changed(new_pitch_max_list):
        with QSignalBlocker(edit_pitch_max): edit_pitch_max.setText(_list_to_str(new_pitch_max_list, ".1f"))
    def on_core_d_alpha_changed(new_d_alpha):
        with QSignalBlocker(edit_delta_alpha): edit_delta_alpha.setText(f"{new_d_alpha:.1f}")
    connector.pitch_changed.connect(on_core_pitch_changed)
    connector.pitch_max_changed.connect(on_core_pitch_max_changed)
    connector.d_alpha_changed.connect(on_core_d_alpha_changed)
    def on_show_pitch_bin():
        dialog = PitchBinDialog(app_state, parent_window); dialog.exec_()
    button_show_pitch.clicked.connect(on_show_pitch_bin)
    
    # --- E / R (НОВАЯ ЛОГИКА) ---
    
    # --- Связь: E -> R (Логика ConvertT2R) ---
    def on_e_changed_by_user():
        txt = edit_e_min.text()
        if txt.lower() == 'all':
            app_state.update_multiple(e=[-1], rig=[-1], is_e=True)
            return
        try:
            e_values = [float(val.strip()) for val in txt.split(',') if val.strip()]
            # Конвертируем E -> R
            # TODO: Уточнить M, A, Z (пока M=протон, A=1, Z=1)
            M, A, Z = 0.938, 1.0, 1.0
            e_values_gev = np.array(e_values) / (1000.0 if combo_e_units.currentIndex() == 0 else 1.0)
            rig_values = kinematics.convert_T_to_R(e_values_gev, M, A, Z)
            
            app_state.update_multiple(e=e_values, rig=list(rig_values), is_e=True)
            
        except ValueError: on_core_e_changed(app_state.e) # Сброс

    # --- Связь: R -> E (Логика ConvertR2T) ---
    def on_rig_changed_by_user():
        txt = edit_r_min.text()
        if txt.lower() == 'all':
            app_state.update_multiple(e=[-1], rig=[-1], is_e=False)
            return
        try:
            rig_values = [float(val.strip()) for val in txt.split(',') if val.strip()]
            # Конвертируем R -> E
            M, A, Z = 0.938, 1.0, 1.0
            rig_values_gv = np.array(rig_values) / (1000.0 if combo_r_units.currentIndex() == 0 else 1.0)
            e_values_gev = kinematics.convert_R_to_T(rig_values_gv, M, A, Z)
            
            # Конвертируем обратно в GeV или MeV для E поля
            e_values = e_values_gev * (1000.0 if combo_e_units.currentIndex() == 0 else 1.0)
            
            app_state.update_multiple(e=list(e_values), rig=rig_values, is_e=False)
            
        except ValueError: on_core_rig_changed(app_state.rig) # Сброс

    edit_e_min.editingFinished.connect(on_e_changed_by_user)
    edit_r_min.editingFinished.connect(on_rig_changed_by_user)
    
    # --- Связь: Ядро -> GUI (E/R) ---
    def on_core_e_changed(new_e_list):
        with QSignalBlocker(edit_e_min): 
            edit_e_min.setText(_list_to_str(new_e_list, ".3f"))
    def on_core_e_max_changed(new_e_max_list):
        with QSignalBlocker(edit_e_max): 
            edit_e_max.setText(_list_to_str(new_e_max_list, ".3f"))
    def on_core_rig_changed(new_rig_list):
        with QSignalBlocker(edit_r_min): 
            edit_r_min.setText(_list_to_str(new_rig_list, ".3f"))
    def on_core_rig_max_changed(new_rig_max_list):
        with QSignalBlocker(edit_r_max): 
            edit_r_max.setText(_list_to_str(new_rig_max_list, ".3f"))
            
    connector.e_changed.connect(on_core_e_changed)
    connector.e_max_changed.connect(on_core_e_max_changed)
    connector.rig_changed.connect(on_core_rig_changed)
    connector.rig_max_changed.connect(on_core_rig_max_changed)

    # --- Кнопка "..." (ShowEbin) ---
    def on_show_e_bin():
        dialog = EBinDialog(app_state, parent_window)
        dialog.exec_()
        # app_state уже обновлен (E, E_max, Rig, Rig_max)
            
    button_show_e.clicked.connect(on_show_e_bin)

    # 4. Инициализация
    on_core_l_changed(app_state.l)
    on_core_l_max_changed(app_state.l_max)
    on_core_pitch_changed(app_state.pitch)
    on_core_pitch_max_changed(app_state.pitch_max)
    on_core_d_alpha_changed(app_state.d_alpha)
    # --- НОВАЯ ИНИЦИАЛИЗАЦИЯ (E/R) ---
    on_core_e_changed(app_state.e)
    on_core_e_max_changed(app_state.e_max)
    on_core_rig_changed(app_state.rig)
    on_core_rig_max_changed(app_state.rig_max)
    
    return widget
