"""
Порт pan01_set03_Binnings.m

Создает виджет для выбора "Binnings".
Реализует логику фильтрации (серая подсветка) в зависимости от 'fluxVersion'.
"""
import re
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QComboBox, QGroupBox
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt, QSignalBlocker
from core import config
from core.state import ApplicationState
from desktop_app.qt_connector import QtConnector

def create_binnings_widget(app_state: ApplicationState, connector: QtConnector):
    """
    Создает QGroupBox, содержащий лейбл и выпадающий список для биннингов.
    """
    # 1. Создаем виджеты
    widget = QGroupBox("Binnings")
    layout = QHBoxLayout()
    widget.setLayout(layout)
    layout.setContentsMargins(5, 10, 5, 5)

    combo_binnings = QComboBox()
    
    # 2. Загружаем константы
    BINNING_STR = config.BINNING_STR
    
    combo_binnings.addItems(BINNING_STR)
    
    # -----------------------------------------------------------------
    # 3. Связывание (Binding)
    # -----------------------------------------------------------------

    # --- Связь: GUI -> Ядро ---
    
    def on_binnings_changed(index):
        if index < 0:
            return
            
        selected_binning = combo_binnings.itemText(index)
        
        # В MATLAB у вас был 'raw_binning'. В PyQt мы делаем так же:
        # Проверяем, не "серая" ли опция. Если да, не даем ее выбрать.
        # (Хотя QComboBox.model().item(i).setEnabled(False) должен делать это
        # автоматически, мы перепроверяем).
        item_data = combo_binnings.itemData(index, Qt.ForegroundRole)
        if item_data == QColor('gray'):
            # Пользователь выбрал неактивный элемент. Найти первый активный.
            first_available_idx = 0
            for i in range(combo_binnings.count()):
                if combo_binnings.itemData(i, Qt.ForegroundRole) != QColor('gray'):
                    first_available_idx = i
                    break
            # Принудительно возвращаем на первый активный
            combo_binnings.setCurrentIndex(first_available_idx)
            return

        # Парсим P(d)L(d)E(d)
        matches = re.match(r'P(\d+)L(\d+)E(\d+)', selected_binning)
        
        if matches:
            # Обновляем все поля в app_state
            app_state.update_multiple(
                stdbinning=selected_binning,
                pitchb=int(matches.group(1)),
                Lb=int(matches.group(2)),
                Eb=int(matches.group(3))
            )
        else:
            app_state.stdbinning = selected_binning

    combo_binnings.currentIndexChanged.connect(on_binnings_changed)

    # --- Связь: Ядро -> GUI ---

    def on_core_stdbinning_changed(new_stdbinning):
        """
        Вызывается, когда ЯДРО меняет stdbinning.
        Обновляет комбо-бокс 'Binnings'.
        """
        if new_stdbinning in BINNING_STR:
            idx = BINNING_STR.index(new_stdbinning)
            with QSignalBlocker(combo_binnings):
                combo_binnings.setCurrentIndex(idx)

    def on_core_flux_version_changed(new_flux_version):
        """
        Вызывается, когда ЯДРО меняет fluxVersion.
        Фильтрует (красит серым) комбо-бокс 'Binnings'.
        """
        # TODO: Реализовать логику фильтрации
        # Эта логика в MATLAB зависела от 'loaded_data' из file_metadata.mat.
        # Мы портируем ее позже, когда будет готов file_metadata.mat
        
        # --- ВРЕМЕННАЯ ЗАГЛУШКА (все опции активны) ---
        gray_color = QColor('gray')
        black_color = QColor('black')
        
        # (Здесь должна быть логика из updateBinningPopupAvailability)
        # available_stdbinnings = ...
        
        with QSignalBlocker(combo_binnings):
            for i, item_text in enumerate(BINNING_STR):
                # is_available = item_text in available_stdbinnings
                is_available = True # <--- ЗАГЛУШКА
                
                if is_available:
                    combo_binnings.model().item(i).setEnabled(True)
                    combo_binnings.setItemData(i, black_color, Qt.ForegroundRole)
                else:
                    combo_binnings.model().item(i).setEnabled(False)
                    combo_binnings.setItemData(i, gray_color, Qt.ForegroundRole)
        # --- КОНЕЦ ЗАГЛУШКИ ---


    connector.stdbinning_changed.connect(on_core_stdbinning_changed)
    connector.flux_version_changed.connect(on_core_flux_version_changed)
    
    # 4. Инициализация
    on_core_stdbinning_changed(app_state.stdbinning)
    on_core_flux_version_changed(app_state.flux_version)
    
    # Добавляем виджеты в макет
    layout.addWidget(combo_binnings)
    
    return widget
