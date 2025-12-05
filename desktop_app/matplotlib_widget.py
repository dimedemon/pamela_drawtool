"""
Виджет Matplotlib (Фаза 4 - 2D SUPPORT)
Поддерживает errorbar и pcolormesh (тепловые карты).
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib.colors import LogNorm, Normalize
import matplotlib.pyplot as plt
import numpy as np

class MplCanvas(QWidget):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        super(MplCanvas, self).__init__(parent)

        try: plt.style.use('seaborn-v0_8-darkgrid')
        except: pass
        plt.rcParams.update({'font.size': 10, 'axes.titlesize': 12})

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
        self.fig.tight_layout()
        self.canvas.draw()

    def clear_all_axes(self):
        for ax in self.axes_list:
            ax.clear() # clear() полнее чем cla()
            # Удаляем старые colorbars, если они были
            # (в matplotlib это сложно, проще очистить фигуру, но пока так)

    def draw_plot(self, plot_data: dict):
        """Рисует 1D или 2D график."""
        target_ax_idx = plot_data.get("ax_index", 0)
        if target_ax_idx >= len(self.axes_list): target_ax_idx = 0
        ax = self.axes_list[target_ax_idx]
        
        plot_type = plot_data.get("plot_type", "errorbar")
        label = plot_data.get("label", "")
        
        # --- 1D ERRORBAR ---
        if plot_type == "errorbar":
            ax.errorbar(
                plot_data.get("x", []),
                plot_data.get("y", []),
                xerr=plot_data.get("x_err", None),
                yerr=plot_data.get("y_err", None),
                label=label,
                linestyle='-', marker='.', capsize=3
            )
            ax.grid(True)
            if plot_data.get("xscale") == "log": ax.set_xscale('log')
            if plot_data.get("yscale") == "log": ax.set_yscale('log')
            
            # Легенда
            if label: ax.legend()

        # --- 2D PCOLOR (Heatmap) ---
        elif plot_type == "pcolor":
            # Подготовка данных для pcolormesh
            X = plot_data.get("x") # Границы бинов X
            Y = plot_data.get("y") # Границы бинов Y
            Z = plot_data.get("z") # Значения (2D массив)
            
            # Логарифмическая шкала цвета (Z)
            norm = None
            if plot_data.get("zscale") == "log":
                # Защита от 0 и отрицательных для LogNorm
                vmin = np.min(Z[Z > 0]) if np.any(Z > 0) else 1e-5
                vmax = np.max(Z)
                norm = LogNorm(vmin=vmin, vmax=vmax)
            else:
                norm = Normalize(vmin=np.min(Z), vmax=np.max(Z))

            # Рисуем карту
            # shading='flat' требует, чтобы X и Y были на 1 больше Z по размеру (границы)
            # или 'nearest'/'auto' для центров.
            # В MATLAB pcolor использует границы.
            pcm = ax.pcolormesh(X, Y, Z, norm=norm, cmap='jet', shading='auto')
            
            # Colorbar
            cbar = self.fig.colorbar(pcm, ax=ax)
            cbar.set_label(plot_data.get("zlabel", ""))
            
            ax.grid(False) # На картах сетка обычно мешает
            
            if plot_data.get("xscale") == "log": ax.set_xscale('log')
            if plot_data.get("yscale") == "log": ax.set_yscale('log')

        # --- Оформление ---
        ax.set_xlabel(plot_data.get("xlabel", ""))
        ax.set_ylabel(plot_data.get("ylabel", ""))
        ax.set_title(label)
        
        self.canvas.draw()
