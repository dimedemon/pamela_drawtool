"""
Виджет Matplotlib (SCIENTIFIC HISTOGRAM EDITION)
Добавлена поддержка гистограмм N vs Flux с логарифмической шкалой Y 
для изучения "хвостов" распределения.
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib.ticker import LogFormatterMathtext, LogLocator, ScalarFormatter
import matplotlib.pyplot as plt
import numpy as np

class MplCanvas(QWidget):
    def __init__(self, parent=None, width=7, height=5, dpi=100):
        super(MplCanvas, self).__init__(parent)

        # Установка научного стиля
        try:
            plt.style.use('seaborn-v0_8-ticks') 
        except:
            plt.style.use('ggplot')

        plt.rcParams.update({
            'font.size': 10,
            'axes.linewidth': 1.2,
            'xtick.direction': 'in',
            'ytick.direction': 'in',
            'xtick.major.size': 6,
            'ytick.major.size': 6,
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

    def _apply_styling(self, ax, xscale='linear', yscale='linear'):
        """Настройка сетки и делений для научного вида."""
        ax.grid(True, which='major', linestyle='-', linewidth='0.7', color='0.85')
        ax.grid(True, which='minor', linestyle='--', linewidth='0.3', color='0.9', alpha=0.6)
        ax.minorticks_on()

        if xscale == 'log':
            ax.set_xscale('log')
            ax.xaxis.set_major_formatter(LogFormatterMathtext())
        else:
            ax.xaxis.set_major_formatter(ScalarFormatter())

        if yscale == 'log':
            ax.set_yscale('log')
            ax.yaxis.set_major_formatter(LogFormatterMathtext())
            # Установка локатора для логарифмической шкалы Y, чтобы видеть "хвосты"
            ax.yaxis.set_major_locator(LogLocator(base=10.0, numticks=10))
        else:
            ax.yaxis.set_major_formatter(ScalarFormatter())

    def draw_plot(self, plot_data: list):
        """Принимает список словарей с данными и отрисовывает их."""
        if not plot_data: return

        for data_item in plot_data:
            target_ax_idx = data_item.get("ax_index", 0)
            if target_ax_idx >= len(self.axes_list): target_ax_idx = 0
            ax = self.axes_list[target_ax_idx]
            
            # Применяем масштаб и сетку
            self._apply_styling(
                ax, 
                xscale=data_item.get("xscale", "linear"), 
                yscale=data_item.get("yscale", "linear")
            )

            plot_type = data_item.get("plot_type", "errorbar")
            label = data_item.get("label", "")

            # --- ЛОГИКА ГИСТОГРАММЫ (N vs Flux) ---
            if plot_type == "histogram":
                # x в данном случае - это массив значений потока
                values = data_item.get("x", [])
                bins = data_item.get("bins", 20)
                
                # Рисуем N по вертикали
                ax.hist(values, bins=bins, color='#2ca02c', edgecolor='black', 
                        alpha=0.7, label=label, density=False)
                
            # --- ЛОГИКА ОШИБОК (Спектры) ---
            elif plot_type == "errorbar":
                ax.errorbar(
                    data_item.get("x", []),
                    data_item.get("y", []),
                    xerr=data_item.get("x_err", None),
                    yerr=data_item.get("y_err", None),
                    label=label, color='#1f77b4',
                    linestyle='-', marker='o', markersize=4, capsize=2
                )

            # Оформление осей
            ax.set_xlabel(data_item.get("xlabel", "Flux"), labelpad=6, fontweight='bold')
            ax.set_ylabel(data_item.get("ylabel", "N"), labelpad=2, fontweight='bold')
            
            if data_item.get("title"):
                ax.set_title(data_item.get("title"), loc='left', fontsize=11, pad=10)
            
            if label:
                ax.legend(framealpha=0.8)

        self.canvas.draw()
