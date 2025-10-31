"""
Порт диалога ShowEbin из pan04_set03_E.m
"""
import numpy as np
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem,
                             QPushButton, QHBoxLayout, QAbstractItemView)
from PyQt5.QtCore import Qt
from core import config
from core.state import ApplicationState

class EBinDialog(QDialog):
    
    def __init__(self, app_state: ApplicationState, parent=None):
        super().__init__(parent)
        
        self.app_state = app_state
        self.setWindowTitle(f"Energy/Rigidity Bins (E{self.app_state.eb})")
        self.setGeometry(250, 250, 400, 500)
        
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
        Заполняет E/R бинами из config.BIN_INFO
        """
        try:
            # -1 т.к. Eb в MATLAB начинается с 1
            eb_idx = self.app_state.eb - 1
            e_bins = config.BIN_INFO['Ebin'][eb_idx]
            r_bins = config.BIN_INFO['Rig'][eb_idx]
        except (IndexError, TypeError, KeyError):
            self.table.setRowCount(1)
            self.table.setColumnCount(1)
            self.table.setItem(0, 0, QTableWidgetItem(f"Ошибка: E-bin {self.app_state.eb} не найден."))
            return

        e_min_col = e_bins[:-1]
        e_max_col = e_bins[1:]
        r_min_col = r_bins[:-1]
        r_max_col = r_bins[1:]
        
        self.table.setRowCount(len(e_min_col))
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(
            ["E_min, GeV", "E_max, GeV", "R_min, GV", "R_max, GV"]
        )
        
        for row in range(len(e_min_col)):
            self.table.setItem(row, 0, QTableWidgetItem(f"{e_min_col[row]:.3f}"))
            self.table.setItem(row, 1, QTableWidgetItem(f"{e_max_col[row]:.3f}"))
            self.table.setItem(row, 2, QTableWidgetItem(f"{r_min_col[row]:.3f}"))
            self.table.setItem(row, 3, QTableWidgetItem(f"{r_max_col[row]:.3f}"))

    def on_selection_changed(self):
        self.btn_ok.setEnabled(True)
        
    def on_ok(self):
        selected_rows = sorted(list(set(index.row() for index in self.table.selectedIndexes())))
        
        if not selected_rows:
            self.reject()
            return
            
        try:
            eb_idx = self.app_state.eb - 1
            e_bins = config.BIN_INFO['Ebin'][eb_idx]
            r_bins = config.BIN_INFO['Rig'][eb_idx]
            
            e_values = [e_bins[row] for row in selected_rows]
            e_max_values = [e_bins[row + 1] for row in selected_rows]
            rig_values = [r_bins[row] for row in selected_rows]
            rig_max_values = [r_bins[row + 1] for row in selected_rows]
            
            # Сохраняем в app_state
            self.app_state.update_multiple(
                e=e_values,
                e_max=e_max_values,
                rig=rig_values,
                rig_max=rig_max_values
            )
            
            self.accept() # Закрываем
            
        except Exception as e:
            print(f"Ошибка при выборе E-бина: {e}")
            self.reject()
