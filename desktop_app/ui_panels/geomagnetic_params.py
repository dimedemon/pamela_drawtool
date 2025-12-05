"""
Порт pan04_GeomagneticParams.m (ИСПРАВЛЕННЫЙ MAX)
Реализует логику setGeomagParamEn.m и правильное отображение списков.
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
    """Конвертирует список чисел в строку через запятую."""
    if val_list is None: return ""
    if isinstance(val_list, (int, float)): return f"{val_list:{fmt}}" # Если вдруг пришло число
    if not isinstance(val_list, (list, tuple, np.ndarray)): return str(val_list)
    if len(val_list) == 0: return ""
    if len(val_list) == 1 and val_list[0] == -1: return "All"
    return ", ".join(f"{val:{fmt}}" for val in val_list)

def create_geomag_params_widget(app_state: ApplicationState, connector: QtConnector, parent_window):
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

    # --- Макеты ---
    l_layout = QHBoxLayout()
    edit_l_min = QLineEdit(); button_show_l = QPushButton("..."); button_show_l.setFixedWidth(30)
    edit_l_max = QLineEdit(); edit_delta_l = QLineEdit()
    l_layout.addWidget(QLabel("L:"), 1); l_layout.addWidget(edit_l_min, 4); l_layout.addWidget(button_show_l, 2)
    l_layout.addWidget(edit_l_max, 2); l_layout.addWidget(edit_delta_l, 1)
    main_layout.addLayout(l_layout)

    pitch_layout = QHBoxLayout()
    edit_pitch_min = QLineEdit(); button_show_pitch = QPushButton("..."); button_show_pitch.setFixedWidth(30)
    edit_pitch_max = QLineEdit(); edit_delta_alpha = QLineEdit()
    pitch_layout.addWidget(QLabel("α:"), 1); pitch_layout.addWidget(edit_pitch_min, 4); pitch_layout.addWidget(button_show_pitch, 2)
    pitch_layout.addWidget(edit_pitch_max, 2); pitch_layout.addWidget(edit_delta_alpha, 1)
    main_layout.addLayout(pitch_layout)
    
    e_layout = QHBoxLayout()
    edit_e_min = QLineEdit(); combo_e_units = QComboBox(); combo_e_units.addItems(['MeV', 'GeV']); combo_e_units.setCurrentIndex(1)
    button_show_e = QPushButton("..."); button_show_e.setFixedWidth(30)
    edit_e_max = QLineEdit(); edit_delta_e = QLineEdit()
    e_units_layout = QHBoxLayout(); e_units_layout.setContentsMargins(0,0,0,0)
    e_units_layout.addWidget(combo_e_units); e_units_layout.addWidget(button_show_e)
    e_layout.addWidget(QLabel("E:"), 1); e_layout.addWidget(edit_e_min, 4); e_layout.addLayout(e_units_layout, 2)
    e_layout.addWidget(edit_e_max, 2); e_layout.addWidget(edit_delta_e, 1)
    main_layout.addLayout(e_layout)

    r_layout = QHBoxLayout()
    edit_r_min = QLineEdit(); combo_r_units = QComboBox(); combo_r_units.addItems(['MV', 'GV']); combo_r_units.setCurrentIndex(1)
    edit_r_max = QLineEdit()
    r_layout.addWidget(QLabel("R:"), 1); r_layout.addWidget(edit_r_min, 4); r_layout.addWidget(combo_r_units, 2)
    r_layout.addWidget(edit_r_max, 2); r_layout.addWidget(QLabel(""), 1)
    main_layout.addLayout(r_layout)

    t_layout = QHBoxLayout()
    edit_t_min = QLineEdit("hh:mm:ss"); edit_t_max = QLineEdit("hh:mm:ss"); edit_dt = QLineEdit()
    t_layout.addWidget(QLabel("t:"), 1); t_layout.addWidget(edit_t_min, 4); t_layout.addWidget(QLabel(""), 2)
    t_layout.addWidget(edit_t_max, 2); t_layout.addWidget(edit_dt, 1)
    main_layout.addLayout(t_layout)

    # --- Логика Блокировки ---
    def update_ui_state(plot_kind_val):
        l_en = False; pitch_en = False; er_en = False; t_en = False
        
        if plot_kind_val in [1, 2]: er_en = False; l_en = True; pitch_en = True
        elif plot_kind_val == 3: pitch_en = False; l_en = True; er_en = True
        elif plot_kind_val == 4: l_en = False; pitch_en = True; er_en = True
        elif plot_kind_val in [5, 7]: l_en = True; pitch_en = True; er_en = True
        elif plot_kind_val == 6: l_en = True; pitch_en = True; er_en = True; t_en = True
        elif plot_kind_val == 8: er_en = True
        elif plot_kind_val == 9: l_en = True
        elif plot_kind_val == 10: pitch_en = True
        elif plot_kind_val == 11: t_en = True

        for w in [edit_l_min, button_show_l, edit_l_max, edit_delta_l]: w.setEnabled(l_en)
        for w in [edit_pitch_min, button_show_pitch, edit_pitch_max, edit_delta_alpha]: w.setEnabled(pitch_en)
        for w in [edit_e_min, combo_e_units, button_show_e, edit_e_max, edit_delta_e, edit_r_min, combo_r_units, edit_r_max]: w.setEnabled(er_en)
        for w in [edit_t_min, edit_t_max, edit_dt]: w.setEnabled(t_en)

    connector.plot_kind_changed.connect(update_ui_state)

    # --- Binding L ---
    def on_l_min_changed():
        txt = edit_l_min.text()
        try: app_state.l = [float(v) for v in txt.split(',') if v.strip()]
        except: on_core_l_changed(app_state.l)
    edit_l_min.editingFinished.connect(on_l_min_changed)
    
    def on_core_l_changed(v): 
        with QSignalBlocker(edit_l_min): edit_l_min.setText(_list_to_str(v, ".3f"))
    connector.l_changed.connect(on_core_l_changed)

    # --- FIX: L MAX (Теперь используем _list_to_str) ---
    def on_core_l_max_changed(v):
        with QSignalBlocker(edit_l_max): edit_l_max.setText(_list_to_str(v, ".3f"))
    connector.l_max_changed.connect(on_core_l_max_changed)
    
    button_show_l.clicked.connect(lambda: LBinDialog(app_state, parent_window).exec_())
    
    # --- Binding Pitch ---
    def on_pitch_min_changed():
        try: app_state.pitch = [float(v) for v in edit_pitch_min.text().split(',') if v.strip()]
        except: on_core_pitch_changed(app_state.pitch)
    edit_pitch_min.editingFinished.connect(on_pitch_min_changed)
    
    def on_core_pitch_changed(v): 
        with QSignalBlocker(edit_pitch_min): edit_pitch_min.setText(_list_to_str(v, ".1f"))
    connector.pitch_changed.connect(on_core_pitch_changed)

    # --- FIX: PITCH MAX ---
    def on_core_pitch_max_changed(v):
        with QSignalBlocker(edit_pitch_max): edit_pitch_max.setText(_list_to_str(v, ".1f"))
    connector.pitch_max_changed.connect(on_core_pitch_max_changed)
    
    button_show_pitch.clicked.connect(lambda: PitchBinDialog(app_state, parent_window).exec_())

    # --- Binding E/R ---
    def on_e_changed():
        try:
            vals = [float(v) for v in edit_e_min.text().split(',') if v.strip()]
            # Convert to GeV
            e_gev = np.array(vals) / (1000.0 if combo_e_units.currentIndex()==0 else 1.0)
            r_gv = kinematics.convert_T_to_R(e_gev, 0.938, 1.0, 1.0)
            app_state.update_multiple(e=list(e_gev), rig=list(r_gv), is_e=True)
        except: on_core_e_changed(app_state.e)
    edit_e_min.editingFinished.connect(on_e_changed)
    
    def on_core_e_changed(v):
        with QSignalBlocker(edit_e_min):
            if v == [-1]: edit_e_min.setText("All")
            else:
                fac = 1000.0 if combo_e_units.currentIndex()==0 else 1.0
                edit_e_min.setText(_list_to_str(np.array(v)*fac, ".3f"))
    connector.e_changed.connect(on_core_e_changed)
    combo_e_units.currentIndexChanged.connect(lambda: on_core_e_changed(app_state.e))

    # --- FIX: E MAX ---
    def on_core_e_max_changed(v):
        with QSignalBlocker(edit_e_max):
            fac = 1000.0 if combo_e_units.currentIndex()==0 else 1.0
            edit_e_max.setText(_list_to_str(np.array(v)*fac, ".3f"))
    connector.e_max_changed.connect(on_core_e_max_changed)

    # R binding similar...
    def on_core_rig_changed(v):
        with QSignalBlocker(edit_r_min):
            if v == [-1]: edit_r_min.setText("All")
            else:
                fac = 1000.0 if combo_r_units.currentIndex()==0 else 1.0
                edit_r_min.setText(_list_to_str(np.array(v)*fac, ".3f"))
    connector.rig_changed.connect(on_core_rig_changed)
    
    # --- FIX: R MAX ---
    def on_core_rig_max_changed(v):
        with QSignalBlocker(edit_r_max):
            fac = 1000.0 if combo_r_units.currentIndex()==0 else 1.0
            edit_r_max.setText(_list_to_str(np.array(v)*fac, ".3f"))
    connector.rig_max_changed.connect(on_core_rig_max_changed)
    combo_r_units.currentIndexChanged.connect(lambda: on_core_rig_changed(app_state.rig))

    button_show_e.clicked.connect(lambda: EBinDialog(app_state, parent_window).exec_())
    
    # Time binding
    def on_dt_change():
        try: app_state.dt = float(edit_dt.text())
        except: pass
    edit_dt.editingFinished.connect(on_dt_change)
    connector.dt_changed.connect(lambda v: edit_dt.setText(str(v)))

    # Init
    update_ui_state(app_state.plot_kind)
    on_core_l_changed(app_state.l); on_core_l_max_changed(app_state.l_max)
    on_core_pitch_changed(app_state.pitch); on_core_pitch_max_changed(app_state.pitch_max)
    on_core_e_changed(app_state.e); on_core_e_max_changed(app_state.e_max)
    on_core_rig_changed(app_state.rig); on_core_rig_max_changed(app_state.rig_max)
    
    return widget
