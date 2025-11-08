"""
Виджет для кнопки "Plot" (ИСПРАВЛЕННЫЙ)
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton
from PyQt5.QtGui import QFont

def create_plot_button_widget():
    """
    Создает QWidget, содержащий большую кнопку "PLOT".
    Возвращает: QWidget
    """
    widget = QWidget()
    layout = QVBoxLayout()
    layout.setContentsMargins(0, 10, 0, 10) # Добавим отступ сверху и снизу
    widget.setLayout(layout)
    
    button_plot = QPushButton("PLOT DATA")
    
    # Сделаем кнопку большой и заметной
    font = button_plot.font()
    font.setPointSize(14)
    font.setBold(True)
    button_plot.setMinimumHeight(40) # Зададим минимальную высоту
    
    layout.addWidget(button_plot)
    
    # --- ИСПРАВЛЕНИЕ ---
    # Сохраняем кнопку как атрибут виджета,
    # чтобы main.py мог до нее "достучаться"
    widget.plot_button = button_plot 
    
    # Возвращаем WIDGET (контейнер), а не кнопку
    return widget
