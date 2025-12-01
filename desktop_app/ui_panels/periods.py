"""
Порт pan01_set04_Periods.m, pan03_set01_Dates.m, pan03_set02_Pamdays.m

Объединяет управление Tbin/Period и выбор Дат/Дней PAMELA.
"""
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QLabel, QComboBox, 
                             QLineEdit, QPushButton, QGroupBox, QVBoxLayout)
from PyQt5.QtCore import QSignalBlocker
from core import config
from core.state import ApplicationState
from desktop_app.qt_connector import QtConnector
from desktop_app.dialogs.long_periods import LongPeriodsDialog
from desktop_app.dialogs.days_dialog import DaysDialog # <--- Импорт диалога дней

# Константа PAMSTART из config
PAM_START_JD = config.PAMSTART

def pam_to_date_str(pam_day):
    """Конвертирует номер дня PAMELA в строку даты (YYYY-MM-DD)."""
    try:
        # HACK: Для прототипа используем базовую дату 2005-12-31 + pam_day
        base_date = datetime(2005, 12, 31)
        target_date = base_date + timedelta(days=float(pam_day))
        return target_date.strftime('%Y-%m-%d')
    except Exception:
        return ""

def date_str_to_pam(date_str):
    """Конвертирует строку даты (YYYY-MM-DD) в номер дня PAMELA."""
    try:
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        base_date = datetime(2005, 12, 31)
        delta = dt - base_date
        return int(delta.days)
    except ValueError:
        return None

def create_periods_widget(app_state: ApplicationState, connector: QtConnector, parent_window):
    """
    Создает QGroupBox "Temporal Parameters" с выбором Tbin, Period и Dates.
    """
    widget = QGroupBox("Temporal Parameters")
    layout = QVBoxLayout()
    widget.setLayout(layout)
    layout.setContentsMargins(5, 10, 5, 5)

    # --- Секция 1: T Bins и Period ---
    row1 = QHBoxLayout()
    
    # T Bins
    combo_tbins = QComboBox()
    combo_tbins.addItems(config.TBIN_STR)
    row1.addWidget(QLabel("T bins:"))
    row1.addWidget(combo_tbins)
    
    # Period
    edit_period = QLineEdit()
    edit_period.setReadOnly(True)
    btn_show_period = QPushButton("?")
    btn_show_period.setFixedWidth(30)
    row1.addWidget(QLabel("Period:"))
    row1.addWidget(edit_period)
    row1.addWidget(btn_show_period)
    
    layout.addLayout(row1)

    # --- Секция 2: Даты (Date) ---
    row2 = QHBoxLayout()
    edit_date_start = QLineEdit("yyyy-mm-dd")
    edit_date_end = QLineEdit("yyyy-mm-dd")
    
    row2.addWidget(QLabel("Date Start:"))
    row2.addWidget(edit_date_start)
    row2.addWidget(QLabel("End:"))
    row2.addWidget(edit_date_end)
    
    layout.addLayout(row2)

    # --- Секция 3: Дни PAMELA (Pam day) ---
    row3 = QHBoxLayout()
    edit_day_start = QLineEdit()
    edit_day_end = QLineEdit()
    
    # Кнопка для вызова календаря
    btn_show_days = QPushButton("?") 
    btn_show_days.setFixedWidth(30)
    
    btn_clr_days = QPushButton("clr")
    btn_clr_days.setFixedWidth(30)
    
    row3.addWidget(QLabel("Pam Day Start:"))
    row3.addWidget(edit_day_start)
    row3.addWidget(btn_show_days)
    row3.addWidget(QLabel("End:"))
    row3.addWidget(edit_day_end)
    row3.addWidget(btn_clr_days)
    
    layout.addLayout(row3)

    # -----------------------------------------------------------------
    # Логика Связывания (Binding)
    # -----------------------------------------------------------------

    # 1. T Bins & Period (Старая логика)
    def on_tbins_changed(index):
        app_state.tbin = config.TBIN_STR[index]

    combo_tbins.currentIndexChanged.connect(on_tbins_changed)

    def on_core_tbin_changed(new_tbin):
        if new_tbin in config.TBIN_STR:
            with QSignalBlocker(combo_tbins):
                combo_tbins.setCurrentIndex(config.TBIN_STR.index(new_tbin))
        
        is_period_mode = (new_tbin == 'passage' or new_tbin == 'Separate Periods')
        btn_show_period.setEnabled(is_period_mode)
        edit_period.setEnabled(is_period_mode)
        
        # Включаем/выключаем даты в зависимости от режима
        is_date_mode = not is_period_mode
        edit_date_start.setEnabled(is_date_mode)
        edit_date_end.setEnabled(is_date_mode)
        edit_day_start.setEnabled(is_date_mode)
        edit_day_end.setEnabled(is_date_mode)
        btn_show_days.setEnabled(is_date_mode) # Кнопка календаря

    connector.tbin_changed.connect(on_core_tbin_changed)

    def on_core_period_changed(new_period):
        with QSignalBlocker(edit_period):
            edit_period.setText(new_period)
    connector.period_changed.connect(on_core_period_changed)

    def on_show_periods_click():
        if app_state.tbin == 'Separate Periods':
            dialog = LongPeriodsDialog(app_state, parent_window)
            dialog.exec_()
    btn_show_period.clicked.connect(on_show_periods_click)

    # 2. Dates & Days (Новая логика)
    
    # --- GUI -> Core (Изменение ДНЯ) ---
    def on_day_start_edited():
        try:
            val = int(edit_day_start.text())
            app_state.pam_pers = [val]
        except ValueError:
            pass

    edit_day_start.editingFinished.connect(on_day_start_edited)

    # --- GUI -> Core (Изменение ДАТЫ) ---
    def on_date_start_edited():
        pam_day = date_str_to_pam(edit_date_start.text())
        if pam_day is not None:
            app_state.pam_pers = [pam_day]
        else:
            on_core_pam_pers_changed(app_state.pam_pers)

    edit_date_start.editingFinished.connect(on_date_start_edited)

    # --- Core -> GUI (Обновление ВСЕХ полей) ---
    def on_core_pam_pers_changed(new_pers_list):
        if not new_pers_list:
            with QSignalBlocker(edit_day_start): edit_day_start.setText("")
            with QSignalBlocker(edit_day_end): edit_day_end.setText("")
            with QSignalBlocker(edit_date_start): edit_date_start.setText("yyyy-mm-dd")
            with QSignalBlocker(edit_date_end): edit_date_end.setText("yyyy-mm-dd")
            return

        start_day = new_pers_list[0]
        end_day = new_pers_list[-1] if len(new_pers_list) > 1 else start_day
        
        with QSignalBlocker(edit_day_start): edit_day_start.setText(str(start_day))
        with QSignalBlocker(edit_day_end): 
            edit_day_end.setText(str(end_day) if len(new_pers_list) > 1 else "")

        with QSignalBlocker(edit_date_start): edit_date_start.setText(pam_to_date_str(start_day))
        with QSignalBlocker(edit_date_end): 
            txt = pam_to_date_str(end_day) if len(new_pers_list) > 1 else ""
            edit_date_end.setText(txt)

    connector.pam_pers_changed.connect(on_core_pam_pers_changed)

    # Кнопка CLR
    def on_clr_click():
        app_state.pam_pers = []
    btn_clr_days.clicked.connect(on_clr_click)
    
    # --- Кнопка '?' для дней (ShowDays) ---
    def on_show_days_click():
        dialog = DaysDialog(app_state, parent_window)
        dialog.exec_()
        
    btn_show_days.clicked.connect(on_show_days_click)

    # 3. Инициализация
    on_core_tbin_changed(app_state.tbin)
    on_core_period_changed(app_state.period)
    on_core_pam_pers_changed(app_state.pam_pers)

    return widget
