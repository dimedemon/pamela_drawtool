"""
Qt Коннектор (Фаза 2) - ПОЛНЫЙ (со всеми сигналами)

Этот класс является "клеем" между "безголовым" ядром (ApplicationState)
и GUI (PyQt).
"""

from PyQt5.QtCore import QObject, pyqtSignal
from core.state import ApplicationState

class QtConnector(QObject):
    """
    Класс-посредник (MVVM-ViewModel для Qt).
    """
    
    # --- Сигналы PyQt ---
    
    # Input data source
    gen_changed = pyqtSignal(int)
    
    # Selections
    selection_changed = pyqtSignal(str)
    geo_selection_changed = pyqtSignal(str)
    
    # Binnings
    stdbinning_changed = pyqtSignal(str)
    flux_version_changed = pyqtSignal(str)
    
    # Temporal Parameters
    tbin_changed = pyqtSignal(str)
    period_changed = pyqtSignal(str)
    pam_pers_changed = pyqtSignal(list)
    fullday_changed = pyqtSignal(bool)
    passages_changed = pyqtSignal(list)
    
    # Geomagnetic parameters
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
    
    # --- Time parameters (НОВЫЕ) ---
    dt_changed = pyqtSignal(float)
    t_min_changed = pyqtSignal(str)
    t_max_changed = pyqtSignal(str)
    
    # Plot Controls
    plot_kind_changed = pyqtSignal(int)
    what_changed = pyqtSignal(int)
    units_changed = pyqtSignal(int)
    n_min_changed = pyqtSignal(int)
    
    def __init__(self, app_state: ApplicationState):
        super().__init__()
        self._app_state = app_state
        
        print("QtConnector: Подключение к сигналам ядра...")
        
        # --- Подписки (Blinker -> PyQt) ---
        
        self._app_state.gen_changed.connect(self._on_gen_changed)
        self._app_state.selection_changed.connect(self._on_selection_changed)
        self._app_state.geo_selection_changed.connect(self._on_geo_selection_changed)
        self._app_state.stdbinning_changed.connect(self._on_stdbinning_changed)
        self._app_state.flux_version_changed.connect(self._on_flux_version_changed)
        
        self._app_state.tbin_changed.connect(self._on_tbin_changed)
        self._app_state.period_changed.connect(self._on_period_changed)
        self._app_state.pam_pers_changed.connect(self._on_pam_pers_changed)
        self._app_state.fullday_changed.connect(self._on_fullday_changed)
        self._app_state.passages_changed.connect(self._on_passages_changed)
        
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
        
        # --- Time ---
        self._app_state.dt_changed.connect(self._on_dt_changed)
        self._app_state.t_min_changed.connect(self._on_t_min_changed)
        self._app_state.t_max_changed.connect(self._on_t_max_changed)
        
        self._app_state.plot_kind_changed.connect(self._on_plot_kind_changed)
        self._app_state.what_changed.connect(self._on_what_changed)
        self._app_state.units_changed.connect(self._on_units_changed)
        self._app_state.n_min_changed.connect(self._on_n_min_changed)

    # --- Методы-излучатели ---

    def _on_gen_changed(self, sender, **kwargs): self.gen_changed.emit(kwargs.get('value'))
    def _on_selection_changed(self, sender, **kwargs): self.selection_changed.emit(kwargs.get('value'))
    def _on_geo_selection_changed(self, sender, **kwargs): self.geo_selection_changed.emit(kwargs.get('value'))
    def _on_stdbinning_changed(self, sender, **kwargs): self.stdbinning_changed.emit(kwargs.get('value'))
    def _on_flux_version_changed(self, sender, **kwargs): self.flux_version_changed.emit(kwargs.get('value'))
    
    def _on_tbin_changed(self, sender, **kwargs): self.tbin_changed.emit(kwargs.get('value'))
    def _on_period_changed(self, sender, **kwargs): self.period_changed.emit(kwargs.get('value'))
    def _on_pam_pers_changed(self, sender, **kwargs): self.pam_pers_changed.emit(kwargs.get('value'))
    def _on_fullday_changed(self, sender, **kwargs): self.fullday_changed.emit(kwargs.get('value'))
    def _on_passages_changed(self, sender, **kwargs): self.passages_changed.emit(kwargs.get('value'))
        
    def _on_l_changed(self, sender, **kwargs): self.l_changed.emit(kwargs.get('value'))
    def _on_l_max_changed(self, sender, **kwargs): self.l_max_changed.emit(kwargs.get('value'))
    def _on_pitch_changed(self, sender, **kwargs): self.pitch_changed.emit(kwargs.get('value'))
    def _on_pitch_max_changed(self, sender, **kwargs): self.pitch_max_changed.emit(kwargs.get('value'))
    def _on_d_alpha_changed(self, sender, **kwargs): self.d_alpha_changed.emit(kwargs.get('value'))
    
    def _on_e_changed(self, sender, **kwargs): self.e_changed.emit(kwargs.get('value'))
    def _on_e_max_changed(self, sender, **kwargs): self.e_max_changed.emit(kwargs.get('value'))
    def _on_rig_changed(self, sender, **kwargs): self.rig_changed.emit(kwargs.get('value'))
    def _on_rig_max_changed(self, sender, **kwargs): self.rig_max_changed.emit(kwargs.get('value'))
    def _on_d_e_changed(self, sender, **kwargs): self.d_e_changed.emit(kwargs.get('value'))
    def _on_is_e_changed(self, sender, **kwargs): self.is_e_changed.emit(kwargs.get('value'))
    
    # --- Time ---
    def _on_dt_changed(self, sender, **kwargs): self.dt_changed.emit(kwargs.get('value'))
    def _on_t_min_changed(self, sender, **kwargs): self.t_min_changed.emit(kwargs.get('value'))
    def _on_t_max_changed(self, sender, **kwargs): self.t_max_changed.emit(kwargs.get('value'))
    
    def _on_plot_kind_changed(self, sender, **kwargs): self.plot_kind_changed.emit(kwargs.get('value'))
    def _on_what_changed(self, sender, **kwargs): self.what_changed.emit(kwargs.get('value'))
    def _on_units_changed(self, sender, **kwargs): self.units_changed.emit(kwargs.get('value'))
    def _on_n_min_changed(self, sender, **kwargs): self.n_min_changed.emit(kwargs.get('value'))
