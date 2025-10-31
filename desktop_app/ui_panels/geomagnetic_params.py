"""
Порт pan04_GeomagneticParams.m (контейнер)
и pan04_set01_L.m (виджет L)
"""
from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QGroupBox, QVBoxLayout)
from PyQt5.QtCore import QSignalBlocker, Qt
from core.state import ApplicationState
from desktop_app.qt_connector import QtConnector
from desktop_app.dialogs.l_bin_dialog import LBinDialog

def create_geomag_params_widget(app_state: ApplicationState, connector: QtConnector, parent_window):
    """
    Создает QGroupBox "Input parameters: Geomagnetic".
    """
    # 1. Создаем главный контейнер (pan04)
    widget = QGroupBox("Input parameters: Geomagnetic")
    main_layout = QVBoxLayout()
    widget.setLayout(main_layout)
    main_layout.setContentsMargins(5, 10, 5, 5)

    # --- Верхний макет (заголовки) ---
    header_layout = QHBoxLayout()
    header_layout.addWidget(QLabel(""), 1) # Пустое место 1/8
    header_layout.addWidget(QLabel("min value"), 4) # 4/8
    header_layout.addWidget(QLabel("max value"), 2) # 2/8
    header_layout.addWidget(QLabel("Δ"), 1) # 1/8
    main_layout.addLayout(header_layout)

    # --- Макет 1: L-Shell (pan04_set01_L) ---
    l_layout = QHBoxLayout()
    
    label_l = QLabel("L:")
    edit_l_min = QLineEdit()
    button_show_l = QPushButton("...") # Кнопка "ShowLbin"
    button_show_l.setFixedWidth(30)
    edit_l_max = QLineEdit()
    edit_delta_l = QLineEdit()

    # Добавляем в макет L
    l_layout.addWidget(label_l, 1)
    l_layout.addWidget(edit_l_min, 4)
    l_layout.addWidget(button_show_l) # Кнопка между min и max
    l_layout.addWidget(edit_l_max, 2)
    l_layout.addWidget(edit_delta_l, 1)
    main_layout.addLayout(l_layout)

    # --- (Здесь будут Макет 2: Pitch, Макет 3: E, Макет 4: R...) ---
    
    # -----------------------------------------------------------------
    # 3. Связывание (Binding) - только для L
    # -----------------------------------------------------------------

    # --- Связь: GUI -> Ядро ---
    
    def on_l_min_changed():
        txt = edit_l_min.text()
        if txt.lower() == 'all':
            app_state.l = [-1]
        else:
            try:
                # Парсим "1.1, 1.2, 1.3"
                l_values = [float(val.strip()) for val in txt.split(',') if val.strip()]
                app_state.l = l_values
            except ValueError:
                # Если ввели ерунду, возвращаем значение из app_state
                on_core_l_changed(app_state.l)

    def on_l_max_changed():
        try:
            app_state.l_max = float(edit_l_max.text())
        except ValueError:
            on_core_l_max_changed(app_state.l_max)
    
    edit_l_min.editingFinished.connect(on_l_min_changed)
    edit_l_max.editingFinished.connect(on_l_max_changed)
    # (delta_l пока не привязываем)

    # --- Связь: Ядро -> GUI ---

    def on_core_l_changed(new_l_list):
        with QSignalBlocker(edit_l_min):
            if not new_l_list:
                edit_l_min.setText("")
            elif new_l_list == [-1]:
                edit_l_min.setText("All")
            else:
                # Конвертируем [1.1, 1.2] в "1.1, 1.2"
                txt = ", ".join(f"{val:.3f}" for val in new_l_list)
                edit_l_min.setText(txt)

    def on_core_l_max_changed(new_l_max):
        with QSignalBlocker(edit_l_max):
            edit_l_max.setText(f"{new_l_max:.3f}")
            
    connector.l_changed.connect(on_core_l_changed)
    connector.l_max_changed.connect(on_core_l_max_changed)
    
    # --- Кнопка "..." (ShowLbin) ---
    def on_show_l_bin():
        dialog = LBinDialog(app_state, parent_window)
        # exec_() блокирует и ждет. Если пользователь нажал OK,
        # диалог УЖЕ обновил app_state.
        dialog.exec_()
        # Нам не нужно читать результат, app_state уже обновлен,
        # и сигналы connector'а (l_changed) уже обновили QLineEdit.
            
    button_show_l.clicked.connect(on_show_l_bin)

    # 4. Инициализация
    on_core_l_changed(app_state.l)
    on_core_l_max_changed(app_state.l_max)
    
    # TODO: Включить/выключить виджеты в зависимости от PlotKind
    # (setGeomagParamEn.m)
    
    return widget
