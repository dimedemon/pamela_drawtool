"""
Порт ShowDays из pan03_set02_Pamdays.m
STABLE EDITION: Классический функционал (как в MATLAB).
- Быстрая загрузка (без MagParam).
- Раскраска по качеству данных.
- Инфо о Бартельсе/Кэррингтоне при клике.
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

# Цвета из MATLAB (DayQualColours)
# 0: OFF, 1: Good, 2: Short, 4: Tracker OFF, 6: Orient missed, 7: Calo OFF
DAY_QUAL_COLORS = [
    '#3d3339', # 0: OFF (Black)
    '#80df20', # 1: Good (Green)
    '#e1d81a', # 2: Short (Yellow)
    '#ffffff', # 3: Empty
    '#ec614b', # 4: Tracker OFF (Red)
    '#ffffff', # 5: Empty
    '#ecb245', # 6: Orientation Missed (Orange)
    '#63eae8'  # 7: Calo OFF (Cyan)
]

class DaysDialog(QDialog):
    
    def __init__(self, app_state: ApplicationState, parent=None):
        super().__init__(parent)
        self.app_state = app_state
        self.selected_day = None
        
        # Данные
        self.day_quality_map = {} 
        self.bartels_data = None
        self.carrington_data = None
        self.row_map_cache = {} 
        
        self.setWindowTitle("Days Data")
        self.setGeometry(100, 100, 1000, 600)
        
        main_layout = QHBoxLayout()
        self.setLayout(main_layout)
        
        # --- ЛЕВАЯ ПАНЕЛЬ (Инфо и Легенда) ---
        left_panel = QWidget()
        left_panel.setFixedWidth(280)
        left_layout = QVBoxLayout()
        left_panel.setLayout(left_layout)
        
        # Легенда
        left_layout.addWidget(QLabel("<b>Data Quality:</b>"))
        self.add_legend_item(left_layout, "PAMELA OFF", DAY_QUAL_COLORS[0], "white")
        self.add_legend_item(left_layout, "Good Data", DAY_QUAL_COLORS[1])
        self.add_legend_item(left_layout, "Short File", DAY_QUAL_COLORS[2])
        self.add_legend_item(left_layout, "Tracker OFF", DAY_QUAL_COLORS[4])
        self.add_legend_item(left_layout, "Orientation Missed", DAY_QUAL_COLORS[6])
        self.add_legend_item(left_layout, "Calo OFF", DAY_QUAL_COLORS[7])
        
        line = QFrame(); line.setFrameShape(QFrame.HLine); line.setFrameShadow(QFrame.Sunken)
        left_layout.addWidget(line)
        
        # Информация о выбранном дне
        self.info_box = QLabel("Select a day to see details...")
        self.info_box.setWordWrap(True)
        self.info_box.setStyleSheet("background-color: #f0f0f0; padding: 10px; border-radius: 5px;")
        font = self.info_box.font(); font.setPointSize(11); self.info_box.setFont(font)
        left_layout.addWidget(self.info_box)
        
        left_layout.addStretch()
        
        # Кнопки выбора
        self.btn_set_start = QPushButton("Set as START day")
        self.btn_set_end = QPushButton("Set as END day")
        self.btn_set_start.setEnabled(False)
        self.btn_set_end.setEnabled(False)
        self.btn_set_start.clicked.connect(self.on_set_start)
        self.btn_set_end.clicked.connect(self.on_set_end)
        
        left_layout.addWidget(self.btn_set_start)
        left_layout.addWidget(self.btn_set_end)
        
        main_layout.addWidget(left_panel)
        
        # --- ПРАВАЯ ПАНЕЛЬ (Таблица) ---
        self.table = QTableWidget()
        self.setup_table()
        self.table.cellClicked.connect(self.on_cell_clicked)
        main_layout.addWidget(self.table)
        
        # Загрузка данных
        self.load_data()         # Tbinning
        self.load_solar_data()   # Bartels/Carrington
        self.fill_table()        # Отрисовка

    def setup_table(self):
        self.table.setColumnCount(31)
        self.table.setHorizontalHeaderLabels([str(i) for i in range(1, 32)])
        
        months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
        row_labels = []
        self.row_map_cache = {}
        
        curr_row = 0
        # 2006 (Jun-Dec)
        for m in range(6, 13):
            row_labels.append(f"2006 {months[m-1]}")
            self.row_map_cache[(2006, m)] = curr_row
            curr_row += 1
            
        # 2007-2015
        for year in range(2007, 2016):
            for m in range(1, 13):
                row_labels.append(f"{year} {months[m-1]}")
                self.row_map_cache[(year, m)] = curr_row
                curr_row += 1
        
        # 2016 Jan
        row_labels.append("2016 Jan")
        self.row_map_cache[(2016, 1)] = curr_row
        
        self.table.setRowCount(len(row_labels))
        self.table.setVerticalHeaderLabels(row_labels)
        
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)

    def add_legend_item(self, layout, text, color_hex, text_color="black"):
        lbl = QLabel(text)
        lbl.setStyleSheet(f"background-color: {color_hex}; color: {text_color}; border: 1px solid gray; padding: 2px;")
        layout.addWidget(lbl)

    def load_data(self):
        """Загружает Tbinning_day.mat."""
        path = os.path.join(config.BASE_DATA_PATH, 'UserBinnings', 'Tbinning_day.mat')
        mat = config._load_mat_file(path)
        if not mat: 
            self.info_box.setText(f"Error: {path} not found.")
            return

        try:
            t_bins = np.array(mat['Tbins']).flatten()
            day_qual = np.array(mat['DayQuality']).flatten()
            
            for i, pam_day in enumerate(t_bins):
                self.day_quality_map[int(pam_day)] = int(day_qual[i])
        except Exception as e:
            print(f"Error loading Tbinning: {e}")

    def load_solar_data(self):
        """Загружает Bartels.mat и Carrington.mat."""
        try:
            path_b = os.path.join(config.BASE_DATA_PATH, 'SolarHelioParams', 'Bartels.mat')
            mat_b = config._load_mat_file(path_b)
            if mat_b:
                self.bartels_data = {
                    'days': np.array(mat_b['pamdays']).flatten(),
                    'bn': np.array(mat_b['BN']).flatten()
                }

            path_c = os.path.join(config.BASE_DATA_PATH, 'SolarHelioParams', 'Carrington.mat')
            mat_c = config._load_mat_file(path_c)
            if mat_c:
                self.carrington_data = {
                    'days': np.array(mat_c['pamdays']).flatten(),
                    'cn': np.array(mat_c['CN']).flatten()
                }
        except Exception as e:
            print(f"Error loading Solar data: {e}")

    def fill_table(self):
        """Заполняет таблицу цветами."""
        self.table.setUpdatesEnabled(False)
        self.table.clearContents()
        
        base_date = datetime(2005, 12, 31)
        
        for pam_day, qual in self.day_quality_map.items():
            # Быстрая конвертация даты
            dt = base_date + timedelta(days=pam_day)
            
            target_row = self.row_map_cache.get((dt.year, dt.month), -1)
            if target_row == -1: continue
            
            col = dt.day - 1
            item = QTableWidgetItem(str(pam_day))
            item.setTextAlignment(Qt.AlignCenter)
            item.setData(Qt.UserRole, pam_day)
            
            # Цвет
            idx = qual if qual < len(DAY_QUAL_COLORS) else 0
            bg_color = QColor(DAY_QUAL_COLORS[idx])
            text_color = Qt.white if idx == 0 else Qt.black
            
            item.setBackground(QBrush(bg_color))
            item.setForeground(QBrush(text_color))
            
            self.table.setItem(target_row, col, item)
            
        self.table.setUpdatesEnabled(True)

    def pam_to_date(self, pam_day):
        base = datetime(2005, 12, 31)
        target = base + timedelta(days=float(pam_day))
        return target.strftime('%Y-%m-%d')

    def on_cell_clicked(self, row, col):
        item = self.table.item(row, col)
        if item:
            pam_day = item.data(Qt.UserRole)
            self.selected_day = pam_day
            date_str = self.pam_to_date(pam_day)
            
            html = f"<h3>Day {pam_day}</h3>Date: <b>{date_str}</b><br><hr>"
            
            # Bartels
            if self.bartels_data:
                # MATLAB: find(curpamday-BN.pamdays>=0) -> last index
                # Python: searchsorted возвращает индекс вставки, берем предыдущий
                idx = np.searchsorted(self.bartels_data['days'], pam_day, side='right') - 1
                if idx >= 0:
                    bn = self.bartels_data['bn'][idx]
                    html += f"Bartels period: <b>{bn}</b><br>"
            
            # Carrington
            if self.carrington_data:
                idx = np.searchsorted(self.carrington_data['days'], pam_day, side='right') - 1
                if idx >= 0:
                    cn = self.carrington_data['cn'][idx]
                    html += f"Carrington period: <b>{cn}</b><br>"
            
            self.info_box.setText(html)
            self.btn_set_start.setEnabled(True)
            self.btn_set_end.setEnabled(True)
        else:
            self.selected_day = None
            self.info_box.setText("-")
            self.btn_set_start.setEnabled(False)
            self.btn_set_end.setEnabled(False)

    def on_set_start(self):
        if self.selected_day:
            self.app_state.pam_pers = [self.selected_day]
            QMessageBox.information(self, "Info", f"Day {self.selected_day} set as START")
    
    def on_set_end(self):
        if self.selected_day and self.app_state.pam_pers:
            start = self.app_state.pam_pers[0]
            if self.selected_day >= start:
                self.app_state.pam_pers = list(range(start, self.selected_day + 1))
                QMessageBox.information(self, "Info", f"Range set: {start} - {self.selected_day}")
