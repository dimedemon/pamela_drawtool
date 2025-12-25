"""
Порт ShowDays (LOCAL + CRASH FIX).
Использует файлы из локальной папки проекта (config.UI_DATA_PATH).
Исправлена ошибка доступа к атрибутам словаря.
"""
import os
import numpy as np
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem,
                             QPushButton, QHBoxLayout, QHeaderView, QLabel, QWidget,
                             QFrame, QAbstractItemView, QMessageBox)
from PyQt5.QtGui import QColor, QBrush
from PyQt5.QtCore import Qt
from core import config
from core.state import ApplicationState

DAY_QUAL_INFO = {
    0: {'color': '#3d3339', 'desc': 'PAMELA OFF', 'text_col': 'white'},
    1: {'color': '#80df20', 'desc': 'Good Data', 'text_col': 'black'},
    2: {'color': '#e1d81a', 'desc': 'Short File', 'text_col': 'black'},
    4: {'color': '#ec614b', 'desc': 'Tracker OFF', 'text_col': 'black'},
    6: {'color': '#ecb245', 'desc': 'Orientation Missed', 'text_col': 'black'},
    7: {'color': '#63eae8', 'desc': 'Calo OFF', 'text_col': 'black'}
}
DEFAULT_QUAL = {'color': '#ffffff', 'desc': 'Unknown Status', 'text_col': 'black'}

def get_kp_color_hex(kp):
    if kp < 3: return '#00aa00'
    if kp < 5: return '#ccaa00'
    if kp < 7: return '#ff6600'
    return '#ff0000'

# Хелпер для безопасного доступа (dict или object)
def _get_field(obj, key):
    if isinstance(obj, dict):
        return obj.get(key)
    return getattr(obj, key, None)

class DaysDialog(QDialog):
    def __init__(self, app_state: ApplicationState, parent=None):
        super().__init__(parent)
        self.app_state = app_state
        self.selected_day = None
        
        self.day_quality_map = {} 
        self.bartels_data = None
        self.carrington_data = None
        self.mag_data_map = {} 
        self.row_map_cache = {} 
        
        self.setWindowTitle("Mission Timeline (Local Data)")
        self.resize(1100, 650)
        
        main_layout = QHBoxLayout()
        self.setLayout(main_layout)
        
        # Left Panel
        left_panel = QWidget()
        left_panel.setFixedWidth(300)
        left_layout = QVBoxLayout()
        left_panel.setLayout(left_layout)
        
        left_layout.addWidget(QLabel("<b>Status Legend:</b>"))
        self.create_legend(left_layout)
        
        line = QFrame(); line.setFrameShape(QFrame.HLine); line.setFrameShadow(QFrame.Sunken)
        left_layout.addWidget(line)
        
        self.info_box = QLabel("Select a day...")
        self.info_box.setWordWrap(True)
        self.info_box.setStyleSheet("background-color: #f9f9f9; padding: 10px; border: 1px solid #ddd;")
        left_layout.addWidget(self.info_box)
        left_layout.addStretch()
        
        self.btn_set_start = QPushButton("Set as START")
        self.btn_set_end = QPushButton("Set as END")
        self.btn_set_start.setEnabled(False)
        self.btn_set_end.setEnabled(False)
        self.btn_set_start.clicked.connect(self.on_set_start)
        self.btn_set_end.clicked.connect(self.on_set_end)
        left_layout.addWidget(self.btn_set_start)
        left_layout.addWidget(self.btn_set_end)
        
        main_layout.addWidget(left_panel)
        
        # Table
        self.table = QTableWidget()
        self.setup_table()
        self.table.cellClicked.connect(self.on_cell_clicked)
        main_layout.addWidget(self.table)
        
        # Load Data
        self.load_data()         
        self.load_solar_data()   
        self.load_mag_data()     
        
        self.fill_table()        

    def setup_table(self):
        self.table.setColumnCount(31)
        self.table.setHorizontalHeaderLabels([str(i) for i in range(1, 32)])
        months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
        row_labels = []
        curr_row = 0
        for m in range(6, 13):
            row_labels.append(f"2006 {months[m-1]}")
            self.row_map_cache[(2006, m)] = curr_row
            curr_row += 1
        for year in range(2007, 2017):
            end_m = 12 if year < 2016 else 1
            for m in range(1, end_m + 1):
                row_labels.append(f"{year} {months[m-1]}")
                self.row_map_cache[(year, m)] = curr_row
                curr_row += 1
        self.table.setRowCount(len(row_labels))
        self.table.setVerticalHeaderLabels(row_labels)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)

    def create_legend(self, layout):
        for code in [1, 4, 6, 7, 0]:
            info = DAY_QUAL_INFO.get(code, DEFAULT_QUAL)
            lbl = QLabel(info['desc'])
            lbl.setStyleSheet(f"background-color: {info['color']}; color: {info['text_col']}; padding: 2px;")
            layout.addWidget(lbl)

    def load_data(self):
        """Загрузка Tbinning_day из локальной папки data/UserBinnings"""
        base = config.UI_DATA_PATH
        path = os.path.join(base, 'UserBinnings', 'Tbinning_day.mat')
        
        if not os.path.exists(path):
            print(f"[DAYS] ⚠️ Tbinning не найден: {path}")
            return

        mat = config._load_mat_file(path)
        if not mat: return
        try:
            # Используем безопасный геттер
            t_bins = np.array(_get_field(mat, 'Tbins')).flatten()
            day_qual = np.array(_get_field(mat, 'DayQuality')).flatten()
            for i, pam_day in enumerate(t_bins):
                self.day_quality_map[int(pam_day)] = int(day_qual[i])
        except Exception as e:
            print(f"Error loading Tbinning: {e}")

    def load_solar_data(self):
        base = config.UI_DATA_PATH
        try:
            path_b = os.path.join(base, 'SolarHelioParams', 'Bartels.mat')
            mat_b = config._load_mat_file(path_b)
            if mat_b:
                self.bartels_data = {
                    'days': np.array(_get_field(mat_b, 'pamdays')).flatten(), 
                    'bn': np.array(_get_field(mat_b, 'BN')).flatten()
                }
            
            path_c = os.path.join(base, 'SolarHelioParams', 'Carrington.mat')
            mat_c = config._load_mat_file(path_c)
            if mat_c:
                self.carrington_data = {
                    'days': np.array(_get_field(mat_c, 'pamdays')).flatten(), 
                    'cn': np.array(_get_field(mat_c, 'CN')).flatten()
                }
        except: pass

    def load_mag_data(self):
        """Загрузка MagParam2 из локальной папки data/SolarHelioParams"""
        base = config.UI_DATA_PATH
        path = os.path.join(base, 'SolarHelioParams', 'MagParam2.mat')
        
        if not os.path.exists(path):
             print(f"[DAYS] ⚠️ MagParam2 не найден: {path}")
             return

        mat = config._load_mat_file(path)
        if not mat: return

        try:
            # ИСПОЛЬЗУЕМ БЕЗОПАСНЫЙ ДОСТУП, ЧТОБЫ НЕ БЫЛО ATTRIBUTE ERROR
            unixtime = np.array(_get_field(mat, 'unixtime')).flatten()
            kp = np.array(_get_field(mat, 'Kp')).flatten()
            dst = np.array(_get_field(mat, 'Dst')).flatten()
            f10 = np.array(_get_field(mat, 'f10p7')).flatten()
            
            base_unix = datetime(2005, 12, 31).timestamp()
            pam_days_all = np.floor((unixtime - base_unix) / 86400.0).astype(int)
            
            sort_idx = np.argsort(pam_days_all)
            pam_days_sorted = pam_days_all[sort_idx]
            unique_days, change_indices = np.unique(pam_days_sorted, return_index=True)
            
            kp_max = np.maximum.reduceat(kp[sort_idx], change_indices)
            dst_min = np.minimum.reduceat(dst[sort_idx], change_indices)
            
            f10_sorted = f10[sort_idx]
            f10_sum = np.add.reduceat(f10_sorted, change_indices)
            counts = np.diff(np.append(change_indices, len(pam_days_sorted)))
            f10_mean = f10_sum / counts
            
            if not self.day_quality_map:
                 for d in unique_days: self.day_quality_map[int(d)] = 1

            for i, day in enumerate(unique_days):
                self.mag_data_map[int(day)] = {'Kp': kp_max[i], 'Dst': dst_min[i], 'F10.7': f10_mean[i]}
        except Exception as e:
            print(f"Error mag data: {e}")

    def fill_table(self):
        self.table.setUpdatesEnabled(False)
        self.table.clearContents()
        base_date = datetime(2005, 12, 31)
        for pam_day, qual in self.day_quality_map.items():
            dt = base_date + timedelta(days=pam_day)
            target_row = self.row_map_cache.get((dt.year, dt.month), -1)
            if target_row == -1: continue
            
            col = dt.day - 1
            item = QTableWidgetItem(str(pam_day))
            item.setTextAlignment(Qt.AlignCenter)
            item.setData(Qt.UserRole, pam_day)
            
            info = DAY_QUAL_INFO.get(qual, DEFAULT_QUAL)
            item.setBackground(QBrush(QColor(info['color'])))
            item.setForeground(QBrush(QColor(info['text_col'])))
            self.table.setItem(target_row, col, item)
        self.table.setUpdatesEnabled(True)

    def on_cell_clicked(self, row, col):
        item = self.table.item(row, col)
        if item:
            pam_day = item.data(Qt.UserRole)
            self.selected_day = pam_day
            date_str = (datetime(2005, 12, 31) + timedelta(days=pam_day)).strftime('%Y-%m-%d')
            qual = self.day_quality_map.get(pam_day, -1)
            q_info = DAY_QUAL_INFO.get(qual, DEFAULT_QUAL)
            
            html = f"<h3>Day {pam_day}</h3>Date: <b>{date_str}</b><br>Status: <b style='color:{q_info['color']}'>{q_info['desc']}</b><hr>"
            
            if self.bartels_data:
                idx = np.searchsorted(self.bartels_data['days'], pam_day, side='right') - 1
                if idx >= 0: html += f"Bartels: <b>{self.bartels_data['bn'][idx]}</b><br>"
            
            if pam_day in self.mag_data_map:
                mag = self.mag_data_map[pam_day]
                kp_c = get_kp_color_hex(mag['Kp'])
                dst_c = "red" if mag['Dst'] < -50 else "black"
                html += f"Kp max: <b style='color:{kp_c}'>{mag['Kp']:.1f}</b><br>Dst min: <b style='color:{dst_c}'>{mag['Dst']:.0f}</b><br>F10.7: <b>{mag['F10.7']:.1f}</b>"
            
            self.info_box.setText(html)
            self.btn_set_start.setEnabled(True)
            self.btn_set_end.setEnabled(True)

    def on_set_start(self):
        if self.selected_day:
            self.app_state.pam_pers = [self.selected_day]
            QMessageBox.information(self, "Info", f"Start Day: {self.selected_day}")
    
    def on_set_end(self):
        if self.selected_day and self.app_state.pam_pers:
            start = self.app_state.pam_pers[0]
            if self.selected_day >= start:
                self.app_state.pam_pers = list(range(start, self.selected_day + 1))
                QMessageBox.information(self, "Info", f"Range: {start} - {self.selected_day}")
