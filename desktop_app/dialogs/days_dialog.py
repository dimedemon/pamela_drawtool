"""
Порт ShowDays из pan03_set02_Pamdays.m
SMART EDITION: С интеграцией Космической Погоды (MagParam2).
"""
import os
import numpy as np
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem,
                             QPushButton, QHBoxLayout, QHeaderView, QLabel, QWidget,
                             QComboBox, QFrame, QScrollArea)
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
# 0-2 (Green), 3-4 (Yellow), 5-6 (Orange), 7+ (Red)
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
        self.day_quality_map = {} # pam_day -> quality
        self.mag_data_map = {}    # pam_day -> {Kp, Dst, F10.7}
        
        self.setWindowTitle("Mission Timeline & Space Weather")
        self.setGeometry(100, 100, 1200, 750)
        
        main_layout = QHBoxLayout()
        self.setLayout(main_layout)
        
        # --- ЛЕВАЯ ПАНЕЛЬ (Инфо и Настройки) ---
        left_panel = QWidget()
        left_panel.setFixedWidth(320)
        left_layout = QVBoxLayout()
        left_panel.setLayout(left_layout)
        
        # 1. Color Mode Selector
        left_layout.addWidget(QLabel("<b>Color Mode:</b>"))
        self.combo_color_mode = QComboBox()
        self.combo_color_mode.addItems(["Instrument Quality", "Geomagnetic Activity (Kp)", "Solar Activity (F10.7)"])
        self.combo_color_mode.currentIndexChanged.connect(self.refresh_table_colors)
        left_layout.addWidget(self.combo_color_mode)
        
        # Легенда (динамическая)
        self.legend_widget = QWidget()
        self.legend_layout = QVBoxLayout()
        self.legend_layout.setContentsMargins(0,0,0,0)
        self.legend_widget.setLayout(self.legend_layout)
        left_layout.addWidget(self.legend_widget)
        
        # Разделитель
        line = QFrame(); line.setFrameShape(QFrame.HLine); line.setFrameShadow(QFrame.Sunken)
        left_layout.addWidget(line)
        
        # 2. Информация о дне (Space Weather Dashboard)
        self.info_box = QLabel("Select a day to see details...")
        self.info_box.setWordWrap(True)
        self.info_box.setStyleSheet("background-color: #f0f0f0; padding: 10px; border-radius: 5px;")
        font = self.info_box.font(); font.setPointSize(11); self.info_box.setFont(font)
        left_layout.addWidget(self.info_box)
        
        left_layout.addStretch()
        
        # 3. Кнопки выбора
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
        self.load_mag_data() # <-- Загрузка MagParam2
        self.update_legend()

    def setup_table(self):
        self.table.setColumnCount(31)
        self.table.setHorizontalHeaderLabels([str(i) for i in range(1, 32)])
        
        months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
        row_labels = []
        self.row_map = [] 
        
        # Создаем строки с 2006 по 2016
        for year in range(2006, 2017):
            start_m = 6 if year == 2006 else 1
            end_m = 1 if year == 2016 else 12
            for m in range(start_m, end_m + 1):
                row_labels.append(f"{year} {months[m-1]}")
                self.row_map.append((year, m))
        
        self.table.setRowCount(len(row_labels))
        self.table.setVerticalHeaderLabels(row_labels)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)

    def load_data(self):
        """Загружает Tbinning_day.mat (Качество данных)."""
        path = os.path.join(config.BASE_DATA_PATH, 'UserBinnings', 'Tbinning_day.mat')
        mat = config._load_mat_file(path)
        if not mat: return

        try:
            t_bins = np.array(mat['Tbins']).flatten()
            day_qual = np.array(mat['DayQuality']).flatten()
            
            for i, pam_day in enumerate(t_bins):
                self.day_quality_map[int(pam_day)] = int(day_qual[i])
                
            # Первичная отрисовка (Quality по умолчанию)
            self.refresh_table_colors()
            
        except Exception as e:
            print(f"Error loading Tbinning: {e}")

    def load_mag_data(self):
        """Загружает MagParam2.mat (Космическая погода)."""
        path = os.path.join(config.BASE_DATA_PATH, 'SolarHelioParams', 'MagParam2.mat')
        mat = config._load_mat_file(path)
        if not mat: 
            print("MagParam2.mat not found.")
            return

        try:
            # Данные в MagParam2 обычно идут по времени (unixtime)
            # Нам нужно сопоставить их с днями PAMELA
            # PAMSTART (Juliandate) -> Unix Timestamp
            
            # Упрощенно: создадим карту для быстрого доступа
            # Предполагаем, что массивы Kp, Dst, Ap, f10p7, unixtime одинаковой длины
            unixtime = np.array(mat['unixtime']).flatten()
            kp = np.array(mat['Kp']).flatten()
            dst = np.array(mat['Dst']).flatten()
            f10 = np.array(mat['f10p7']).flatten()
            
            # Конвертация времени (Векторизованная, для скорости)
            # 1 день = 86400 сек.
            # PAMSTART (JD) ~ 2005-12-31
            base_unix = datetime(2005, 12, 31).timestamp()
            
            # Вычисляем номер дня PAMELA для каждой точки в MagParam
            pam_days_mag = (unixtime - base_unix) / 86400.0
            pam_days_int = np.floor(pam_days_mag).astype(int)
            
            # Агрегируем данные по дням (берем max Kp и min Dst за день)
            # Это может занять время, поэтому лучше делать умно
            
            # Пройдемся по уникальным дням
            unique_days = np.unique(pam_days_int)
            
            for day in unique_days:
                mask = (pam_days_int == day)
                if not np.any(mask): continue
                
                # Берем статистику за день
                day_kp = np.max(kp[mask]) # Max Kp за день (шторм?)
                day_dst = np.min(dst[mask]) # Min Dst (глубина шторма)
                day_f10 = np.mean(f10[mask]) # Средний F10.7
                
                self.mag_data_map[int(day)] = {
                    'Kp': day_kp,
                    'Dst': day_dst,
                    'F10.7': day_f10
                }
            print(f"Loaded MagParam2 for {len(self.mag_data_map)} days.")
            
        except Exception as e:
            print(f"Error processing MagParam2: {e}")

    def refresh_table_colors(self):
        """Перерисовывает таблицу в зависимости от выбранного режима."""
        mode = self.combo_color_mode.currentIndex()
        self.update_legend()
        
        # Очищаем/Заполняем таблицу
        # (Для оптимизации лучше обновлять только цвета, но пересоздадим итемы для надежности)
        self.table.clearContents()
        
        # Проходим по всем дням, для которых у нас есть данные (QualityMap - база)
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
                if qual < len(DAY_QUAL_COLORS):
                    bg_color = QColor(DAY_QUAL_COLORS[qual])
                if qual == 0: text_color = Qt.white
                
            elif mode == 1: # Kp Index
                if pam_day in self.mag_data_map:
                    kp = self.mag_data_map[pam_day]['Kp']
                    bg_color = get_kp_color(kp)
                else:
                    bg_color = QColor('#eeeeee') # Нет данных
                    
            elif mode == 2: # F10.7 (Solar)
                if pam_day in self.mag_data_map:
                    f10 = self.mag_data_map[pam_day]['F10.7']
                    # Градиент синий -> красный (70 -> 200+)
                    norm = min(max((f10 - 70) / 130.0, 0.0), 1.0)
                    # Простой heat map (Blue -> Red)
                    hue = (1.0 - norm) * 0.66 # 0.66=Blue, 0.0=Red
                    bg_color = QColor.fromHsvF(hue, 0.7, 0.9)
                else:
                    bg_color = QColor('#eeeeee')

            item.setBackground(QBrush(bg_color))
            item.setForeground(QBrush(text_color
