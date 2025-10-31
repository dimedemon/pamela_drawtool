"""
Порт pan01_set01_Versions.m

Создает виджет для выбора "Version" и кнопку "?"
"""
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QLineEdit, QPushButton, QGroupBox
from PyQt5.QtCore import QSignalBlocker
from core.state import ApplicationState
from desktop_app.qt_connector import QtConnector
# Мы импортируем диалог, который создадим на следующем шаге
from desktop_app.dialogs.version_info import VersionInfoDialog

def create_versions_widget(app_state: ApplicationState, connector: QtConnector, parent_window):
    """
    Создает QGroupBox, содержащий лейбл, поле ввода и кнопку.
    'parent_window' нужен, чтобы диалоговое окно было модальным.
    """
    # 1. Создаем виджеты
    widget = QGroupBox("Version")
    layout = QHBoxLayout()
    widget.setLayout(layout)
    layout.setContentsMargins(5, 10, 5, 5)

    # label = QLabel("Version:") # Лейбл в заголовке
    edit_version = QLineEdit()
    edit_version.setReadOnly(True)
    button_info = QPushButton("?")
    button_info.setFixedWidth(30) # Делаем кнопку '?' маленькой
    
    # -----------------------------------------------------------------
    # 3. Связывание (Binding)
    # -----------------------------------------------------------------

    # --- Связь: GUI -> Ядро ---
    
    def on_version_changed():
        app_state.flux_version = edit_version.text()

    edit_version.editingFinished.connect(on_version_changed)

    # --- Связь: Ядро -> GUI ---

    def on_core_flux_version_changed(new_flux_version):
        """
        Вызывается, когда ЯДРО меняет fluxVersion.
        Обновляет поле QLineEdit.
        """
        with QSignalBlocker(edit_version):
            edit_version.setText(new_flux_version)

    connector.flux_version_changed.connect(on_core_flux_version_changed)
    
    # --- Логика кнопки "?" ---
    
    def on_info_button_clicked():
        """
        Открывает диалоговое окно VersionInfo.
        """
        # Создаем и показываем диалог.
        # 'parent_window' (self.main_window) важен,
        # чтобы диалог открылся "поверх" главного окна.
        dialog = VersionInfoDialog(app_state, parent_window)
        dialog.exec_() # exec_() открывает модальное окно и ждет

    button_info.clicked.connect(on_info_button_clicked)

    # 4. Инициализация
    on_core_flux_version_changed(app_state.flux_version)
    
    # Добавляем виджеты в макет
    # layout.addWidget(label)
    layout.addWidget(edit_version)
    layout.addWidget(button_info)
    
    return widget
