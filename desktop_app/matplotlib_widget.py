"""
Виджет Matplotlib (Фаза 4)

Этот файл содержит класс MplCanvas, который является
холстом Matplotlib, "завернутым" в виджет PyQt.
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt # Импортируем pyplot для rcParams

class MplCanvas(QWidget):
    """
    Виджет Matplotlib.
    """
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        super(MplCanvas, self).__init__(parent)

        # Настраиваем параметры Matplotlib для читаемости
        plt.rcParams.update({'font.size': 9, 'axes.titlesize': 10})

        # 1. Создаем фигуру Matplotlib
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        
        # 2. Создаем холст PyQt, который будет рисовать эту фигуру
        self.canvas = FigureCanvas(self.fig)
        
        # 3. Добавляем холст в макет виджета
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)
        
        # Добавляем 4 "оси" (subplots), как в вашем DrawTool4.m
        # (2x2 сетка)
        self.ax1 = self.fig.add_subplot(2, 2, 1)
        self.ax2 = self.fig.add_subplot(2, 2, 2)
        self.ax3 = self.fig.add_subplot(2, 2, 3)
        self.ax4 = self.fig.add_subplot(2, 2, 4)
        
        self.axes_list = [self.ax1, self.ax2, self.ax3, self.ax4]
        
        self.fig.tight_layout() # Чтобы графики не наезжали друг на друга

    def clear_all_axes(self):
        """Очищает все 4 графика."""
        for ax in self.axes_list:
            ax.cla() # cla() = Clear Axis

    def draw_plot(self, plot_data: dict):
        """
        Рисует один график (errorbar, plot, pcolor...) на
        основе словаря данных из processing.py.
        """
        ax_index = plot_data.get("ax_index", 0)
        if ax_index >= len(self.axes_list):
            print(f"Ошибка: Неверный индекс осей {ax_index}. Рисуем на ax[0].")
            ax_index = 0
            
        ax = self.axes_list[ax_index]
        
        plot_type = plot_data.get("plot_type", "errorbar")
        
        if plot_type == "errorbar":
            ax.errorbar(
                plot_data.get("x", []),
                plot_data.get("y", []),
                xerr=plot_data.get("x_err", None),
                yerr=plot_data.get("y_err", None),
                label=plot_data.get("label", ""),
                linestyle='-',
                marker='.'
            )
        
        # (Здесь мы добавим 'pcolor', 'stairs' и т.д., когда портируем их)
        
        # Применяем логарифмические шкалы, если нужно
        if plot_data.get("xscale") == "log":
            ax.set_xscale('log')
        if plot_data.get("yscale") == "log":
            ax.set_yscale('log')
            
        ax.set_xlabel(plot_data.get("xlabel", ""))
        ax.set_ylabel(plot_data.get("ylabel", ""))
        ax.set_title(plot_data.get("label", "")) # Временно ставим лейбл как заголовок
        ax.legend()
        ax.grid(True)
        
        # Перерисовываем холст
        self.canvas.draw()
