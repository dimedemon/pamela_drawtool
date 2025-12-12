"""
Панель управления графиком.
Добавлен тип 12: Flux Distribution.
"""
from PyQt5.QtWidgets import (QGroupBox, QVBoxLayout, QHBoxLayout, QLabel, 
                             QComboBox, QSpinBox, QSpacerItem, QSizePolicy)
from PyQt5.QtCore import QSignalBlocker
from core.state import ApplicationState
from desktop_app.qt_connector import QtConnector

PLOT_TYPES = {
    1: "Energy spectra",
    2: "Rigidity spectra",
    3: "Pitch angle profile",
    4: "Radial profile",
    5: "Temporal variations",
    6: "Variations along orbit",
    8: "L-pitch map",
    9: "Energy-pitch map",
    10: "Energy-L map",
    11: "Auxiliary parameters",
    12: "Flux Distribution (Hist)" # <--- НОВЫЙ ПУНКТ
}

def create_plot_controls_widget(app_state: ApplicationState, connector: QtConnector, parent_window):
    widget = QGroupBox("Plot controls")
    layout = QVBoxLayout()
    widget.setLayout(layout)
    layout.setContentsMargins(5, 10, 5, 5)

    # 1. Plot Type
    row1 = QHBoxLayout()
    combo_plot_kind = QComboBox()
    # Сортируем ключи, чтобы меню было аккуратным
    sorted_keys = sorted(PLOT_TYPES.keys())
    for k in sorted_keys:
        combo_plot_kind.addItem(PLOT_TYPES[k], k)
        
    row1.addWidget(QLabel("Plot type:"))
    row1.addWidget(combo_plot_kind)
    layout.addLayout(row1)

    # 2. What
    row2 = QHBoxLayout()
    combo_what = QComboBox()
    combo_what.addItems(["Flux", "Ratio"]) 
    row2.addWidget(QLabel("What:"))
    row2.addWidget(combo_what)
    layout.addLayout(row2)

    # 3. Units / N min
    row3 = QHBoxLayout()
    combo_units = QComboBox()
    combo_units.addItems(["MeV", "GeV"])
    spin_n_min = QSpinBox()
    spin_n_min.setRange(0, 1000)
    
    row3.addWidget(QLabel("Units:"))
    row3.addWidget(combo_units)
    row3.addWidget(QLabel("N min:"))
    row3.addWidget(spin_n_min)
    layout.addLayout(row3)

    # --- Logic ---
    def on_plot_kind_changed(idx):
        kind_id = combo_plot_kind.itemData(idx)
        app_state.plot_kind = kind_id

    combo_plot_kind.currentIndexChanged.connect(on_plot_kind_changed)

    def on_core_plot_kind(val):
        idx = combo_plot_kind.findData(val)
        if idx >= 0:
            with QSignalBlocker(combo_plot_kind):
                combo_plot_kind.setCurrentIndex(idx)
    
    connector.plot_kind_changed.connect(on_core_plot_kind)

    # Units
    combo_units.currentIndexChanged.connect(lambda i: setattr(app_state, 'units', i))
    connector.units_changed.connect(lambda v: combo_units.setCurrentIndex(v))

    # N min
    spin_n_min.valueChanged.connect(lambda v: setattr(app_state, 'n_min', v))
    connector.n_min_changed.connect(lambda v: spin_n_min.setValue(v))

    # Init
    on_core_plot_kind(app_state.plot_kind)
    combo_units.setCurrentIndex(app_state.units)
    spin_n_min.setValue(app_state.n_min)

    return widget
