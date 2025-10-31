"""
Порт pan01_set04_sub01_LongPeriods.m

Диалог для выбора "длинных" периодов (month, year и т.д.)
"""
import os
import re
import numpy as np
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem,
                             QPushButton, QHBoxLayout, QAbstractItemView, QHeaderView)
from core import config
from core.state import ApplicationState

class LongPeriodsDialog(QDialog):
    
    def __init__(self, app_state: ApplicationState, parent=None):
        super().__init__(parent)
        
        self.app_state = app_state
        self.selected_period = None
        self.selected_binning_info = None
        
        self.setWindowTitle("Periods Data")
        self.setGeometry(200, 200, 700, 400)
        
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        
        # 1. Таблица
        self.table = QTableWidget()
        main_layout.addWidget(self.table)
        
        # 2. Кнопки
        button_layout = QHBoxLayout()
        self.btn_ok = QPushButton("OK")
        self.btn_ok.setEnabled(False)
        self.btn_ok.clicked.connect(self.on_ok)
        
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject) # reject() закрывает
        
        button_layout.addStretch()
        button_layout.addWidget(self.btn_ok)
        button_layout.addWidget(btn_cancel)
        main_layout.addLayout(button_layout)
        
        # 3. Заполнение
        self.populate_table()
        
        # 4. Настройки
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.cellClicked.connect(self.on_cell_clicked)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

    def populate_table(self):
        """
        Портирует логику сканирования папок из sub01_LongPeriods.m
        """
        base_path = config.GEN_PATH # 'data/dirflux_newStructure'
        
        # TODO: Это нужно будет портировать более надежно.
        # Сейчас мы просто ищем папки stdbinning_*
        
        binnings_list = []
        try:
            for item in os.listdir(base_path):
                if item.startswith('stdbinning_') and os.path.isdir(os.path.join(base_path, item)):
                    binnings_list.append(item)
        except FileNotFoundError:
            self.table.setItem(0, 0, QTableWidgetItem(f"Ошибка: Не найдена папка {base_path}"))
            return

        col_headers = []
        all_periods_data = [] # Список списков
        self.binning_info_map = {} # Карта 'col' -> {bincode}
        
        max_rows = 0

        for col_idx, binning_dir in enumerate(binnings_list):
            periods_path = os.path.join(base_path, binning_dir, 'RBfullfluxes')
            
            periods = []
            if os.path.exists(periods_path):
                try:
                    for f in os.listdir(periods_path):
                        if f.endswith('.mat'):
                            periods.append(f.replace('.mat', ''))
                except FileNotFoundError:
                    continue # Папки нет, пропускаем
            
            if not periods:
                continue # Пропускаем, если нет данных

            # --- Парсим bincode из имени папки ---
            # 'stdbinning_P3L3E3'
            matches = re.match(r'stdbinning_P(\d+)L(\d+)([ER])(\d+)', binning_dir)
            if not matches:
                continue

            col_headers.append(binning_dir)
            all_periods_data.append(periods)
            max_rows = max(max_rows, len(periods))
            
            self.binning_info_map[col_idx] = {
                'pitchb': int(matches.group(1)),
                'Lb': int(matches.group(2)),
                'RorE': 1 if matches.group(3) == 'E' else 2, # 1=E, 2=R
                'Eb': int(matches.group(4))
            }

        # Настраиваем таблицу
        self.table.setRowCount(max_rows)
        self.table.setColumnCount(len(col_headers))
        self.table.setHorizontalHeaderLabels(col_headers)
        
        # Заполняем
        for c, periods in enumerate(all_periods_data):
            for r, period_name in enumerate(periods):
                self.table.setItem(r, c, QTableWidgetItem(period_name))

    def on_cell_clicked(self, row, col):
        item = self.table.item(row, col)
        if item and item.text():
            self.selected_period = item.text()
            self.selected_binning_info = self.binning_info_map.get(col)
            self.btn_ok.setEnabled(True)
        else:
            self.selected_period = None
            self.selected_binning_info = None
            self.btn_ok.setEnabled(False)

    def on_ok(self):
        """
        Обновляет app_state и закрывает окно.
        """
        if self.selected_period and self.selected_binning_info:
            info = self.selected_binning_info
            
            # Собираем stdbinning из информации
            b_type = "E" if info['RorE'] == 1 else "R"
            stdbinning = f"P{info['pitchb']}L{info['Lb']}{b_type}{info['Eb']}"
            
            self.app_state.update_multiple(
                Period=self.selected_period,
                pitchb=info['pitchb'],
                Lb=info['Lb'],
                RorE=info['RorE'],
                Eb=info['Eb'],
                stdbinning=stdbinning
                # TODO: Надо проверить, как 'Eb' и 'Rb' в app_state
            )
        
        self.accept() # Закрываем
