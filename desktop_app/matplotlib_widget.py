"""
Виджет Matplotlib (Фаза 4 - IMPROVED)

Добавлен NavigationToolbar и динамическая смена макета.
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

class MplCanvas(QWidget):
    """
    Виджет Matplotlib с поддержкой тулбара и смены сетки.
    """
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        super(MplCanvas, self).__init__(parent)

        # 1. Наводим красоту (стиль графиков)
        try:
            plt.style.use('seaborn-v0_8-darkgrid') # Или 'ggplot', 'bmh'
        except:
            pass # Если стиль не найден, используем стандартный

        # Настройки шрифтов
        plt.rcParams.update({'font.size': 10, 'axes.titlesize': 12})

        # 2. Создаем фигуру
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.canvas = FigureCanvas(self.fig)
        
        # 3. Добавляем Toolbar (Зум, Пан, Сохранение)
        self.toolbar = NavigationToolbar(self.canvas, self)

        # 4. Макет
        layout = QVBoxLayout()
        layout.addWidget(self.toolbar) # Панель инструментов сверху
        layout.addWidget(self.canvas)  # Холст снизу
        self.setLayout(layout)
        
        # Инициализируем оси
        self.axes_list = []
        self.set_layout_mode(1) # По умолчанию 1 график

    def set_layout_mode(self, mode):
        """
        Переключает режим отображения:
        mode=1 -> 1 график (1x1)
        mode=4 -> 4 графика (2x2)
        """
        self.fig.clf() # Очищаем фигуру полностью
        self.axes_list = []
        
        if mode == 1:
            # Один большой график
            ax = self.fig.add_subplot(1, 1, 1)
            self.axes_list.append(ax)
        elif mode == 4:
            # Сетка 2x2
            for i in range(1, 5):
                ax = self.fig.add_subplot(2, 2, i)
                self.axes_list.append(ax)
        
        self.fig.tight_layout()
        self.canvas.draw()

    def clear_all_axes(self):
        """Очищает содержимое осей (не удаляя сами оси)."""
        for ax in self.axes_list:
            ax.cla()
            ax.grid(True)

    def draw_plot(self, plot_data: dict):
        """
        Рисует график.
        """
        # Определяем, на каких осях рисовать
        target_ax_idx = plot_data.get("ax_index", 0)
        
        # Если мы в режиме "1 график", но данные просят 2-й или 3-й,
        # мы все равно рисуем на 1-м (наложение), либо игнорируем.
        # Давайте рисовать на текущем активном:
        if target_ax_idx >= len(self.axes_list):
            target_ax_idx = 0 # Fallback на первый график
            
        ax = self.axes_list[target_ax_idx]
        
        plot_type = plot_data.get("plot_type", "errorbar")
        
        # --- Рисование ---
        if plot_type == "errorbar":
            ax.errorbar(
                plot_data.get("x", []),
                plot_data.get("y", []),
                xerr=plot_data.get("x_err", None),
                yerr=plot_data.get("y_err", None),
                label=plot_data.get("label", ""),
                linestyle='-',
                marker='.',
                capsize=3 # Красивые "шапочки" у баров ошибок
            )
        
        # --- Оформление ---
        if plot_data.get("xscale") == "log": ax.set_xscale('log')
        if plot_data.get("yscale") == "log": ax.set_yscale('log')
            
        ax.set_xlabel(plot_data.get("xlabel", ""))
        ax.set_ylabel(plot_data.get("ylabel", ""))
        ax.set_title(plot_data.get("label", ""))
        
        # Включаем легенду, если есть лейблы
        if ax.get_legend_handles_labels()[1]:
            ax.legend()
            
        self.canvas.draw()
