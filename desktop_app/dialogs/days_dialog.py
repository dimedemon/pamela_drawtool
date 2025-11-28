"""
Порт ShowDays из pan03_set02_Pamdays.m

Интерактивный календарь дней PAMELA.
"""
import os
import numpy as np
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem,
                             QPushButton, QHBoxLayout, QHeaderView, QLabel, QWidget,
                             QGridLayout, QAbstractItemView, QMessageBox)
from PyQt5.QtGui import QColor, QBrush
from PyQt5.QtCore import Qt
from core import config
from core.state import ApplicationState

# Цвета из MATLAB (DayQualColours)
DAY_QUAL_COLORS = [
    '#3d3339', # 0: OFF
    '#80df20', # 1: ON (Good)
    '#e1d81a', # 2: Short
    '#ffffff', # 3: (Empty in matlab?)
    '#ec614b', # 4: Tracker OFF
    '#ffffff', # 5: (Empty?)
    '#ecb245', # 6: Orientation missed
    '#63eae8'  # 7: Calo OFF
]

class DaysDialog(QDialog):
    
    def __init__(self, app_state: ApplicationState, parent=None):
        super().__init__(parent)
        self.app_state = app_state
        self.setWindowTitle("Days Data (Calendar)")
        self.setGeometry(100, 100, 1000, 700) # Большое окно
        
        # Данные биннинга
        self.tbins_data = None
        self.pam_days_map = {} # map[pam_day] -> info
        
        # Основной макет
        main_layout = QHBoxLayout()
        self.setLayout(main_layout)
        
        # --- Левая часть: Легенда и Кнопки ---
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        left_panel.setLayout(left_layout)
        left_panel.setFixedWidth(250)
        
        left_layout.addWidget(QLabel("<b>Day Quality Legend:</b>"))
        self.add_legend_item(left_layout, "PAMELA OFF", DAY_QUAL_COLORS[0], "white")
        self.add_legend_item(left_layout, "Good Data", DAY_QUAL_COLORS[1])
        self.add_legend_item(left_layout, "Short File", DAY_QUAL_COLORS[2])
        self.add_legend_item(left_layout, "Tracker OFF", DAY_QUAL_COLORS[4])
        self.add_legend_item(left_layout, "Orientation Missed", DAY_QUAL_COLORS[6])
        self.add_legend_item(left_layout, "Calo OFF", DAY_QUAL_COLORS[7])
        
        left_layout.addSpacing(20)
        left_layout.addWidget(QLabel("<b>Overlays:</b>"))
        
        # Кнопки оверлеев (пока заглушки)
        self.btn_nof = QPushButton("Show NOF periods")
        self.btn_bartels = QPushButton("Show Bartels")
        self.btn_carrington = QPushButton("Show Carrington")
        
        # TODO: Реализовать логику оверлеев позже
        self.btn_nof.setEnabled(False) 
        self.btn_bartels.setEnabled(False)
        self.btn_carrington.setEnabled(False)
        
        left_layout.addWidget(self.btn_nof)
        left_layout.addWidget(self.btn_bartels)
        left_layout.addWidget(self.btn_carrington)
        
        left_layout.addStretch()
        
        # Информация о выборе
        self.lbl_selection_info = QLabel("Select a day...")
        self.lbl_selection_info.setWordWrap(True)
        left_layout.addWidget(self.lbl_selection_info)
        
        self.btn_set_start = QPushButton("Set as START")
        self.btn_set_end = QPushButton("Set as END")
        self.btn_set_start.setEnabled(False)
        self.btn_set_end.setEnabled(False)
        
        self.btn_set_start.clicked.connect(self.on_set_start)
        self.btn_set_end.clicked.connect(self.on_set_end)
        
        left_layout.addWidget(self.btn_set_start)
        left_layout.addWidget(self.btn_set_end)
        
        main_layout.addWidget(left_panel)
        
        # --- Правая часть: Таблица (Календарь) ---
        self.table = QTableWidget()
        self.setup_table()
        self.table.cellClicked.connect(self.on_cell_clicked)
        main_layout.addWidget(self.table)
        
        # Загрузка данных
        self.load_data()

    def setup_table(self):
        """Настраивает сетку таблицы."""
        # Столбцы: 1-31
        self.table.setColumnCount(31)
        self.table.setHorizontalHeaderLabels([str(i) for i in range(1, 32)])
        
        # Строки: Месяцы с 2006 по 2016
        months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
        row_labels = []
        
        # 2006 (начиная с июля, т.к. старт миссии) или весь год? 
        # В MATLAB цикл: for i=1:7, RowName{i} = ['2006 ' months{i+5}]; end (Июнь-Дек)
        # Но давайте сделаем полные года для простоты, или как в MATLAB
        
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
        
        # Настройки вида
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)

    def add_legend_item(self, layout, text, color_hex, text_color="black"):
        lbl = QLabel(text)
        lbl.setStyleSheet(f"background-color: {color_hex}; color: {text_color}; border: 1px solid gray; padding: 2px;")
        layout.addWidget(lbl)

    def load_data(self):
        """
        Загружает Tbinning_day.mat и заполняет календарь.
        """
        # Путь к файлу: data/UserBinnings/Tbinning_day.mat
        # (Предполагаем, что пользователь положил его туда)
        path = os.path.join(config.BASE_DATA_PATH, 'UserBinnings', 'Tbinning_day.mat')
        
        try:
            mat = config._load_mat_file(path)
            if mat is None:
                # Если файла нет, пробуем найти в корне data/ (для теста)
                path_alt = os.path.join(config.BASE_DATA_PATH, 'Tbinning_day.mat')
                mat = config._load_mat_file(path_alt)
                
            if mat is None:
                self.lbl_selection_info.setText(f"Error: {path} not found.")
                return

            # Извлекаем данные
            # В MATLAB: A.Tbins (номера дней), A.DayQuality (качество)
            t_bins = mat['Tbins']
            day_qual = mat['DayQuality']
            
            # Заполняем таблицу
            for i, pam_day in enumerate(t_bins):
                qual = day_qual[i]
                
                # Конвертируем pam_day в дату
                date_str = self.pam_to_date(pam_day)
                dt = datetime.strptime(date_str, '%Y-%m-%d')
                
                # Ищем строку в таблице
                target_row = -1
                for r_idx, (y, m) in enumerate(self.row_map):
                    if y == dt.year and m == dt.month:
                        target_row = r_idx
                        break
                
                if target_row != -1:
                    col = dt.day - 1 # 0-based
                    
                    item = QTableWidgetItem(str(pam_day))
                    item.setTextAlignment(Qt.AlignCenter)
                    
                    # Цвет
                    bg_color = QColor(DAY_QUAL_COLORS[qual])
                    item.setBackground(QBrush(bg_color))
                    
                    if qual == 0: # OFF - белый текст
                        item.setForeground(QBrush(Qt.white))
                    
                    # Сохраняем данные в ячейку
                    item.setData(Qt.UserRole, pam_day)
                    self.table.setItem(target_row, col, item)
                    
        except Exception as e:
            print(f"Ошибка при загрузке календаря: {e}")
            self.lbl_selection_info.setText(f"Error loading data: {e}")

    def pam_to_date(self, pam_day):
        # Используем нашу логику из config/state
        # PAMSTART = 2005-12-31 (примерно)
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
                f"<h2>Day: {pam_day}</h2>"
                f"Date: {date_str}<br>"
                f"(Quality info available in mat file)"
            )
            
            self.btn_set_start.setEnabled(True)
            self.btn_set_end.setEnabled(True)
            
            # TODO: Здесь можно показать картинку DataCoverage, если она есть
        else:
            self.selected_day = None
            self.btn_set_start.setEnabled(False)
            self.btn_set_end.setEnabled(False)

    def on_set_start(self):
        if self.selected_day:
            # Если список пуст или мы начинаем заново
            self.app_state.pam_pers = [self.selected_day]
            self.lbl_selection_info.setText(f"Start day set to {self.selected_day}")

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
                
            # Создаем диапазон
            new_range = list(range(start_day, self.selected_day + 1))
            self.app_state.pam_pers = new_range
            self.lbl_selection_info.setText(f"Range set: {start_day} - {self.selected_day}")
            # Можно закрыть окно, если нужно
            # self.accept()
