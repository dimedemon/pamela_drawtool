"""
Порт pan04_GeomagneticParams.m (MAX VALUES FIX)
Исправлено заполнение правых полей (max values) для L и Pitch.
"""
import numpy as np
from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QGroupBox, QVBoxLayout, QComboBox)
from PyQt5.QtCore import QSignalBlocker
from core import kinematics
from core.state import ApplicationState
from desktop_app.qt_connector import QtConnector
from desktop_app.dialogs.l_bin_dialog import LBinDialog
from desktop_app.dialogs.pitch_bin_dialog import PitchBinDialog 
from desktop_app.dialogs.e_bin_dialog import EBinDialog

def _list_to_str(val_list, fmt=".3f"):
    """Универсальный конвертер в строку для списков и чисел."""
    if val_list is None: return ""
    # Если пришло одно число (float/int), превращаем его в строку
    if isinstance(val_list, (int, float)): return f"{val_list:{fmt}}"
    # Если список пуст
    if len(val_list) == 0: return ""
    # Если список [-1] (код для 'All')
    if len(val_list) == 1 and val_list[0] == -1: return "All"
    # Стандартный список
    return ", ".join(f"{val:{fmt}}" for val in val_list)

def create_geomag_params_widget(app_state: ApplicationState, connector: QtConnector, parent_window):
    widget = QGroupBox("Input parameters: Geomagnetic")
    main_layout = QVBoxLayout()
    widget.setLayout(main_layout)
    main_layout.setContentsMargins(5, 10, 5, 5)

    # --- Header ---
    header_layout = QHBoxLayout()
    header_layout.addWidget(QLabel(""), 1)
    header_layout.addWidget(QLabel("min value"), 4)
    header_layout.addWidget(QLabel("units / ..."), 2)
    header_layout.addWidget(QLabel("max value"), 2)
    header_layout.addWidget(QLabel("Δ"), 1)
    main_layout.addLayout(header_layout)

    # --- L-Shell ---
    l_layout = QHBoxLayout()
    edit_l_min = QLineEdit(); button_show_l = QPushButton("..."); button_show_l.setFixedWidth(30)
    edit_l_max = QLineEdit(); edit_delta_l = QLineEdit()
    l_layout.addWidget(QLabel("L:"), 1); l_layout.addWidget(edit_l_min, 4); l_layout.addWidget(button_show_l, 2)
    l_layout.addWidget(edit_l_max, 2); l_layout.addWidget(edit_delta_l, 1)
    main_layout.addLayout(l_layout)

    # --- Pitch ---
    pitch_layout = QHBoxLayout()
    edit_pitch_min = QLineEdit(); button_show_pitch = QPushButton("..."); button_show_pitch.setFixedWidth(30)
    edit_pitch_max = QLineEdit(); edit_delta_alpha = QLineEdit()
    pitch_layout.addWidget(QLabel("α:"), 1); pitch_layout.addWidget(edit_pitch_min, 4); pitch_layout.addWidget(button_show_pitch, 2)
    pitch_layout.addWidget(edit_pitch_max, 2); pitch_layout.addWidget(edit_delta_alpha, 1)
    main_layout.addLayout(pitch_layout)
    
    # --- Energy ---
    e_layout = QHBoxLayout()
    edit_e_min = QLineEdit(); combo_e_units = QComboBox(); combo_e_units.addItems(['MeV', 'GeV']); combo_e_units.setCurrentIndex(1)
    button_show_e = QPushButton("..."); button_show_e.setFixedWidth(30)
    edit_e_max = QLineEdit(); edit_delta_e = QLineEdit()
    e_units_layout = QHBoxLayout(); e_units_layout.setContentsMargins(0,0,0,0)
    e_units_layout.addWidget(combo_e_units); e_units_layout.addWidget(button_show_e)
    e_layout.addWidget(QLabel("E:"), 1); e_layout.addWidget(edit_e_min, 4); e_layout.addLayout(e_units_layout, 2)
    e_layout.addWidget(edit_e_max, 2); e_layout.addWidget(edit_delta_e, 1)
    main_layout.addLayout(e_layout)

    # --- Rigidity ---
    r_layout = QHBoxLayout()
    edit_r_min = QLineEdit(); combo_r_units = QComboBox(); combo_r_units.addItems(['MV', 'GV']); combo_r_units.setCurrentIndex(1)
    edit_r_max = QLineEdit()
    r_layout.addWidget(QLabel("R:"), 1); r_layout.addWidget(edit_r_min, 4); r_layout.addWidget(combo_r_units, 2)
    r_layout.addWidget(edit_r_max, 2); r_layout.addWidget(QLabel(""), 1)
    main_layout.addLayout(r_layout)

    # --- Time ---
    t_layout = QHBoxLayout()
    edit_t_min = QLineEdit("hh:mm:ss"); edit_t_max = QLineEdit("hh:mm:ss"); edit_dt = QLineEdit()
    t_layout.addWidget(QLabel("t:"), 1); t_layout.addWidget(edit_t_min, 4); t_layout.addWidget(QLabel(""), 2)
    t_layout.addWidget(edit_t_max, 2); t_layout.addWidget(edit_dt, 1)
    main_layout.addLayout(t_layout)

    # --- UI State Logic ---
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

    # ---------------- BINDINGS ----------------

    # === L-Shell ===
    # MIN
    def on_l_min_edit():
        try: app_state.l = [float(v) for v in edit_l_min.text().split(',') if v.strip()]
        except: connector.l_changed.emit(app_state.l)
    edit_l_min.editingFinished.connect(on_l_min_edit)
    connector.l_changed.connect(lambda v: edit_l_min.setText(_list_to_str(v, ".3f")))
    
    # MAX (Вот та самая связка!)
    connector.l_max_changed.connect(lambda v: edit_l_max.setText(_list_to_str(v, ".3f")))
    
    button_show_l.clicked.connect(lambda: LBinDialog(app_state, parent_window).exec_())

    # === PITCH ===
    # MIN
    def on_pitch_min_edit():
        try: app_state.pitch = [float(v) for v in edit_pitch_min.text().split(',') if v.strip()]
        except: connector.pitch_changed.emit(app_state.pitch)
    edit_pitch_min.editingFinished.connect(on_pitch_min_edit)
    connector.pitch_changed.connect(lambda v: edit_pitch_min.setText(_list_to_str(v, ".1f")))
    
    # MAX (Вот та самая связка!)
    connector.pitch_max_changed.connect(lambda v: edit_pitch_max.setText(_list_to_str(v, ".1f")))
    
    button_show_pitch.clicked.connect(lambda: PitchBinDialog(app_state, parent_window).exec_())

    # === E/R ===
    # E
    def on_e_edit():
        try:
            vals = [float(v) for v in edit_e_min.text().split(',') if v.strip()]
            e_gev = np.array(vals) / (1000.0 if combo_e_units.currentIndex()==0 else 1.0)
            r_gv = kinematics.convert_T_to_R(e_gev, 0.938, 1.0, 1.0)
            app_state.update_multiple(e=list(e_gev), rig=list(r_gv), is_e=True)
        except: connector.e_changed.emit(app_state.e)
    edit_e_min.editingFinished.connect(on_e_edit)
    
    def update_e_disp(v):
        fac = 1000.0 if combo_e_units.currentIndex()==0 else 1.0
        with QSignalBlocker(edit_e_min): edit_e_min.setText(_list_to_str(np.array(v)*fac, ".3f"))
    connector.e_changed.connect(update_e_disp)
    combo_e_units.currentIndexChanged.connect(lambda: update_e_disp(app_state.e))
    
    # E MAX
    connector.e_max_changed.connect(lambda v: edit_e_max.setText(_list_to_str(np.array(v)*(1000.0 if combo_e_units.currentIndex()==0 else 1.0), ".3f")))

    # R MAX
    connector.rig_max_changed.connect(lambda v: edit_r_max.setText(_list_to_str(np.array(v)*(1000.0 if combo_r_units.currentIndex()==0 else 1.0), ".3f")))
    
    button_show_e.clicked.connect(lambda: EBinDialog(app_state, parent_window).exec_())

    # === TIME ===
    def on_dt_edit():
        try: app_state.dt = float(edit_dt.text())
        except: connector.dt_changed.emit(app_state.dt)
    edit_dt.editingFinished.connect(on_dt_edit)
    connector.dt_changed.connect(lambda v: edit_dt.setText(str(v)))

    # Инициализация
    update_ui_state(app_state.plot_kind)
    connector.l_changed.emit(app_state.l)
    connector.l_max_changed.emit(app_state.l_max)
    connector.pitch_changed.emit(app_state.pitch)
    connector.pitch_max_changed.emit(app_state.pitch_max)
    connector.e_changed.emit(app_state.e)
    
    return widget
