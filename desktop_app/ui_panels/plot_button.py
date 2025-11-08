"""
Виджет для кнопки "Plot"
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton
from PyQt5.QtGui import QFont

def create_plot_button_widget():
    """
    Создает QWidget, содержащий большую кнопку "PLOT".
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
    button_plot.setFont(font)
    button_plot.setMinimumHeight(40) # Зададим минимальную высоту
    
    layout.addWidget(button_plot)
    
    # Мы не возвращаем widget, мы возвращаем саму кнопку,
    # чтобы main.py мог напрямую подключиться к ее .clicked
    return button_plot
