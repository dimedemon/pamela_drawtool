"""
Виджет Matplotlib (Фаза 6 - HISTOGRAM SUPPORT)
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
            ax.clear()

    def draw_plot(self, plot_data: dict):
        """Рисует график в зависимости от plot_type."""
        target_ax_idx = plot_data.get("ax_index", 0)
        if target_ax_idx >= len(self.axes_list): target_ax_idx = 0
        ax = self.axes_list[target_ax_idx]
        
        plot_type = plot_data.get("plot_type", "errorbar")
        label = plot_data.get("label", "")
        
        # --- 1. ERRORBAR (Lines) ---
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
            if label: ax.legend()

        # --- 2. PCOLOR (Maps) ---
        elif plot_type == "pcolor":
            X = plot_data.get("x")
            Y = plot_data.get("y")
            Z = plot_data.get("z")
            
            norm = None
            if plot_data.get("zscale") == "log":
                valid_Z = Z[Z > 0]
                vmin = np.min(valid_Z) if len(valid_Z) > 0 else 1e-5
                vmax = np.max(Z) if len(Z) > 0 else 1.0
                norm = LogNorm(vmin=vmin, vmax=vmax)
            else:
                norm = Normalize(vmin=np.min(Z), vmax=np.max(Z))

            pcm = ax.pcolormesh(X, Y, Z, norm=norm, cmap='jet', shading='auto')
            cbar = self.fig.colorbar(pcm, ax=ax)
            cbar.set_label(plot_data.get("zlabel", ""))
            
            ax.grid(False)
            if plot_data.get("xscale") == "log": ax.set_xscale('log')
            if plot_data.get("yscale") == "log": ax.set_yscale('log')

        # --- 3. HISTOGRAM (Distribution) - ВОТ ЭТО ДОБАВЛЯЕМ! ---
        elif plot_type == "histogram":
            data = plot_data.get("x", [])
            bins = plot_data.get("bins", 50)
            
            # Рисуем гистограмму
            # alpha - прозрачность (чтобы видеть наложения)
            # density=False - по оси Y будет количество (Counts), а не вероятность
            ax.hist(data, bins=bins, alpha=0.7, edgecolor='black', label=label)
            
            ax.legend(loc='best')
            ax.grid(True, axis='y', alpha=0.5)
            
            # Если нужно лог-распределение по X (часто нужно для потоков)
            # if plot_data.get("xscale") == "log": ax.set_xscale('log')

        # --- Оформление ---
        ax.set_xlabel(plot_data.get("xlabel", ""))
        ax.set_ylabel(plot_data.get("ylabel", ""))
        
        if plot_type == "pcolor" and label:
            ax.set_title(label)
        
        self.canvas.draw()
