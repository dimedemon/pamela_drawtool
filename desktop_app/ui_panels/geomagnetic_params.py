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
from desktop_app.dialogs.pitch_bin_dialog import PitchBinDialog

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

    pitch_layout = QHBoxLayout()
    
    label_pitch = QLabel("α:")
    edit_pitch_min = QLineEdit()
    button_show_pitch = QPushButton("...") # Кнопка "ShowPitchbin"
    button_show_pitch.setFixedWidth(30)
    edit_pitch_max = QLineEdit()
    edit_delta_alpha = QLineEdit()

    # Добавляем в макет Pitch
    pitch_layout.addWidget(label_pitch, 1)
    pitch_layout.addWidget(edit_pitch_min, 4)
    pitch_layout.addWidget(button_show_pitch) 
    pitch_layout.addWidget(edit_pitch_max, 2)
    pitch_layout.addWidget(edit_delta_alpha, 1)
    main_layout.addLayout(pitch_layout)

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
    ##тут вставка
    def on_pitch_min_changed():
        txt = edit_pitch_min.text()
        if txt.lower() == 'all':
            app_state.pitch = [-1]
        else:
            try:
                pitch_values = [float(val.strip()) for val in txt.split(',') if val.strip()]
                app_state.pitch = pitch_values
            except ValueError:
                on_core_pitch_changed(app_state.pitch)

    def on_pitch_max_changed():
        txt = edit_pitch_max.text()
        try:
            pitch_max_values = [float(val.strip()) for val in txt.split(',') if val.strip()]
            app_state.pitch_max = pitch_max_values
        except ValueError:
            on_core_pitch_max_changed(app_state.pitch_max)
            
    def on_d_alpha_changed():
        try:
            app_state.d_alpha = float(edit_delta_alpha.text())
        except ValueError:
            on_core_d_alpha_changed(app_state.d_alpha)
    
    edit_pitch_min.editingFinished.connect(on_pitch_min_changed)
    edit_pitch_max.editingFinished.connect(on_pitch_max_changed)
    edit_delta_alpha.editingFinished.connect(on_d_alpha_changed)

    # --- Связь: Ядро -> GUI (Pitch) ---

    def on_core_pitch_changed(new_pitch_list):
        with QSignalBlocker(edit_pitch_min):
            if not new_pitch_list:
                edit_pitch_min.setText("")
            elif new_pitch_list == [-1]:
                edit_pitch_min.setText("All")
            else:
                txt = ", ".join(f"{val:.1f}" for val in new_pitch_list)
                edit_pitch_min.setText(txt)

    def on_core_pitch_max_changed(new_pitch_max_list):
        with QSignalBlocker(edit_pitch_max):
            if not new_pitch_max_list:
                edit_pitch_max.setText("")
            else:
                txt = ", ".join(f"{val:.1f}" for val in new_pitch_max_list)
                edit_pitch_max.setText(txt)

    def on_core_d_alpha_changed(new_d_alpha):
        with QSignalBlocker(edit_delta_alpha):
            edit_delta_alpha.setText(f"{new_d_alpha:.1f}")
            
    connector.pitch_changed.connect(on_core_pitch_changed)
    connector.pitch_max_changed.connect(on_core_pitch_max_changed)
    connector.d_alpha_changed.connect(on_core_d_alpha_changed)
    
    # --- Кнопка "..." (ShowPitchbin) ---
    def on_show_pitch_bin():
        dialog = PitchBinDialog(app_state, parent_window)
        dialog.exec_()
        # app_state уже обновлен диалогом
            
    button_show_pitch.clicked.connect(on_show_pitch_bin)
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
    on_core_pitch_changed(app_state.pitch)
    on_core_pitch_max_changed(app_state.pitch_max)
    on_core_d_alpha_changed(app_state.d_alpha)
    
    # TODO: Включить/выключить виджеты в зависимости от PlotKind
    # (setGeomagParamEn.m)
    
    return widget
