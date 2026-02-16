"""
Виджет Matplotlib (SCIENTIFIC VERSION - LABEL ADJUSTED)
Изменено: уменьшен отступ названия оси Y (labelpad), чтобы оно располагалось ближе к оси.
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib.ticker import LogFormatterMathtext, LogLocator, ScalarFormatter
from matplotlib.colors import LogNorm, Normalize
import matplotlib.pyplot as plt
import numpy as np

class MplCanvas(QWidget):
    def __init__(self, parent=None, width=7, height=5, dpi=100):
        super(MplCanvas, self).__init__(parent)

        # Установка научного стиля для четкости линий и делений
        try:
            plt.style.use('seaborn-v0_8-ticks') 
        except:
            plt.style.use('ggplot')

        # Параметры для качественной визуализации
        plt.rcParams.update({
            'font.size': 10,
            'axes.linewidth': 1.2,
            'xtick.direction': 'in',
            'ytick.direction': 'in',
            'xtick.major.size': 6,
            'ytick.major.size': 6,
            'xtick.minor.size': 3,
            'ytick.minor.size': 3,
            'legend.frameon': True,
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
        self.fig.tight_layout(pad=2.5)
        self.canvas.draw()

    def clear_all_axes(self):
        for ax in self.axes_list:
            ax.clear()

    def _apply_scientific_styling(self, ax, xscale='linear', yscale='linear'):
        """Настройка сетки и делений с полным основанием 10^n."""
        ax.grid(True, which='major', linestyle='-', linewidth='0.7', color='0.85')
        ax.grid(True, which='minor', linestyle='--', linewidth='0.3', color='0.9', alpha=0.6)
        ax.minorticks_on()

        if xscale == 'log':
            ax.set_xscale('log')
            ax.xaxis.set_major_locator(LogLocator(base=10.0, numticks=10))
            ax.xaxis.set_minor_locator(LogLocator(base=10.0, subs=np.arange(2, 10) * 0.1, numticks=10))
            ax.xaxis.set_major_formatter(LogFormatterMathtext())
        else:
            ax.xaxis.set_major_formatter(ScalarFormatter())

        if yscale == 'log':
            ax.set_yscale('log')
            ax.yaxis.set_major_locator(LogLocator(base=10.0, numticks=10))
            ax.yaxis.set_minor_locator(LogLocator(base=10.0, subs=np.arange(2, 10) * 0.1, numticks=10))
            ax.yaxis.set_major_formatter(LogFormatterMathtext())
        else:
            ax.yaxis.set_major_formatter(ScalarFormatter())

    def draw_plot(self, plot_data: dict):
        """Отрисовка данных с уменьшенным отступом названия оси Y."""
        target_ax_idx = plot_data.get("ax_index", 0)
        if target_ax_idx >= len(self.axes_list): target_ax_idx = 0
        ax = self.axes_list[target_ax_idx]
        
        self._apply_scientific_styling(
            ax, 
            xscale=plot_data.get("xscale", "linear"), 
            yscale=plot_data.get("yscale", "linear")
        )

        plot_type = plot_data.get("plot_type", "errorbar")
        label = plot_data.get("label", "")

        if plot_type == "errorbar":
            ax.errorbar(
                plot_data.get("x", []),
                plot_data.get("y", []),
                xerr=plot_data.get("x_err", None),
                yerr=plot_data.get("y_err", None),
                label=label,
                color='#1f77b4',
                linestyle='-', marker='o', markersize=4, 
                capsize=2, linewidth=1.2, elinewidth=1.0
            )
            if label: ax.legend(framealpha=0.8, loc='best')

        # Установка подписей осей
        ax.set_xlabel(plot_data.get("xlabel", ""), labelpad=6, fontweight='bold')
        # labelpad=2 существенно приближает название к оси Y
        ax.set_ylabel(plot_data.get("ylabel", ""), labelpad=2, fontweight='bold')
        
        if plot_data.get("title"):
            ax.set_title(plot_data.get("title"), loc='left', fontsize=11, pad=10)
        
        self.canvas.draw()
