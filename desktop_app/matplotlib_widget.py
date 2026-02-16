"""
Виджет Matplotlib (SCIENTIFIC VISUALIZATION)
Улучшенная графика: второстепенные деления, качественная сетка, 
научное форматирование осей.
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib.ticker import LogFormatterExponent, LogLocator, ScalarFormatter
import matplotlib.pyplot as plt
import numpy as np

class MplCanvas(QWidget):
    def __init__(self, parent=None, width=7, height=5, dpi=100):
        super(MplCanvas, self).__init__(parent)

        # Устанавливаем современный научный стиль
        try:
            plt.style.use('seaborn-v0_8-ticks') 
        except:
            plt.style.use('ggplot')

        # Общие параметры шрифтов и линий для соответствия протоколу
        plt.rcParams.update({
            'font.size': 11,
            'axes.linewidth': 1.2,
            'xtick.direction': 'in',
            'ytick.direction': 'in',
            'xtick.major.size': 7,
            'ytick.major.size': 7,
            'xtick.minor.size': 4,
            'ytick.minor.size': 4,
            'legend.frameon': True,
            'legend.edgecolor': '0.8',
            'figure.facecolor': 'white'
        })

        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.canvas = FigureCanvas(self.fig)
        self.toolbar = NavigationToolbar(self.canvas, self)

        layout = QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        self.setLayout(layout)
        
        self.axes_list = []
        self.set_layout_mode(1)

    def set_layout_mode(self, mode):
        self.fig.clf()
        self.axes_list = []
        if mode == 1:
            ax = self.fig.add_subplot(1, 1, 1)
            self.axes_list.append(ax)
        elif mode == 4:
            for i in range(1, 5):
                ax = self.fig.add_subplot(2, 2, i)
                self.axes_list.append(ax)
        self.fig.tight_layout(pad=3.0)
        self.canvas.draw()

    def _setup_scientific_axes(self, ax, xscale='log', yscale='log'):
        """Настройка профессиональной сетки и делений."""
        # Основная и второстепенная сетка
        ax.grid(True, which='major', linestyle='-', linewidth='0.8', color='0.85')
        ax.grid(True, which='minor', linestyle='--', linewidth='0.4', color='0.9', alpha=0.7)
        ax.minorticks_on()

        # Настройка логарифмической шкалы
        if xscale == 'log':
            ax.set_xscale('log')
            # Основные деления (10^0, 10^1...)
            ax.xaxis.set_major_locator(LogLocator(base=10.0, numticks=12))
            # Второстепенные деления (2, 3, 4... между степенями)
            ax.xaxis.set_minor_locator(LogLocator(base=10.0, subs=np.arange(2, 10) * 0.1, numticks=12))
            # Красивое экспоненциальное форматирование
            ax.xaxis.set_major_formatter(LogFormatterExponent())
        else:
            ax.xaxis.set_major_formatter(ScalarFormatter())

        if yscale == 'log':
            ax.set_yscale('log')
            ax.yaxis.set_major_locator(LogLocator(base=10.0, numticks=12))
            ax.yaxis.set_minor_locator(LogLocator(base=10.0, subs=np.arange(2, 10) * 0.1, numticks=12))
            ax.yaxis.set_major_formatter(LogFormatterExponent())

    def draw_plot(self, plot_data: dict):
        """Рисует привлекательный и понятный график."""
        target_ax_idx = plot_data.get("ax_index", 0)
        if target_ax_idx >= len(self.axes_list): target_ax_idx = 0
        ax = self.axes_list[target_ax_idx]
        ax.clear()

        # Применяем научную настройку осей
        self._setup_scientific_axes(
            ax, 
            xscale=plot_data.get("xscale", "log"), 
            yscale=plot_data.get("yscale", "log")
        )

        plot_type = plot_data.get("plot_type", "errorbar")
        label = plot_data.get("label", "Data")

        if plot_type == "errorbar":
            # Основная линия с точками и погрешностями
            ax.errorbar(
                plot_data.get("x", []),
                plot_data.get("y", []),
                xerr=plot_data.get("x_err", None),
                yerr=plot_data.get("y_err", None),
                label=label,
                color='#1f77b4', # Классический научный синий
                marker='o',
                markersize=5,
                linestyle='-',
                linewidth=1.5,
                capsize=3,
                capthick=1,
                elinewidth=1,
                markeredgecolor='white',
                markeredgewidth=0.5
            )

        # Оформление подписей согласно протоколу
        ax.set_xlabel(plot_data.get("xlabel", ""), fontweight='bold', labelpad=10)
        ax.set_ylabel(plot_data.get("ylabel", ""), fontweight='bold', labelpad=10)
        
        # Добавляем заголовок (опционально)
        title = plot_data.get("title", "")
        if title:
            ax.set_title(title, loc='left', fontsize=12, color='0.3')

        # Улучшенная легенда
        if label:
            ax.legend(loc='best', fontsize=9, framealpha=0.9)

        self.fig.tight_layout()
        self.canvas.draw()
