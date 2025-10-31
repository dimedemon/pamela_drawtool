"""
Порт pan01_set04_Periods.m

Создает виджеты для "T bins" и "Period".
"""
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QComboBox, QLineEdit, QPushButton, QGroupBox
from PyQt5.QtCore import QSignalBlocker
from core import config
from core.state import ApplicationState
from desktop_app.qt_connector import QtConnector
from desktop_app.dialogs.long_periods import LongPeriodsDialog
# (short_periods_dialog импортируем позже)

def create_periods_widget(app_state: ApplicationState, connector: QtConnector, parent_window):
    """
    Создает QGroupBox, содержащий Tbins и Period.
    """
    # 1. Создаем виджеты
    widget = QGroupBox("Temporal Parameters")
    layout = QVBoxLayout() # Вертикальный макет
    widget.setLayout(layout)
    layout.setContentsMargins(5, 10, 5, 5)

    # --- Макет 1: T Bins ---
    layout_tbins = QHBoxLayout()
    label_tbins = QLabel("T bins:")
    combo_tbins = QComboBox()
    combo_tbins.addItems(config.TBIN_STR)
    
    layout_tbins.addWidget(label_tbins)
    layout_tbins.addWidget(combo_tbins)
    layout.addLayout(layout_tbins)

    # --- Макет 2: Period ---
    layout_period = QHBoxLayout()
    label_period = QLabel("Period:")
    edit_period = QLineEdit()
    edit_period.setReadOnly(True) # Только для чтения
    button_show_period = QPushButton("?")
    button_show_period.setFixedWidth(30)
    
    layout_period.addWidget(label_period)
    layout_period.addWidget(edit_period)
    layout_period.addWidget(button_show_period)
    layout.addLayout(layout_period)

    # -----------------------------------------------------------------
    # 3. Связывание (Binding)
    # -----------------------------------------------------------------

    # --- T Bins ---
    def on_tbins_changed(index):
        tbin_value = config.TBIN_STR[index]
        app_state.Tbin = tbin_value

    combo_tbins.currentIndexChanged.connect(on_tbins_changed)

    def on_core_tbin_changed(new_tbin):
        if new_tbin in config.TBIN_STR:
            idx = config.TBIN_STR.index(new_tbin)
            with QSignalBlocker(combo_tbins):
                combo_tbins.setCurrentIndex(idx)
        
        # Включаем/выключаем кнопку "?"
        # (Логика из SetPeriodTypeDependancees.m)
        if new_tbin == 'passage' or new_tbin == 'Separate Periods':
             button_show_period.setEnabled(True)
             edit_period.setEnabled(True)
        else:
             button_show_period.setEnabled(False)
             edit_period.setEnabled(False)

    connector.tbin_changed.connect(on_core_tbin_changed)

    # --- Period ---
    def on_core_period_changed(new_period):
        with QSignalBlocker(edit_period):
            edit_period.setText(new_period)
            
    connector.period_changed.connect(on_core_period_changed)
    
    # --- Кнопка "?" ---
    def on_show_periods():
        tbin = app_state.Tbin
        
        if tbin == 'Separate Periods':
            # Показываем диалог "длинных" периодов
            dialog = LongPeriodsDialog(app_state, parent_window)
            dialog.exec_()
        elif tbin == 'passage':
            # TODO: Показываем диалог "коротких" периодов (dt)
            # dialog = ShortPeriodsDialog(app_state, parent_window)
            # dialog.exec_()
            print("ДИАЛОГ 'ShortPeriods' (dt) ЕЩЕ НЕ РЕАЛИЗОВАН")
            pass
            
    button_show_period.clicked.connect(on_show_periods)

    # 4. Инициализация
    on_core_tbin_changed(app_state.Tbin)
    on_core_period_changed(app_state.Period)
    
    return widget
