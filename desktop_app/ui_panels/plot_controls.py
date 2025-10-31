"""
Порт pan02_DrawObject.m
Включает:
- pan02_set01_PlotKindVar (PlotKind, What)
- pan02_set02_JunitsNmin (J units, min N)
"""
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QComboBox, QLineEdit, QGroupBox, QVBoxLayout
from PyQt5.QtCore import QSignalBlocker, Qt
from core import config
from core.state import ApplicationState
from desktop_app.qt_connector import QtConnector

def create_plot_controls_widget(app_state: ApplicationState, connector: QtConnector, parent_window):
    """
    Создает QGroupBox "Distribution & entity to plot".
    """
    # 1. Создаем главный контейнер (pan02)
    widget = QGroupBox("Distribution & entity to plot")
    main_layout = QVBoxLayout()
    widget.setLayout(main_layout)
    main_layout.setContentsMargins(5, 10, 5, 5)

    # --- Макет 1: PlotKind и What (set01) ---
    layout_set01 = QHBoxLayout()
    combo_plot_kind = QComboBox()
    combo_what = QComboBox()
    
    combo_plot_kind.addItems(config.PLOT_KINDS)
    combo_what.addItems(config.DISTR_VARS)
    
    layout_set01.addWidget(combo_plot_kind, 1) # 1 = доля ширины
    layout_set01.addWidget(combo_what, 1)    # 1 = доля ширины
    main_layout.addLayout(layout_set01)
    
    # --- Макет 2: J units и min N (set02) ---
    layout_set02 = QHBoxLayout()
    label_junit = QLabel("J units:")
    combo_junit = QComboBox()
    combo_junit.addItems(['(MeV cm^2 sr sec)^-1', '(GeV m^2 sr sec)^-1'])
    
    label_min_n = QLabel("min N:")
    edit_min_n = QLineEdit()
    edit_min_n.setText(str(app_state.n_min)) # Устанавливаем 0
    
    layout_set02.addWidget(label_junit)
    layout_set02.addWidget(combo_junit)
    layout_set02.addStretch()
    layout_set02.addWidget(label_min_n)
    layout_set02.addWidget(edit_min_n)
    main_layout.addLayout(layout_set02)

    # -----------------------------------------------------------------
    # 3. Связывание (Binding)
    # -----------------------------------------------------------------

    # --- Связь: GUI -> Ядро ---
    
    def on_plot_kind_changed(index):
        app_state.plot_kind = index + 1 # +1 т.к. MATLAB value с 1

    def on_what_changed(index):
        app_state.what = index + 1 # +1
        # Логика из pan02_set01 (включение/выключение J units)
        if (index + 1) > 1: # Если не "Flux"
            combo_junit.setEnabled(False)
        else:
            combo_junit.setEnabled(True)

    def on_junit_changed(index):
        app_state.units = index # 0=MeV, 1=GeV

    def on_min_n_changed():
        try:
            app_state.n_min = int(edit_min_n.text())
        except ValueError:
            edit_min_n.setText(str(app_state.n_min)) # Сброс

    combo_plot_kind.currentIndexChanged.connect(on_plot_kind_changed)
    combo_what.currentIndexChanged.connect(on_what_changed)
    combo_junit.currentIndexChanged.connect(on_junit_changed)
    edit_min_n.editingFinished.connect(on_min_n_changed)
    
    # --- Связь: Ядро -> GUI ---
    
    def on_core_plot_kind_changed(new_pk_value):
        with QSignalBlocker(combo_plot_kind):
            combo_plot_kind.setCurrentIndex(new_pk_value - 1)

    def on_core_what_changed(new_what_value):
        with QSignalBlocker(combo_what):
            combo_what.setCurrentIndex(new_what_value - 1)
        # Также триггерим обновление J units enable/disable
        on_what_changed(new_what_value - 1)

    def on_core_units_changed(new_units_value):
        with QSignalBlocker(combo_junit):
            combo_junit.setCurrentIndex(new_units_value)
            
    def on_core_n_min_changed(new_n_min_value):
        with QSignalBlocker(edit_min_n):
            edit_min_n.setText(str(new_n_min_value))

    connector.plot_kind_changed.connect(on_core_plot_kind_changed)
    connector.what_changed.connect(on_core_what_changed)
    connector.units_changed.connect(on_core_units_changed)
    connector.n_min_changed.connect(on_core_n_min_changed)
    
    # 4. Инициализация
    on_core_plot_kind_changed(app_state.plot_kind)
    on_core_what_changed(app_state.what)
    on_core_units_changed(app_state.units)
    on_core_n_min_changed(app_state.n_min)
    
    # TODO: Реализовать сложную логику фильтрации
    # (setGeomagParamEn.m и SetPeriodTypeDependancees.m)
    
    return widget
