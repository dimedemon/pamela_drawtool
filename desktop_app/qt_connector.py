"""
Qt Коннектор (Фаза 2)

Этот класс является "клеем" между "безголовым" ядром (ApplicationState)
и GUI (PyQt).

Он слушает "чистые" сигналы blinker от ядра и "пере-излучает" (re-emits)
их как сигналы PyQt, на которые могут подписаться виджеты.
"""

from PyQt5.QtCore import QObject, pyqtSignal
from core.state import ApplicationState

class QtConnector(QObject):
    """
    Класс-посредник (MVVM-ViewModel для Qt).
    """
    
    # --- Сигналы PyQt ---
    # Мы дублируем сигналы из ApplicationState, но уже как pyqtSignal
    
    # Из pan00_InputDataSource
    gen_changed = pyqtSignal(int)
    
    # Из pan01_set02_Selections
    selection_changed = pyqtSignal(str)
    geo_selection_changed = pyqtSignal(str)
    
    # Из pan01_set03_Binnings
    stdbinning_changed = pyqtSignal(str)
    flux_version_changed = pyqtSignal(str)

    
    tbin_changed = pyqtSignal(str)
    period_changed = pyqtSignal(str)

    l_changed = pyqtSignal(list)
    l_max_changed = pyqtSignal(float)

    pitch_changed = pyqtSignal(list)
    pitch_max_changed = pyqtSignal(list)
    d_alpha_changed = pyqtSignal(float)

    e_changed = pyqtSignal(list)
    e_max_changed = pyqtSignal(list)
    rig_changed = pyqtSignal(list)
    rig_max_changed = pyqtSignal(list)
    d_e_changed = pyqtSignal(float)
    is_e_changed = pyqtSignal(bool)
    # (Мы добавим сюда больше сигналов по мере необходимости)
    
    def __init__(self, app_state: ApplicationState):
        """
        Инициализирует коннектор и "подписывается" на сигналы ядра.
        """
        super().__init__()
        self._app_state = app_state
        
        print("QtConnector: Подключение к сигналам ядра...")
        
        # --- Подписки (Blinker -> PyQt) ---
        
        # gen_changed
        self._app_state.gen_changed.connect(self._on_gen_changed)
        
        # selection_changed
        self._app_state.selection_changed.connect(self._on_selection_changed)
        
        # geo_selection_changed
        self._app_state.geo_selection_changed.connect(self._on_geo_selection_changed)
        
        # stdbinning_changed
        self._app_state.stdbinning_changed.connect(self._on_stdbinning_changed)
        
        # flux_version_changed
        self._app_state.flux_version_changed.connect(self._on_flux_version_changed)

        self._app_state.tbin_changed.connect(self._on_tbin_changed)
        self._app_state.period_changed.connect(self._on_period_changed)

        self._app_state.l_changed.connect(self._on_l_changed)
        self._app_state.l_max_changed.connect(self._on_l_max_changed)

        self._app_state.pitch_changed.connect(self._on_pitch_changed)
        self._app_state.pitch_max_changed.connect(self._on_pitch_max_changed)
        self._app_state.d_alpha_changed.connect(self._on_d_alpha_changed)

        self._app_state.e_changed.connect(self._on_e_changed)
        self._app_state.e_max_changed.connect(self._on_e_max_changed)
        self._app_state.rig_changed.connect(self._on_rig_changed)
        self._app_state.rig_max_changed.connect(self._on_rig_max_changed)
        self._app_state.d_e_changed.connect(self._on_d_e_changed)
        self._app_state.is_e_changed.connect(self._on_is_e_changed)

    # --- Методы-излучатели (Emitters) ---
    # Эти функции вызываются сигналом blinker и излучают сигнал PyQt

    def _on_gen_changed(self, sender, **kwargs):
        self.gen_changed.emit(kwargs.get('value'))

    def _on_selection_changed(self, sender, **kwargs):
        self.selection_changed.emit(kwargs.get('value'))

    def _on_geo_selection_changed(self, sender, **kwargs):
        self.geo_selection_changed.emit(kwargs.get('value'))
    
    def _on_stdbinning_changed(self, sender, **kwargs):
        self.stdbinning_changed.emit(kwargs.get('value'))
        
    def _on_flux_version_changed(self, sender, **kwargs):
        self.flux_version_changed.emit(kwargs.get('value'))
        
    def _on_tbin_changed(self, sender, **kwargs):
        self.tbin_changed.emit(kwargs.get('value'))
        
    def _on_period_changed(self, sender, **kwargs):
        self.period_changed.emit(kwargs.get('value'))

    def _on_l_changed(self, sender, **kwargs):
        self.l_changed.emit(kwargs.get('value'))
        
    def _on_l_max_changed(self, sender, **kwargs):
        self.l_max_changed.emit(kwargs.get('value'))

    def _on_pitch_changed(self, sender, **kwargs):
        self.pitch_changed.emit(kwargs.get('value'))
        
    def _on_pitch_max_changed(self, sender, **kwargs):
        self.pitch_max_changed.emit(kwargs.get('value'))
        
    def _on_d_alpha_changed(self, sender, **kwargs):
        self.d_alpha_changed.emit(kwargs.get('value'))

    def _on_e_changed(self, sender, **kwargs):
        self.e_changed.emit(kwargs.get('value'))
        
    def _on_e_max_changed(self, sender, **kwargs):
        self.e_max_changed.emit(kwargs.get('value'))
        
    def _on_rig_changed(self, sender, **kwargs):
        self.rig_changed.emit(kwargs.get('value'))
        
    def _on_rig_max_changed(self, sender, **kwargs):
        self.rig_max_changed.emit(kwargs.get('value'))
        
    def _on_d_e_changed(self, sender, **kwargs):
        self.d_e_changed.emit(kwargs.get('value'))
        
    def _on_is_e_changed(self, sender, **kwargs):
        self.is_e_changed.emit(kwargs.get('value'))
