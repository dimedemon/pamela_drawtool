"""
Порт VersionInfo.m

Создает диалоговое окно, показывающее таблицу версий и биннингов.
"""

import numpy as np
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem,
                             QPushButton, QHBoxLayout, QWidget, QAbstractItemView,
                             QHeaderView)
from PyQt5.QtCore import Qt
from core import config
from core.state import ApplicationState

class VersionInfoDialog(QDialog):
    
    def __init__(self, app_state: ApplicationState, parent=None):
        super().__init__(parent)
        
        self.app_state = app_state
        self.selected_cell_info = None
        
        self.setWindowTitle("Version Information")
        self.setGeometry(150, 150, 600, 400) # x, y, width, height
        
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        
        # 1. Создаем таблицу
        self.table = QTableWidget()
        main_layout.addWidget(self.table)
        
        # 2. Создаем кнопки
        button_layout = QHBoxLayout()
        self.btn_set_version = QPushButton("Set Version & Binning")
        self.btn_set_version.setEnabled(False)
        self.btn_set_version.clicked.connect(self.on_set_version)
        
        # (Кнопки "show version info" и "show binning" мы опускаем для простоты,
        # так как вся информация уже на экране)
        
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.accept) # accept() закрывает диалог
        
        button_layout.addStretch()
        button_layout.addWidget(self.btn_set_version)
        button_layout.addWidget(btn_close)
        
        main_layout.addLayout(button_layout)
        
        # 3. Заполняем таблицу данными
        self.populate_table()
        
        # 4. Настраиваем таблицу
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers) # Read-only
        self.table.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.cellClicked.connect(self.on_cell_clicked)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

    def populate_table(self):
        """
        Заполняет таблицу, портируя логику из VersionInfo.m
        """
        
        # --- (Эта логика почти 1-в-1 скопирована из binnings.py) ---
        meta_data = config._load_mat_file(config.METADATA_FILE)
        if not meta_data:
            self.table.setRowCount(1)
            self.table.setColumnCount(1)
            self.table.setItem(0, 0, QTableWidgetItem("Ошибка: file_metadata.mat не найден"))
            return

        # TODO: Портировать чтение versioninfo.dat
        # ВРЕМЕННАЯ ЗАГЛУШКА: Используем только fluxVersions
        all_flux_versions = sorted(np.unique(meta_data['fluxVersions']))
        
        current_geo = self.app_state.geo_selection
        current_sel = self.app_state.selection
        
        flux_pre_indices = (meta_data['GeoSelections'] == current_geo) & \
                           (meta_data['Selections'] == current_sel)
        
        table_headers = []
        table_columns_data = [] # Список списков [ ('P3L3E3', 'binning'), ('P1L1E1', 'binning'), ... ]
        self.cell_info_map = {} # Карта для хранения данных о ячейке 'row,col' -> info
        
        max_rows = 0

        for col, flux_ver in enumerate(all_flux_versions):
            col_header = f"v{flux_ver:02.0f}"
            table_headers.append(col_header)
            
            # (Пропускаем aux_ver, pre_ver... для простоты, т.к. нет versioninfo.dat)
            
            flux_files = flux_pre_indices & (meta_data['fluxVersions'] == flux_ver)
            
            column_data = []
            if np.any(flux_files):
                flux_stdbinnings = meta_data['stdbinnings'][flux_files]
                unique_stdbinnings = sorted(list(np.unique(flux_stdbinnings[flux_stdbinnings != ''])))
                
                for row, binning in enumerate(unique_stdbinnings):
                    column_data.append(binning)
                    key = f"{row},{col}"
                    self.cell_info_map[key] = {
                        'type': 'binning', 
                        'version': col_header, 
                        'binning': binning
                    }
                max_rows = max(max_rows, len(unique_stdbinnings))
            else:
                 column_data.append("no files")
                 key = f"{0},{col}"
                 self.cell_info_map[key] = {'type': 'none', 'version': col_header, 'binning': ''}
                 max_rows = max(max_rows, 1)

            table_columns_data.append(column_data)

        # Устанавливаем размеры таблицы
        self.table.setRowCount(max_rows)
        self.table.setColumnCount(len(table_headers))
        self.table.setHorizontalHeaderLabels(table_headers)
        
        # Заполняем ячейки
        for c, col_data in enumerate(table_columns_data):
            for r, cell_text in enumerate(col_data):
                self.table.setItem(r, c, QTableWidgetItem(cell_text))

    def on_cell_clicked(self, row, col):
        """Вызывается при клике на ячейку."""
        key = f"{row},{col}"
        if key in self.cell_info_map:
            info = self.cell_info_map[key]
            self.selected_cell_info = info
            
            # Включаем кнопку, если это 'binning'
            if info['type'] == 'binning':
                self.btn_set_version.setEnabled(True)
            else:
                self.btn_set_version.setEnabled(False)
        else:
            self.selected_cell_info = None
            self.btn_set_version.setEnabled(False)

    def on_set_version(self):
        """
        Вызывается при нажатии "Set Version & Binning".
        Обновляет app_state и закрывает окно.
        """
        if not self.selected_cell_info:
            return
            
        info = self.selected_cell_info
        
        if info['type'] == 'binning':
            # Парсим P(d)L(d)E(d)
            matches = re.match(r'P(\d+)L(\d+)E(\d+)', info['binning'])
            if matches:
                self.app_state.update_multiple(
                    flux_version=info['version'],
                    stdbinning=info['binning'],
                    pitchb=int(matches.group(1)),
                    Lb=int(matches.group(2)),
                    Eb=int(matches.group(3))
                    # TODO: Добавить auxVersion, preVersion из versioninfo.dat
                )
            else:
                 self.app_state.update_multiple(
                    flux_version=info['version'],
                    stdbinning=info['binning']
                 )
        
        self.accept() # Закрываем диалог
