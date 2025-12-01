"""
Порт ShowDays из pan03_set02_Pamdays.m
SMART EDITION: С интеграцией Космической Погоды (MagParam2).
"""
import os
import numpy as np
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem,
                             QPushButton, QHBoxLayout, QHeaderView, QLabel, QWidget,
                             QComboBox, QFrame, QScrollArea, QAbstractItemView, QMessageBox) # <--- ДОБАВЛЕНЫ ИМПОРТЫ
from PyQt5.QtGui import QColor, QBrush, QFont
from PyQt5.QtCore import Qt
from core import config
from core.state import ApplicationState

# Цвета качества (Original)
DAY_QUAL_COLORS = [
    '#3d3339', '#80df20', '#e1d81a', '#ffffff', 
    '#ec614b', '#ffffff', '#ecb245', '#63eae8'
]

# Цвета для Kp индекса (Space Weather)
def get_kp_color(kp):
    if kp < 3: return QColor('#80df20') # Quiet
    if kp < 5: return QColor('#e1d81a') # Unsettled
    if kp < 7: return QColor('#ecb245') # Storm
    return QColor('#ec614b')            # Severe Storm

class DaysDialog(QDialog):
    
    def __init__(self, app_state: ApplicationState, parent=None):
        super().__init__(parent)
        self.app_state = app_state
        self.selected_day = None
        
        # Данные
        self.day_quality_map = {} 
        self.mag_data_map = {}    
        
        self.setWindowTitle("Mission Timeline & Space Weather")
        self.setGeometry(100, 100, 1200, 750)
        
        main_layout = QHBoxLayout()
        self.setLayout(main_layout)
        
        # --- ЛЕВАЯ ПАНЕЛЬ ---
        left_panel = QWidget()
        left_panel.setFixedWidth(320)
        left_layout = QVBoxLayout()
        left_panel.setLayout(left_layout)
        
        # 1. Color Mode
        left_layout.addWidget(QLabel("<b>Color Mode:</b>"))
        self.combo_color_mode = QComboBox()
        self.combo_color_mode.addItems(["Instrument Quality", "Geomagnetic Activity (Kp)", "Solar Activity (F10.7)"])
        self.combo_color_mode.currentIndexChanged.connect(self.refresh_table_colors)
        left_layout.addWidget(self.combo_color_mode)
        
        # Легенда
        self.legend_widget = QWidget()
        self.legend_layout = QVBoxLayout()
        self.legend_layout.setContentsMargins(0,0,0,0)
        self.legend_widget.setLayout(self.legend_layout)
        left_layout.addWidget(self.legend_widget)
        
        # Разделитель
        line = QFrame(); line.setFrameShape(QFrame.HLine); line.setFrameShadow(QFrame.Sunken)
        left_layout.addWidget(line)
        
        # 2. Инфо
        self.info_box = QLabel("Select a day to see details...")
        self.info_box.setWordWrap(True)
        self.info_box.setStyleSheet("background-color: #f0f0f0; padding: 10px; border-radius: 5px;")
        font = self.info_box.font(); font.setPointSize(11); self.info_box.setFont(font)
        left_layout.addWidget(self.info_box)
        
        left_layout.addStretch()
        
        # 3. Кнопки
        self.btn_set_start = QPushButton("Set as START")
        self.btn_set_end = QPushButton("Set as END")
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
        
        # Инициализация
        self.load_data()
        self.load_mag_data() 
        self.update_legend()

    def setup_table(self):
        self.table.setColumnCount(31)
        self.table.setHorizontalHeaderLabels([str(i) for i in range(1, 32)])
        
        months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
        row_labels = []
        self.row_map = [] 
        
        for year in range(2006, 2017):
            start_m = 6 if year == 2006 else 1
            end_m = 1 if year == 2016 else 12
            for m in range(start_m, end_m + 1):
                row_labels.append(f"{year} {months[m-1]}")
                self.row_map.append((year, m))
        
        self.table.setRowCount(len(row_labels))
        self.table.setVerticalHeaderLabels(row_labels)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        
        # Исправлено: теперь QAbstractItemView импортирован
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)

    def load_data(self):
        path = os.path.join(config.BASE_DATA_PATH, 'UserBinnings', 'Tbinning_day.mat')
        mat = config._load_mat_file(path)
        if not mat: return

        try:
            t_bins = np.array(mat['Tbins']).flatten()
            day_qual = np.array(mat['DayQuality']).flatten()
            
            for i, pam_day in enumerate(t_bins):
                self.day_quality_map[int(pam_day)] = int(day_qual[i])
            
            self.refresh_table_colors()
        except Exception as e:
            print(f"Error loading Tbinning: {e}")

    def load_mag_data(self):
        path = os.path.join(config.BASE_DATA_PATH, 'SolarHelioParams', 'MagParam2.mat')
        mat = config._load_mat_file(path)
        if not mat: return

        try:
            unixtime = np.array(mat['unixtime']).flatten()
            kp = np.array(mat['Kp']).flatten()
            dst = np.array(mat['Dst']).flatten()
            f10 = np.array(mat['f10p7']).flatten()
            
            base_unix = datetime(2005, 12, 31).timestamp()
            pam_days_mag = (unixtime - base_unix) / 86400.0
            pam_days_int = np.floor(pam_days_mag).astype(int)
            
            unique_days = np.unique(pam_days_int)
            
            for day in unique_days:
                mask = (pam_days_int == day)
                if not np.any(mask): continue
                
                day_kp = np.max(kp[mask]) 
                day_dst = np.min(dst[mask])
                day_f10 = np.mean(f10[mask])
                
                self.mag_data_map[int(day)] = {'Kp': day_kp, 'Dst': day_dst, 'F10.7': day_f10}
            print(f"Loaded MagParam2 for {len(self.mag_data_map)} days.")
        except Exception as e:
            print(f"Error processing MagParam2: {e}")

    def refresh_table_colors(self):
        mode = self.combo_color_mode.currentIndex()
        self.update_legend()
        self.table.clearContents()
        
        for pam_day, qual in self.day_quality_map.items():
            date_str = self.pam_to_date(pam_day)
            try: dt = datetime.strptime(date_str, '%Y-%m-%d')
            except: continue
            
            target_row = -1
            for r_idx, (y, m) in enumerate(self.row_map):
                if y == dt.year and m == dt.month:
                    target_row = r_idx; break
            if target_row == -1: continue
            
            col = dt.day - 1
            item = QTableWidgetItem(str(pam_day))
            item.setTextAlignment(Qt.AlignCenter)
            item.setData(Qt.UserRole, pam_day)
            
            bg_color = Qt.white
            text_color = Qt.black
            
            if mode == 0: # Quality
                if qual < len(DAY_QUAL_COLORS): bg_color = QColor(DAY_QUAL_COLORS[qual])
                if qual == 0: text_color = Qt.white
            elif mode == 1: # Kp
                if pam_day in self.mag_data_map: bg_color = get_kp_color(self.mag_data_map[pam_day]['Kp'])
                else: bg_color = QColor('#eeeeee')
            elif mode == 2: # F10.7
                if pam_day in self.mag_data_map:
                    f10 = self.mag_data_map[pam_day]['F10.7']
                    norm = min(max((f10 - 70) / 130.0, 0.0), 1.0)
                    hue = (1.0 - norm) * 0.66 
                    bg_color = QColor.fromHsvF(hue, 0.7, 0.9)
                else: bg_color = QColor('#eeeeee')

            item.setBackground(QBrush(bg_color))
            item.setForeground(QBrush(text_color))
            self.table.setItem(target_row, col, item)

    def update_legend(self):
        while self.legend_layout.count():
            child = self.legend_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()
        mode = self.combo_color_mode.currentIndex()
        if mode == 0: 
            self.add_legend_item(self.legend_layout, "Good Data", DAY_QUAL_COLORS[1])
            self.add_legend_item(self.legend_layout, "Tracker/Calo Issue", DAY_QUAL_COLORS[4])
        elif mode == 1: 
            self.add_legend_item(self.legend_layout, "Quiet (Kp < 3)", '#80df20')
            self.add_legend_item(self.legend_layout, "Storm (Kp 5-6)", '#ecb245')
            self.add_legend_item(self.legend_layout, "Severe (Kp 7+)", '#ec614b')
        elif mode == 2:
            self.add_legend_item(self.legend_layout, "Low Activity (Blue)", '#0000ff', "white")
            self.add_legend_item(self.legend_layout, "High Activity (Red)", '#ff0000', "white")

    def add_legend_item(self, layout, text, color_hex, text_color="black"):
        lbl = QLabel(text)
        lbl.setStyleSheet(f"background-color: {color_hex}; color: {text_color}; border-radius: 3px; padding: 2px;")
        layout.addWidget(lbl)

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
            html = f"<h3>Day {pam_day}</h3>Date: <b>{date_str}</b><br><br>"
            
            if pam_day in self.mag_data_map:
                mag = self.mag_data_map[pam_day]
                kp_col = get_kp_color(mag['Kp']).name()
                dst_col = "red" if mag['Dst'] < -50 else "black"
                html += f"Geomag (Kp max): <span style='background-color:{kp_col}; padding:2px;'><b>{mag['Kp']:.1f}</b></span><br>"
                html += f"Dst min: <span style='color:{dst_col}'><b>{mag['Dst']:.0f} nT</b></span><br>"
                html += f"Solar F10.7: <b>{mag['F10.7']:.1f}</b> sfu"
            else: html += "<i>No Space Weather data</i>"
            
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
            # Исправлено: теперь QMessageBox импортирован
            QMessageBox.information(self, "Info", f"Day {self.selected_day} set as START")
    
    def on_set_end(self):
        if self.selected_day and self.app_state.pam_pers:
            start = self.app_state.pam_pers[0]
            if self.selected_day >= start:
                self.app_state.pam_pers = list(range(start, self.selected_day + 1))
                QMessageBox.information(self, "Info", f"Range set: {start} - {self.selected_day}")
