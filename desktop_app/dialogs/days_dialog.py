"""
Порт ShowDays из pan03_set02_Pamdays.m
SMART EDITION:
- Полная расшифровка цветов (Legend).
- Ленивая загрузка MagParam (не вешает старт).
- Оптимизация циклов даты.
"""
import os
import numpy as np
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem,
                             QPushButton, QHBoxLayout, QHeaderView, QLabel, QWidget,
                             QComboBox, QFrame, QAbstractItemView, QMessageBox, QApplication)
from PyQt5.QtGui import QColor, QBrush
from PyQt5.QtCore import Qt
from core import config
from core.state import ApplicationState

# Цвета качества (из MATLAB)
DAY_QUAL_COLORS = [
    '#3d3339', # 0: OFF (Black/Grey)
    '#80df20', # 1: Good (Green)
    '#e1d81a', # 2: Short (Yellow)
    '#ffffff', # 3: Empty
    '#ec614b', # 4: Tracker OFF (Red)
    '#ffffff', # 5: Empty
    '#ecb245', # 6: Orientation Missed (Orange)
    '#63eae8'  # 7: Calo OFF (Cyan)
]

def get_kp_color(kp):
    if np.isnan(kp): return QColor('white')
    if kp < 3: return QColor('#80df20') 
    if kp < 5: return QColor('#e1d81a') 
    if kp < 7: return QColor('#ecb245') 
    return QColor('#ec614b')            

class DaysDialog(QDialog):
    
    def __init__(self, app_state: ApplicationState, parent=None):
        super().__init__(parent)
        self.app_state = app_state
        self.selected_day = None
        
        self.day_quality_map = {} 
        self.mag_data_map = {}
        self.mag_data_loaded = False # Флаг загрузки
        self.row_map_cache = {} 
        
        self.setWindowTitle("Mission Timeline & Space Weather")
        self.setGeometry(100, 100, 1200, 750)
        
        main_layout = QHBoxLayout()
        self.setLayout(main_layout)
        
        # --- ЛЕВАЯ ПАНЕЛЬ ---
        left_panel = QWidget()
        left_panel.setFixedWidth(320)
        left_layout = QVBoxLayout()
        left_panel.setLayout(left_layout)
        
        # Настройки цвета
        left_layout.addWidget(QLabel("<b>Color Mode:</b>"))
        self.combo_color_mode = QComboBox()
        self.combo_color_mode.addItems(["Instrument Quality", "Geomagnetic Activity (Kp)", "Solar Activity (F10.7)"])
        self.combo_color_mode.currentIndexChanged.connect(self.on_mode_changed)
        left_layout.addWidget(self.combo_color_mode)
        
        # Легенда
        self.legend_widget = QWidget()
        self.legend_layout = QVBoxLayout()
        self.legend_layout.setContentsMargins(0,0,0,0)
        self.legend_widget.setLayout(self.legend_layout)
        left_layout.addWidget(self.legend_widget)
        
        line = QFrame(); line.setFrameShape(QFrame.HLine); line.setFrameShadow(QFrame.Sunken)
        left_layout.addWidget(line)
        
        # Инфо
        self.info_box = QLabel("Loading data...")
        self.info_box.setWordWrap(True)
        self.info_box.setStyleSheet("background-color: #f0f0f0; padding: 10px; border-radius: 5px;")
        font = self.info_box.font(); font.setPointSize(11); self.info_box.setFont(font)
        left_layout.addWidget(self.info_box)
        
        left_layout.addStretch()
        
        # Кнопки
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
        
        # Загрузка ТОЛЬКО легких данных (Quality)
        self.load_data()
        
        self.info_box.setText("Select a day to see details...")
        self.update_legend()

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

    def load_data(self):
        """Загружает Tbinning_day.mat (Быстро)."""
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

    def on_mode_changed(self, index):
        """Обработчик смены режима. Загружает MagParam только если нужно."""
        if index > 0 and not self.mag_data_loaded:
            QApplication.setOverrideCursor(Qt.WaitCursor) # Показать часики
            self.info_box.setText("Loading massive Space Weather data... Please wait.")
            QApplication.processEvents() # Обновить UI
            
            self.load_mag_data()
            
            QApplication.restoreOverrideCursor()
            self.info_box.setText("Data loaded. Refreshing...")
            
        self.refresh_table_colors()

    def load_mag_data(self):
        """Загружает MagParam2.mat (Тяжелый файл)."""
        path = os.path.join(config.BASE_DATA_PATH, 'SolarHelioParams', 'MagParam2.mat')
        mat = config._load_mat_file(path)
        if not mat: 
            print("MagParam2.mat not found.")
            self.mag_data_loaded = True # Чтобы не пытаться снова
            return

        try:
            unixtime = np.array(mat['unixtime']).flatten()
            kp = np.array(mat['Kp']).flatten()
            dst = np.array(mat['Dst']).flatten()
            f10 = np.array(mat['f10p7']).flatten()
            
            base_unix = datetime(2005, 12, 31).timestamp()
            # Векторизованное вычисление дней
            pam_days_all = np.floor((unixtime - base_unix) / 86400.0).astype(int)
            
            # Сортировка и агрегация (быстрая)
            sort_idx = np.argsort(pam_days_all)
            pam_days_sorted = pam_days_all[sort_idx]
            unique_days, change_indices = np.unique(pam_days_sorted, return_index=True)
            
            kp_max = np.maximum.reduceat(kp[sort_idx], change_indices)
            dst_min = np.minimum.reduceat(dst[sort_idx], change_indices)
            
            # Для F10.7 (mean)
            f10_sorted = f10[sort_idx]
            f10_sum = np.add.reduceat(f10_sorted, change_indices)
            counts = np.diff(np.append(change_indices, len(pam_days_sorted)))
            f10_mean = f10_sum / counts
            
            mission_days = set(self.day_quality_map.keys())
            for i, day in enumerate(unique_days):
                d_int = int(day)
                if d_int in mission_days:
                    self.mag_data_map[d_int] = {
                        'Kp': kp_max[i],
                        'Dst': dst_min[i],
                        'F10.7': f10_mean[i]
                    }
            
            self.mag_data_loaded = True
            print(f"Loaded MagParam2. Processed {len(self.mag_data_map)} days.")
            
        except Exception as e:
            print(f"Error processing MagParam2: {e}")
            self.mag_data_loaded = True # Блокируем повторные попытки

    def refresh_table_colors(self):
        self.table.setUpdatesEnabled(False)
        try:
            mode = self.combo_color_mode.currentIndex()
            self.update_legend()
            self.table.clearContents()
            
            base_date = datetime(2005, 12, 31)
            
            for pam_day, qual in self.day_quality_map.items():
                # Оптимизированная работа с датой (без strptime)
                dt = base_date + timedelta(days=pam_day)
                
                target_row = self.row_map_cache.get((dt.year, dt.month), -1)
                if target_row == -1: continue
                
                col = dt.day - 1
                item = QTableWidgetItem(str(pam_day))
                item.setTextAlignment(Qt.AlignCenter)
                item.setData(Qt.UserRole, pam_day)
                
                bg_color = Qt.white
                text_color = Qt.black
                
                if mode == 0: # Quality
                    idx = qual if qual < len(DAY_QUAL_COLORS) else 0
                    bg_color = QColor(DAY_QUAL_COLORS[idx])
                    if idx == 0: text_color = Qt.white # OFF = White text
                    
                elif mode == 1: # Kp Index
                    if pam_day in self.mag_data_map:
                        bg_color = get_kp_color(self.mag_data_map[pam_day]['Kp'])
                    else:
                        bg_color = QColor('#eeeeee')
                        
                elif mode == 2: # F10.7
                    if pam_day in self.mag_data_map:
                        f10 = self.mag_data_map[pam_day]['F10.7']
                        if np.isnan(f10): bg_color = QColor('#eeeeee')
                        else:
                             norm = min(max((f10 - 70) / 130.0, 0.0), 1.0)
                             hue = (1.0 - norm) * 0.66 
                             bg_color = QColor.fromHsvF(hue, 0.7, 0.9)
                    else:
                        bg_color = QColor('#eeeeee')

                item.setBackground(QBrush(bg_color))
                item.setForeground(QBrush(text_color))
                self.table.setItem(target_row, col, item)
        finally:
            self.table.setUpdatesEnabled(True)

    def update_legend(self):
        while self.legend_layout.count():
            child = self.legend_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()
            
        mode = self.combo_color_mode.currentIndex()
        
        if mode == 0: # FULL QUALITY LEGEND
            self.add_legend_item(self.legend_layout, "PAMELA OFF (0)", DAY_QUAL_COLORS[0], "white")
            self.add_legend_item(self.legend_layout, "Good Data (1)", DAY_QUAL_COLORS[1])
            self.add_legend_item(self.legend_layout, "Short File (2)", DAY_QUAL_COLORS[2])
            self.add_legend_item(self.legend_layout, "Tracker OFF (4)", DAY_QUAL_COLORS[4])
            self.add_legend_item(self.legend_layout, "Orientation Missed (6)", DAY_QUAL_COLORS[6])
            self.add_legend_item(self.legend_layout, "Calo OFF (7)", DAY_QUAL_COLORS[7])
            
        elif mode == 1: 
            self.add_legend_item(self.legend_layout, "Quiet (Kp < 3)", '#80df20')
            self.add_legend_item(self.legend_layout, "Unsettled (3-4)", '#e1d81a')
            self.add_legend_item(self.legend_layout, "Storm (Kp 5-6)", '#ecb245')
            self.add_legend_item(self.legend_layout, "Severe (Kp 7+)", '#ec614b')
            
        elif mode == 2:
            self.add_legend_item(self.legend_layout, "Low Activity (Blue)", '#0000ff', "white")
            self.add_legend_item(self.legend_layout, "High Activity (Red)", '#ff0000', "white")

    def add_legend_item(self, layout, text, color_hex, text_color="black"):
        lbl = QLabel(text)
        lbl.setStyleSheet(f"background-color: {color_hex}; color: {text_color}; border-radius: 3px; padding: 4px; margin-bottom: 2px;")
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
            html = f"<h3>Day {pam_day}</h3>Date: <b>{date_str}</b><br><hr>"
            
            # Загружаем инфо даже если мы в режиме Quality (если данные загружены)
            # Если не загружены, и пользователь кликнул, можно попытаться загрузить для одного дня (но это сложно),
            # или просто показать "N/A"
            if self.mag_data_loaded and pam_day in self.mag_data_map:
                mag = self.mag_data_map[pam_day]
                kp_col = get_kp_color(mag['Kp']).name()
                dst_col = "red" if mag['Dst'] < -50 else "black"
                
                html += f"<b>Space Weather:</b><br>"
                html += f"Kp max: <span style='background-color:{kp_col}; padding:2px;'><b>{mag['Kp']:.1f}</b></span><br>"
                html += f"Dst min: <span style='color:{dst_col}'><b>{mag['Dst']:.0f} nT</b></span><br>"
                html += f"Solar F10.7: <b>{mag['F10.7']:.1f}</b>"
            elif not self.mag_data_loaded:
                 html += "<i>(Select 'Geomagnetic Activity' to load weather data)</i>"
            else:
                 html += "<i>No Space Weather data available</i>"
            
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
