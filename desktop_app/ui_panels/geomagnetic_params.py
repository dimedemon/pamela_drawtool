"""
Порт pan04_GeomagneticParams.m (ПОЛНЫЙ + SMART LOGIC)
Реализует логику setGeomagParamEn.m для всех PlotKinds.
"""
import numpy as np
from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QGroupBox, QVBoxLayout, QComboBox)
from PyQt5.QtCore import QSignalBlocker, Qt
from core import kinematics
from core.state import ApplicationState
from desktop_app.qt_connector import QtConnector
from desktop_app.dialogs.l_bin_dialog import LBinDialog
from desktop_app.dialogs.pitch_bin_dialog import PitchBinDialog 
from desktop_app.dialogs.e_bin_dialog import EBinDialog

def _list_to_str(val_list, fmt=".3f"):
    if not val_list: return ""
    if val_list == [-1]: return "All"
    return ", ".join(f"{val:{fmt}}" for val in val_list)

def create_geomag_params_widget(app_state: ApplicationState, connector: QtConnector, parent_window):
    """
    Создает QGroupBox "Input parameters: Geomagnetic".
    """
    widget = QGroupBox("Input parameters: Geomagnetic")
    main_layout = QVBoxLayout()
    widget.setLayout(main_layout)
    main_layout.setContentsMargins(5, 10, 5, 5)

    # --- Заголовки ---
    header_layout = QHBoxLayout()
    header_layout.addWidget(QLabel(""), 1)
    header_layout.addWidget(QLabel("min value"), 4)
    header_layout.addWidget(QLabel("units / ..."), 2)
    header_layout.addWidget(QLabel("max value"), 2)
    header_layout.addWidget(QLabel("Δ"), 1)
    main_layout.addLayout(header_layout)

    # --- Макет 1: L-Shell ---
    l_layout = QHBoxLayout()
    edit_l_min = QLineEdit()
    button_show_l = QPushButton("...")
    button_show_l.setFixedWidth(30)
    edit_l_max = QLineEdit()
    edit_delta_l = QLineEdit()
    l_layout.addWidget(QLabel("L:"), 1); l_layout.addWidget(edit_l_min, 4); l_layout.addWidget(button_show_l, 2)
    l_layout.addWidget(edit_l_max, 2); l_layout.addWidget(edit_delta_l, 1)
    main_layout.addLayout(l_layout)

    # --- Макет 2: Pitch ---
    pitch_layout = QHBoxLayout()
    edit_pitch_min = QLineEdit()
    button_show_pitch = QPushButton("...")
    button_show_pitch.setFixedWidth(30)
    edit_pitch_max = QLineEdit()
    edit_delta_alpha = QLineEdit()
    pitch_layout.addWidget(QLabel("α:"), 1); pitch_layout.addWidget(edit_pitch_min, 4); pitch_layout.addWidget(button_show_pitch, 2)
    pitch_layout.addWidget(edit_pitch_max, 2); pitch_layout.addWidget(edit_delta_alpha, 1)
    main_layout.addLayout(pitch_layout)
    
    # --- Макет 3: Energy ---
    e_layout = QHBoxLayout()
    edit_e_min = QLineEdit()
    combo_e_units = QComboBox(); combo_e_units.addItems(['MeV', 'GeV']); combo_e_units.setCurrentIndex(1)
    button_show_e = QPushButton("..."); button_show_e.setFixedWidth(30)
    edit_e_max = QLineEdit()
    edit_delta_e = QLineEdit()
    e_units_layout = QHBoxLayout(); e_units_layout.setContentsMargins(0,0,0,0)
    e_units_layout.addWidget(combo_e_units); e_units_layout.addWidget(button_show_e)
    e_layout.addWidget(QLabel("E:"), 1); e_layout.addWidget(edit_e_min, 4); e_layout.addLayout(e_units_layout, 2)
    e_layout.addWidget(edit_e_max, 2); e_layout.addWidget(edit_delta_e, 1)
    main_layout.addLayout(e_layout)

    # --- Макет 4: Rigidity ---
    r_layout = QHBoxLayout()
    edit_r_min = QLineEdit()
    combo_r_units = QComboBox(); combo_r_units.addItems(['MV', 'GV']); combo_r_units.setCurrentIndex(1)
    edit_r_max = QLineEdit()
    r_layout.addWidget(QLabel("R:"), 1); r_layout.addWidget(edit_r_min, 4); r_layout.addWidget(combo_r_units, 2)
    r_layout.addWidget(edit_r_max, 2); r_layout.addWidget(QLabel(""), 1)
    main_layout.addLayout(r_layout)

    # --- Макет 5: Time (t:, t_max, dt) ---
    t_layout = QHBoxLayout()
    edit_t_min = QLineEdit("hh:mm:ss")
    edit_t_max = QLineEdit("hh:mm:ss") 
    edit_dt = QLineEdit()
    t_layout.addWidget(QLabel("t:"), 1)
    t_layout.addWidget(edit_t_min, 4)
    t_layout.addWidget(QLabel(""), 2) # Заглушка
    t_layout.addWidget(edit_t_max, 2)
    t_layout.addWidget(edit_dt, 1)
    main_layout.addLayout(t_layout)

    # -----------------------------------------------------------------
    # Логика Блокировки (setGeomagParamEn.m)
    # -----------------------------------------------------------------
    def update_ui_state(plot_kind_val):
        """
        Включает/выключает поля в зависимости от типа графика.
        Логика полностью портирована из setGeomagParamEn.m
        """
        
        # Инициализируем все как выключенное
        l_en = False; pitch_en = False; er_en = False; t_en = False
        
        if plot_kind_val in [1, 2]: # Energy/Rigidity spectra
            # Ось X: E/R. Фиксируем: L, Pitch
            l_en = True; pitch_en = True; er_en = False; t_en = False
            
        elif plot_kind_val == 3: # Pitch-angular distribution
            # Ось X: Pitch. Фиксируем: L, E/R
            l_en = True; pitch_en = False; er_en = True; t_en = False
            
        elif plot_kind_val == 4: # Radial distribution
            # Ось X: L. Фиксируем: Pitch, E/R
            l_en = False; pitch_en = True; er_en = True; t_en = False
            
        elif plot_kind_val in [5, 7]: # Temporal variations / Fluxes Histogram
            # Ось X: Time/Value. Фиксируем: L, Pitch, E/R
            l_en = True; pitch_en = True; er_en = True; t_en = False
            
        elif plot_kind_val == 6: # Variations along orbit
            # Фиксируем всё, плюс время
            l_en = True; pitch_en = True; er_en = True; t_en = True
            
        elif plot_kind_val == 8: # L-pitch map
            # Оси: L, Pitch. Фиксируем: E/R
            l_en = False; pitch_en = False; er_en = True; t_en = False
            
        elif plot_kind_val == 9: # E-pitch map
            # Оси: E, Pitch. Фиксируем: L
            l_en = True; pitch_en = False; er_en = False; t_en = False
            
        elif plot_kind_val == 10: # E-L map
            # Оси: E, L. Фиксируем: Pitch
            l_en = False; pitch_en = True; er_en = False; t_en = False

        elif plot_kind_val == 11: # Auxiliary parameters
            # Нужен только dt
            l_en = False; pitch_en = False; er_en = False; t_en = True

        # Применяем состояние к группам виджетов
        
        # L widgets
        edit_l_min.setEnabled(l_en)
        button_show_l.setEnabled(l_en)
        edit_l_max.setEnabled(l_en)
        edit_delta_l.setEnabled(l_en)
        
        # Pitch widgets
        edit_pitch_min.setEnabled(pitch_en)
        button_show_pitch.setEnabled(pitch_en)
        edit_pitch_max.setEnabled(pitch_en)
        edit_delta_alpha.setEnabled(pitch_en)
        
        # E/R widgets (они всегда включаются/выключаются вместе)
        edit_e_min.setEnabled(er_en)
        combo_e_units.setEnabled(er_en)
        button_show_e.setEnabled(er_en)
        edit_e_max.setEnabled(er_en)
        edit_delta_e.setEnabled(er_en)
        
        edit_r_min.setEnabled(er_en)
        combo_r_units.setEnabled(er_en)
        edit_r_max.setEnabled(er_en)
        
        # Time widgets
        edit_t_min.setEnabled(t_en)
        edit_t_max.setEnabled(t_en)
        edit_dt.setEnabled(t_en)

    # Подписываемся на изменение типа графика
    connector.plot_kind_changed.connect(update_ui_state)

    # -----------------------------------------------------------------
    # Связывание (Binding)
    # -----------------------------------------------------------------
    
    # --- L ---
    def on_l_min_changed():
        txt = edit_l_min.text()
        if txt.lower() == 'all': app_state.l = [-1]
        else:
            try: app_state.l = [float(v) for v in txt.split(',') if v.strip()]
            except ValueError: on_core_l_changed(app_state.l)
    edit_l_min.editingFinished.connect(on_l_min_changed)
    def on_core_l_changed(v): 
        with QSignalBlocker(edit_l_min): edit_l_min.setText(_list_to_str(v))
    connector.l_changed.connect(on_core_l_changed)
    button_show_l.clicked.connect(lambda: LBinDialog(app_state, parent_window).exec_())
    
    # --- Pitch ---
    def on_pitch_min_changed():
        txt = edit_pitch_min.text()
        if txt.lower() == 'all': app_state.pitch = [-1]
        else:
            try: app_state.pitch = [float(val.strip()) for val in txt.split(',') if val.strip()]
            except ValueError: on_core_pitch_changed(app_state.pitch)
    edit_pitch_min.editingFinished.connect(on_pitch_min_changed)
    def on_core_pitch_changed(v): 
        with QSignalBlocker(edit_pitch_min): edit_pitch_min.setText(_list_to_str(v, ".1f"))
    connector.pitch_changed.connect(on_core_pitch_changed)
    button_show_pitch.clicked.connect(lambda: PitchBinDialog(app_state, parent_window).exec_())

    # --- E/R ---
    def on_e_changed_by_user():
        txt = edit_e_min.text()
        if txt.lower() == 'all': 
            app_state.update_multiple(e=[-1], rig=[-1], is_e=True)
            return
        try:
            vals = [float(v) for v in txt.split(',') if v.strip()]
            e_gev = np.array(vals) / (1000.0 if combo_e_units.currentIndex()==0 else 1.0)
            r_gv = kinematics.convert_T_to_R(e_gev, 0.938, 1.0, 1.0)
            app_state.update_multiple(e=list(e_gev), rig=list(r_gv), is_e=True)
        except ValueError: on_core_e_changed(app_state.e)
    edit_e_min.editingFinished.connect(on_e_changed_by_user)
    
    def on_core_e_changed(new_e):
        with QSignalBlocker(edit_e_min):
            if new_e == [-1]: edit_e_min.setText("All")
            else: 
                factor = 1000.0 if combo_e_units.currentIndex()==0 else 1.0
                edit_e_min.setText(_list_to_str(np.array(new_e)*factor, ".3f"))
    connector.e_changed.connect(on_core_e_changed)
    combo_e_units.currentIndexChanged.connect(lambda: on_core_e_changed(app_state.e))
    button_show_e.clicked.connect(lambda: EBinDialog(app_state, parent_window).exec_())

    def on_core_rig_changed(new_r):
        with QSignalBlocker(edit_r_min):
            if new_r == [-1]: edit_r_min.setText("All")
            else:
                factor = 1000.0 if combo_r_units.currentIndex()==0 else 1.0
                edit_r_min.setText(_list_to_str(np.array(new_r)*factor, ".3f"))
    connector.rig_changed.connect(on_core_rig_changed)
    combo_r_units.currentIndexChanged.connect(lambda: on_core_rig_changed(app_state.rig))

    # --- Time (dt) ---
    def on_dt_changed():
        try: app_state.dt = float(edit_dt.text())
        except ValueError: on_core_dt_changed(app_state.dt)
    edit_dt.editingFinished.connect(on_dt_changed)
    
    def on_core_dt_changed(val):
        with QSignalBlocker(edit_dt): edit_dt.setText(str(val))
    connector.dt_changed.connect(on_core_dt_changed)

    # Инициализация UI
    update_ui_state(app_state.plot_kind)
    
    # Инициализация значений
    on_core_l_changed(app_state.l)
    on_core_pitch_changed(app_state.pitch)
    on_core_e_changed(app_state.e)
    on_core_rig_changed(app_state.rig)
    on_core_dt_changed(app_state.dt)
    
    return widget
