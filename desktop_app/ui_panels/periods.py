"""
Порт pan01_set04_Periods, pan03_set01_Dates, pan03_set02_Pamdays
И ТЕПЕРЬ pan03_set03_Passages (Passages + Full Day)
"""
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QLabel, QComboBox, 
                             QLineEdit, QPushButton, QGroupBox, QVBoxLayout, QCheckBox, QMessageBox)
from PyQt5.QtCore import QSignalBlocker
from core import config
from core.state import ApplicationState
from desktop_app.qt_connector import QtConnector
from desktop_app.dialogs.long_periods import LongPeriodsDialog
from desktop_app.dialogs.days_dialog import DaysDialog

def pam_to_date_str(pam_day):
    try:
        base_date = datetime(2005, 12, 31)
        target_date = base_date + timedelta(days=float(pam_day))
        return target_date.strftime('%Y-%m-%d')
    except Exception: return ""

def date_str_to_pam(date_str):
    try:
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        base_date = datetime(2005, 12, 31)
        delta = dt - base_date
        return int(delta.days)
    except ValueError: return None

def _list_to_str(val_list):
    if not val_list: return ""
    return ", ".join(str(v) for v in val_list)

def create_periods_widget(app_state: ApplicationState, connector: QtConnector, parent_window):
    widget = QGroupBox("Temporal Parameters")
    layout = QVBoxLayout()
    widget.setLayout(layout)
    layout.setContentsMargins(5, 10, 5, 5)

    # --- 1. T Bins / Period ---
    row1 = QHBoxLayout()
    combo_tbins = QComboBox(); combo_tbins.addItems(config.TBIN_STR)
    edit_period = QLineEdit(); edit_period.setReadOnly(True)
    btn_show_period = QPushButton("?"); btn_show_period.setFixedWidth(30)
    row1.addWidget(QLabel("T bins:")); row1.addWidget(combo_tbins)
    row1.addWidget(QLabel("Period:")); row1.addWidget(edit_period); row1.addWidget(btn_show_period)
    layout.addLayout(row1)

    # --- 2. Dates ---
    row2 = QHBoxLayout()
    edit_date_start = QLineEdit("yyyy-mm-dd")
    edit_date_end = QLineEdit("yyyy-mm-dd")
    row2.addWidget(QLabel("Date Start:")); row2.addWidget(edit_date_start)
    row2.addWidget(QLabel("End:")); row2.addWidget(edit_date_end)
    layout.addLayout(row2)

    # --- 3. Pam Days ---
    row3 = QHBoxLayout()
    edit_day_start = QLineEdit()
    edit_day_end = QLineEdit()
    btn_show_days = QPushButton("?"); btn_show_days.setFixedWidth(30)
    btn_clr_days = QPushButton("clr"); btn_clr_days.setFixedWidth(30)
    row3.addWidget(QLabel("Pam Day Start:")); row3.addWidget(edit_day_start); row3.addWidget(btn_show_days)
    row3.addWidget(QLabel("End:")); row3.addWidget(edit_day_end); row3.addWidget(btn_clr_days)
    layout.addLayout(row3)
    
    # --- 4. Passages & Full Day (НОВОЕ) ---
    row4 = QHBoxLayout()
    edit_passages = QLineEdit()
    btn_show_pass = QPushButton("?"); btn_show_pass.setFixedWidth(30)
    chk_full_day = QCheckBox("Full day")
    
    row4.addWidget(QLabel("#:")); row4.addWidget(edit_passages)
    row4.addWidget(btn_show_pass)
    row4.addWidget(chk_full_day)
    layout.addLayout(row4)

    # -----------------------------------------------------------------
    # LOGIC
    # -----------------------------------------------------------------

    # T Bins
    combo_tbins.currentIndexChanged.connect(lambda i: setattr(app_state, 'tbin', config.TBIN_STR[i]))
    def on_core_tbin(val):
        if val in config.TBIN_STR:
            with QSignalBlocker(combo_tbins): combo_tbins.setCurrentIndex(config.TBIN_STR.index(val))
        
        is_per = (val == 'passage' or val == 'Separate Periods')
        btn_show_period.setEnabled(is_per); edit_period.setEnabled(is_per)
        
        is_date = not is_per
        edit_date_start.setEnabled(is_date); edit_date_end.setEnabled(is_date)
        edit_day_start.setEnabled(is_date); edit_day_end.setEnabled(is_date)
        btn_show_days.setEnabled(is_date)
        
        # Логика Passages (активны только если выбран конкретный день/дни, но не Separate Periods)
        is_pass = (val == 'day' or val == 'passage')
        edit_passages.setEnabled(is_pass); btn_show_pass.setEnabled(is_pass); chk_full_day.setEnabled(is_pass)

    connector.tbin_changed.connect(on_core_tbin)

    # Period
    connector.period_changed.connect(lambda v: edit_period.setText(v))
    btn_show_period.clicked.connect(lambda: LongPeriodsDialog(app_state, parent_window).exec_())

    # Days / Dates
    def on_day_edit():
        try: app_state.pam_pers = [int(edit_day_start.text())]
        except: pass
    edit_day_start.editingFinished.connect(on_day_edit)
    
    def on_date_edit():
        d = date_str_to_pam(edit_date_start.text())
        if d: app_state.pam_pers = [d]
    edit_date_start.editingFinished.connect(on_date_edit)
    
    def on_core_pam(val):
        if not val:
            edit_day_start.setText(""); edit_day_end.setText("")
            edit_date_start.setText("yyyy-mm-dd"); edit_date_end.setText("yyyy-mm-dd")
        else:
            s, e = val[0], val[-1] if len(val)>1 else val[0]
            with QSignalBlocker(edit_day_start): edit_day_start.setText(str(s))
            with QSignalBlocker(edit_day_end): edit_day_end.setText(str(e) if len(val)>1 else "")
            with QSignalBlocker(edit_date_start): edit_date_start.setText(pam_to_date_str(s))
            with QSignalBlocker(edit_date_end): edit_date_end.setText(pam_to_date_str(e) if len(val)>1 else "")
    connector.pam_pers_changed.connect(on_core_pam)
    
    btn_clr_days.clicked.connect(lambda: setattr(app_state, 'pam_pers', []))
    btn_show_days.clicked.connect(lambda: DaysDialog(app_state, parent_window).exec_())

    # --- Passages Logic (НОВОЕ) ---
    
    # GUI -> Core
    def on_pass_edit():
        txt = edit_passages.text()
        try:
            # Парсим "1, 2, 3"
            vals = [int(x.strip()) for x in txt.split(',') if x.strip()]
            app_state.passages = vals
            if vals:
                app_state.fullday = False # Если ввели пролеты, снимаем Full day
        except: pass
    edit_passages.editingFinished.connect(on_pass_edit)
    
    def on_fullday_click(checked):
        app_state.fullday = checked
        if checked:
            app_state.passages = [] # Очищаем пролеты
    chk_full_day.clicked.connect(on_fullday_click)

    # Core -> GUI
    def on_core_pass(val):
        with QSignalBlocker(edit_passages): edit_passages.setText(_list_to_str(val))
    connector.passages_changed.connect(on_core_pass)
    
    def on_core_fullday(val):
        with QSignalBlocker(chk_full_day): chk_full_day.setChecked(val)
        # Блокируем ввод пролетов, если Full Day
        edit_passages.setEnabled(not val)
        btn_show_pass.setEnabled(not val)
    connector.fullday_changed.connect(on_core_fullday)
    
    # Кнопка ? для Passages
    def on_show_pass_click():
        # Нужен файл PassageStat.m или логика загрузки
        QMessageBox.information(parent_window, "TODO", "Диалог выбора пролетов (PassageStat) требует портирования.")
    btn_show_pass.clicked.connect(on_show_pass_click)


    # Инициализация
    on_core_tbin(app_state.tbin)
    on_core_period_changed(app_state.period)
    on_core_pam(app_state.pam_pers)
    on_core_pass(app_state.passages)
    on_core_fullday(app_state.fullday)

    return widget
