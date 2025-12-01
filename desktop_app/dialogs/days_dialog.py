"""
Порт ShowDays из pan03_set02_Pamdays.m
SMART EDITION: ОПТИМИЗИРОВАННЫЙ (Fast Loading)
"""
import os
import numpy as np
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem,
                             QPushButton, QHBoxLayout, QHeaderView, QLabel, QWidget,
                             QComboBox, QFrame, QAbstractItemView, QMessageBox)
from PyQt5.QtGui import QColor, QBrush
from PyQt5.QtCore import Qt
from core import config
from core.state import ApplicationState

# Цвета качества
DAY_QUAL_COLORS = [
    '#3d3339', '#80df20', '#e1d81a', '#ffffff', 
    '#ec614b', '#ffffff', '#ecb245', '#63eae8'
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
        self.row_map_cache = {} # Кэш для быстрого поиска строк
        
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
        self.combo_color_mode.currentIndexChanged.connect(self.refresh_table_colors)
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
        
        # Загрузка данных (Оптимизирована)
        self.load_data()
        self.load_mag_data() # <-- Теперь это быстро
        
        self.info_box.setText("Select a day to see details...")
        self.update_legend()

    def setup_table(self):
        self.table.setColumnCount(31)
        self.table.setHorizontalHeaderLabels([str(i) for i in range(1, 32)])
        
        months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
        row_labels = []
        self.row_map_cache = {} # Очищаем кэш
        
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
        """Загружает Tbinning_day.mat."""
        path = os.path.join(config.BASE_DATA_PATH, 'UserBinnings', 'Tbinning_day.mat')
        mat = config._load_mat_file(path)
        if not mat: return

        try:
            t_bins = np.array(mat['Tbins']).flatten()
            day_qual = np.array(mat['DayQuality']).flatten()
            
            # Заполняем карту
            for i, pam_day in enumerate(t_bins):
                self.day_quality_map[int(pam_day)] = int(day_qual[i])
                
            self.refresh_table_colors()
        except Exception as e:
            print(f"Error loading Tbinning: {e}")

    def load_mag_data(self):
        """
        Загружает MagParam2.mat.
        ОПТИМИЗАЦИЯ: Используем быструю индексацию вместо цикла for-loop.
        """
        path = os.path.join(config.BASE_DATA_PATH, 'SolarHelioParams', 'MagParam2.mat')
        mat = config._load_mat_file(path)
        if not mat: 
            print("MagParam2.mat not found.")
            return

        try:
            print("Optimizing MagParam data processing...")
            unixtime = np.array(mat['unixtime']).flatten()
            kp = np.array(mat['Kp']).flatten()
            dst = np.array(mat['Dst']).flatten()
            f10 = np.array(mat['f10p7']).flatten()
            
            # 1. Вычисляем дни PAMELA (векторизованно)
            base_unix = datetime(2005, 12, 31).timestamp()
            pam_days_all = np.floor((unixtime - base_unix) / 86400.0).astype(int)
            
            # 2. Сортируем данные по дням (это позволяет использовать reduceat)
            sort_idx = np.argsort(pam_days_all)
            pam_days_sorted = pam_days_all[sort_idx]
            kp_sorted = kp[sort_idx]
            dst_sorted = dst[sort_idx]
            f10_sorted = f10[sort_idx]
            
            # 3. Находим границы дней (индексы, где меняется день)
            # unique_days - уникальные значения
            # change_indices - индексы начала каждого нового дня в отсортированном массиве
            unique_days, change_indices = np.unique(pam_days_sorted, return_index=True)
            
            # 4. Используем reduceat для быстрой агрегации (ufunc.reduceat)
            # Это в сотни раз быстрее цикла
            
            # Max Kp
            kp_max = np.maximum.reduceat(kp_sorted, change_indices)
            # Min Dst
            dst_min = np.minimum.reduceat(dst_sorted, change_indices)
            # Mean F10.7 (add.reduceat / count)
            f10_sum = np.add.reduceat(f10_sorted, change_indices)
            # Кол-во точек в каждом дне (diff индексов)
            # Добавляем длину массива в конец для вычисления последнего интервала
            indices_diff = np.diff(np.append(change_indices, len(pam_days_sorted)))
            f10_mean = f10_sum / indices_diff
            
            # 5. Заполняем словарь (это быстро, так как дней всего ~3-4 тыс)
            # Фильтруем только те дни, которые есть в миссии PAMELA (для экономии памяти)
            mission_days = set(self.day_quality_map.keys())
            
            for i, day in enumerate(unique_days):
                d_int = int(day)
                if d_int in mission_days:
                    self.mag_data_map[d_int] = {
                        'Kp': kp_max[i],
                        'Dst': dst_min[i],
                        'F10.7': f10_mean[i]
                    }
            
            print(f"Loaded MagParam2 fast! Processed {len(self.mag_data_map)} relevant days.")
            
        except Exception as e:
            print(f"Error processing MagParam2: {e}")
            import traceback
            traceback.print_exc()

    def refresh_table_colors(self):
        """Перерисовывает таблицу. Отключает обновления для скорости."""
        self.table.setUpdatesEnabled(False) # <--- Блокировка отрисовки
        try:
            mode = self.combo_color_mode.currentIndex()
            self.update_legend()
            self.table.clearContents()
            
            # Проходим по дням
            for pam_day, qual in self.day_quality_map.items():
                # Быстрая конвертация даты
                date_str = self.pam_to_date(pam_day)
                try: 
                    # Парсинг вручную быстрее чем strptime
                    y, m, d = map(int, date_str.split('-'))
                except: continue
                
                # Быстрый поиск строки через кэш
                target_row = self.row_map_cache.get((y, m), -1)
                if target_row == -1: continue
                
                col = d - 1
                item = QTableWidgetItem(str(pam_day))
                item.setTextAlignment(Qt.AlignCenter)
                item.setData(Qt.UserRole, pam_day)
                
                bg_color = Qt.white
                text_color = Qt.black
                
                if mode == 0: # Quality
                    idx = qual if qual < len(DAY_QUAL_COLORS) else 0
                    bg_color = QColor(DAY_QUAL_COLORS[idx])
                    if idx == 0: text_color = Qt.white
                    
                elif mode == 1: # Kp Index
                    if pam_day in self.mag_data_map:
                        bg_color = get_kp_color(self.mag_data_map[pam_day]['Kp'])
                    else:
                        bg_color = QColor('#eeeeee')
                        
                elif mode == 2: # F10.7 (Solar)
                    if pam_day in self.mag_data_map:
                        f10 = self.mag_data_map[pam_day]['F10.7']
                        if np.isnan(f10):
                             bg_color = QColor('#eeeeee')
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
            self.table.setUpdatesEnabled(True) # <--- Разблокировка

    def update_legend(self):
        # Очистка легенды
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
                kp = mag['Kp']
                kp_col = get_kp_color(kp).name()
                dst = mag['Dst']
                dst_col = "red" if dst < -50 else "black"
                f10 = mag['F10.7']
                
                html += f"Geomag (Kp max): <span style='background-color:{kp_col}; padding:2px;'><b>{kp:.1f}</b></span><br>"
                html += f"Dst min: <span style='color:{dst_col}'><b>{dst:.0f} nT</b></span><br>"
                html += f"Solar F10.7: <b>{f10:.1f}</b> sfu"
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
            QMessageBox.information(self, "Info", f"Day {self.selected_day} set as START")
    
    def on_set_end(self):
        if self.selected_day and self.app_state.pam_pers:
            start = self.app_state.pam_pers[0]
            if self.selected_day >= start:
                self.app_state.pam_pers = list(range(start, self.selected_day + 1))
                QMessageBox.information(self, "Info", f"Range set: {start} - {self.selected_day}")
