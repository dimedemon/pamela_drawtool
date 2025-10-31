"""
Порт диалога ShowPitchbin из pan04_set02_pitch.m
"""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem,
                             QPushButton, QHBoxLayout, QAbstractItemView)
from PyQt5.QtCore import Qt
from core import config
from core.state import ApplicationState

class PitchBinDialog(QDialog):
    
    def __init__(self, app_state: ApplicationState, parent=None):
        super().__init__(parent)
        
        self.app_state = app_state
        self.setWindowTitle(f"Pitch-Angle Bins (P{self.app_state.pitchb})")
        self.setGeometry(250, 250, 300, 500)
        
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
        btn_cancel.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.btn_ok)
        button_layout.addWidget(btn_cancel)
        main_layout.addLayout(button_layout)
        
        # 3. Заполнение
        self.populate_table()
        
        # 4. Настройки
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionMode(QAbstractItemView.MultiSelection)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.selectionModel().selectionChanged.connect(self.on_selection_changed)

    def populate_table(self):
        """
        Заполняет таблицу Pitch-бинами из config.BIN_INFO
        """
        try:
            # -1 т.к. pitchb в MATLAB начинается с 1
            pitch_bins = config.BIN_INFO['pitchbin'][self.app_state.pitchb - 1]
        except (IndexError, TypeError):
            self.table.setRowCount(1)
            self.table.setColumnCount(1)
            self.table.setItem(0, 0, QTableWidgetItem(f"Ошибка: Pitch-bin {self.app_state.pitchb} не найден."))
            return

        pitch_min_col = pitch_bins[:-1]
        pitch_max_col = pitch_bins[1:]
        
        self.table.setRowCount(len(pitch_min_col))
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["α_eq, min (deg)", "α_eq, max (deg)"])
        
        for row in range(len(pitch_min_col)):
            self.table.setItem(row, 0, QTableWidgetItem(f"{pitch_min_col[row]:.1f}"))
            self.table.setItem(row, 1, QTableWidgetItem(f"{pitch_max_col[row]:.1f}"))

    def on_selection_changed(self):
        self.btn_ok.setEnabled(True)
        
    def on_ok(self):
        """
        Сохраняет выбранные значения в app_state.
        """
        selected_rows = sorted(list(set(index.row() for index in self.table.selectedIndexes())))
        
        if not selected_rows:
            self.reject()
            return
            
        try:
            pitch_bins = config.BIN_INFO['pitchbin'][self.app_state.pitchb - 1]
            
            pitch_values = [pitch_bins[row] for row in selected_rows]
            pitch_max_values = [pitch_bins[row + 1] for row in selected_rows]
            
            # Сохраняем в app_state
            self.app_state.pitch = pitch_values
            self.app_state.pitch_max = pitch_max_values
            
            self.accept() # Закрываем
            
        except Exception as e:
            print(f"Ошибка при выборе Pitch-бина: {e}")
            self.reject()
