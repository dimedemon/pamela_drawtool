"""
Порт ShowDays из pan03_set02_Pamdays.m
Интерактивный календарь дней PAMELA.
"""
import os
import numpy as np
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem,
                             QPushButton, QHBoxLayout, QHeaderView, QLabel, QWidget,
                             QAbstractItemView, QMessageBox)
from PyQt5.QtGui import QColor, QBrush
from PyQt5.QtCore import Qt
from core import config
from core.state import ApplicationState

# Цвета из MATLAB (DayQualColours)
# 0: OFF, 1: Good, 2: Short, 4: Tracker OFF, 6: Orient missed, 7: Calo OFF
DAY_QUAL_COLORS = [
    '#3d3339', '#80df20', '#e1d81a', '#ffffff', 
    '#ec614b', '#ffffff', '#ecb245', '#63eae8'
]

class DaysDialog(QDialog):
    
    def __init__(self, app_state: ApplicationState, parent=None):
        super().__init__(parent)
        self.app_state = app_state
        self.selected_day = None
        
        self.setWindowTitle("Days Data (Calendar)")
        self.setGeometry(100, 100, 1100, 700)
        
        main_layout = QHBoxLayout()
        self.setLayout(main_layout)
        
        # --- Левая панель (Легенда и Инфо) ---
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        left_panel.setLayout(left_layout)
        left_panel.setFixedWidth(280)
        
        left_layout.addWidget(QLabel("<b>Day Quality Legend:</b>"))
        self.add_legend_item(left_layout, "PAMELA OFF", DAY_QUAL_COLORS[0], "white")
        self.add_legend_item(left_layout, "Good Data", DAY_QUAL_COLORS[1])
        self.add_legend_item(left_layout, "Short File", DAY_QUAL_COLORS[2])
        self.add_legend_item(left_layout, "Tracker OFF", DAY_QUAL_COLORS[4])
        self.add_legend_item(left_layout, "Orientation Missed", DAY_QUAL_COLORS[6])
        self.add_legend_item(left_layout, "Calo OFF", DAY_QUAL_COLORS[7])
        
        left_layout.addSpacing(20)
        left_layout.addWidget(QLabel("<b>Solar Info:</b>"))
        self.lbl_solar_info = QLabel("-")
        left_layout.addWidget(self.lbl_solar_info)
        
        left_layout.addStretch()
        
        # Информация о выбранном дне
        self.lbl_selection_info = QLabel("Select a day in the table...")
        self.lbl_selection_info.setWordWrap(True)
        self.lbl_selection_info.setStyleSheet("font-size: 14px; font-weight: bold;")
        left_layout.addWidget(self.lbl_selection_info)
        
        left_layout.addSpacing(10)
        
        # Кнопки установки
        self.btn_set_start = QPushButton("Set as START day")
        self.btn_set_end = QPushButton("Set as END day")
        self.btn_set_start.setEnabled(False)
        self.btn_set_end.setEnabled(False)
        
        self.btn_set_start.clicked.connect(self.on_set_start)
        self.btn_set_end.clicked.connect(self.on_set_end)
        
        left_layout.addWidget(self.btn_set_start)
        left_layout.addWidget(self.btn_set_end)
        
        main_layout.addWidget(left_panel)
        
        # --- Правая панель (Таблица) ---
        self.table = QTableWidget()
        self.setup_table()
        self.table.cellClicked.connect(self.on_cell_clicked)
        main_layout.addWidget(self.table)
        
        # Загрузка данных
        self.load_data()

    def setup_table(self):
        """Настраивает сетку таблицы (Месяцы x Дни)."""
        self.table.setColumnCount(31)
        self.table.setHorizontalHeaderLabels([str(i) for i in range(1, 32)])
        
        months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
        row_labels = []
        self.row_map = [] # (year, month) для каждой строки
        
        # 2006 (Jun-Dec)
        for m in range(6, 13):
            row_labels.append(f"2006 {months[m-1]}")
            self.row_map.append((2006, m))
            
        # 2007-2015
        for year in range(2007, 2016):
            for m in range(1, 13):
                row_labels.append(f"{year} {months[m-1]}")
                self.row_map.append((year, m))
        
        # 2016 Jan
        row_labels.append("2016 Jan")
        self.row_map.append((2016, 1))
        
        self.table.setRowCount(len(row_labels))
        self.table.setVerticalHeaderLabels(row_labels)
        
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)

    def add_legend_item(self, layout, text, color_hex, text_color="black"):
        lbl = QLabel(text)
        lbl.setStyleSheet(f"background-color: {color_hex}; color: {text_color}; border: 1px solid gray; padding: 4px;")
        layout.addWidget(lbl)

    def load_data(self):
        """Загружает Tbinning_day.mat и раскрашивает таблицу."""
        path = os.path.join(config.BASE_DATA_PATH, 'UserBinnings', 'Tbinning_day.mat')
        
        try:
            mat = config._load_mat_file(path)
            if mat is None:
                self.lbl_selection_info.setText(f"Error: {path} not found.")
                return

            # В MATLAB: A.Tbins (номера дней), A.DayQuality (качество)
            # При загрузке через scipy.io.loadmat с struct_as_record=False:
            # mat['Tbins'] может быть массивом внутри массива
            
            # Получаем данные и приводим к плоскому виду
            t_bins = np.array(mat['Tbins']).flatten()
            day_qual = np.array(mat['DayQuality']).flatten()
            
            for i, pam_day in enumerate(t_bins):
                qual = int(day_qual[i])
                if qual >= len(DAY_QUAL_COLORS): qual = 0
                
                date_str = self.pam_to_date(pam_day)
                try:
                    dt = datetime.strptime(date_str, '%Y-%m-%d')
                except: continue
                
                # Ищем строку
                target_row = -1
                for r_idx, (y, m) in enumerate(self.row_map):
                    if y == dt.year and m == dt.month:
                        target_row = r_idx
                        break
                
                if target_row != -1:
                    col = dt.day - 1
                    item = QTableWidgetItem(str(int(pam_day)))
                    item.setTextAlignment(Qt.AlignCenter)
                    
                    bg_color = QColor(DAY_QUAL_COLORS[qual])
                    item.setBackground(QBrush(bg_color))
                    
                    if qual == 0: # Темный фон -> белый текст
                        item.setForeground(QBrush(Qt.white))
                    
                    item.setData(Qt.UserRole, int(pam_day)) # Храним номер дня
                    self.table.setItem(target_row, col, item)
                    
        except Exception as e:
            print(f"Error loading calendar: {e}")
            self.lbl_selection_info.setText(f"Error loading data: {e}")

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
            self.lbl_selection_info.setText(
                f"Day Number: <b>{pam_day}</b><br>"
                f"Date: <b>{date_str}</b>"
            )
            
            # Загружаем Bartels/Carrington (если файлы есть)
            self.load_solar_info(pam_day)
            
            self.btn_set_start.setEnabled(True)
            self.btn_set_end.setEnabled(True)
        else:
            self.selected_day = None
            self.lbl_selection_info.setText("No data for this date.")
            self.lbl_solar_info.setText("-")
            self.btn_set_start.setEnabled(False)
            self.btn_set_end.setEnabled(False)

    def load_solar_info(self, pam_day):
        """Загружает информацию о циклах Бартельса и Кэррингтона."""
        try:
            bart_path = os.path.join(config.BASE_DATA_PATH, 'SolarHelioParams', 'Bartels.mat')
            carr_path = os.path.join(config.BASE_DATA_PATH, 'SolarHelioParams', 'Carrington.mat')
            
            b_mat = config._load_mat_file(bart_path)
            c_mat = config._load_mat_file(carr_path)
            
            info = ""
            if b_mat:
                # Простая логика поиска (упрощенно)
                # В MATLAB: find(curpamday-BN.pamdays>=0)
                b_days = np.array(b_mat['pamdays']).flatten()
                b_nums = np.array(b_mat['BN']).flatten()
                idx = np.where(pam_day - b_days >= 0)[0]
                if len(idx) > 0:
                    info += f"Bartels: {b_nums[idx[-1]]}<br>"
            
            if c_mat:
                c_days = np.array(c_mat['pamdays']).flatten()
                c_nums = np.array(c_mat['CN']).flatten()
                idx = np.where(pam_day - c_days >= 0)[0]
                if len(idx) > 0:
                    info += f"Carrington: {c_nums[idx[-1]]}"
            
            self.lbl_solar_info.setText(info if info else "No solar info")
            
        except Exception:
            self.lbl_solar_info.setText("(Solar info error)")

    def on_set_start(self):
        if self.selected_day:
            self.app_state.pam_pers = [self.selected_day]
            self.lbl_selection_info.setText(f"Day {self.selected_day} set as START")

    def on_set_end(self):
        if self.selected_day:
            current = self.app_state.pam_pers
            if not current:
                QMessageBox.warning(self, "Error", "Set start day first!")
                return
            
            start_day = current[0]
            if self.selected_day < start_day:
                QMessageBox.warning(self, "Error", "End day must be >= Start day")
                return
                
            new_range = list(range(start_day, self.selected_day + 1))
            self.app_state.pam_pers = new_range
            self.lbl_selection_info.setText(f"Range set: {start_day} - {self.selected_day}<br>({len(new_range)} days)")
