"""
Модуль Состояния (Фаза 1)

Хранит состояние приложения (замена getDRAWOPT) и использует
сигналы (замена DRAWOPTListenerManager) для уведомления об изменениях.

Использует 'blinker' для создания сигналов, не зависящих от GUI.
"""

from blinker import signal
from . import config  # Импортируем наш config.py

class ApplicationState:
    """
    Класс, хранящий полное состояние GUI.
    При изменении любого @property через .setter,
    он испускает (sends) сигнал blinker, на который
    могут подписаться другие части программы (GUI, логгеры и т.д.).
    """
    
    # --- Создаем сигналы для КАЖДОГО поля ---
    # (Имя сигнала = 'имя_поля_changed')
    
    # Input data source
    gen_changed = signal('gen_changed')
    
    # Input params
    flux_version_changed = signal('flux_version_changed')
    aux_version_changed = signal('aux_version_changed')
    pre_version_changed = signal('pre_version_changed')
    gen_version_changed = signal('gen_version_changed')
    selection_changed = signal('selection_changed')
    geo_selection_changed = signal('geo_selection_changed')
    stdbinning_changed = signal('stdbinning_changed')
    pitchb_changed = signal('pitchb_changed')
    lb_changed = signal('lb_changed')
    eb_changed = signal('eb_changed')
    

    # Period parameters
    period_changed = signal('period_changed')
    tbin_changed = signal('tbin_changed')

    # Geomagnetic parameters
    l_changed = signal('l_changed')
    l_max_changed = signal('l_max_changed')
    pitch_changed = signal('pitch_changed')
    pitch_max_changed = signal('pitch_max_changed')
    d_alpha_changed = signal('d_alpha_changed')

    e_changed = signal('e_changed')
    e_max_changed = signal('e_max_changed')
    rig_changed = signal('rig_changed')
    rig_max_changed = signal('rig_max_changed')
    d_e_changed = signal('d_e_changed')
    is_e_changed = signal('is_e_changed') # Для E/R биннинга

    units_changed = signal('units_changed')
    n_min_changed = signal('n_min_changed')
    
    # (pitch, E, Rig - добавим позже)
    # ... (добавим остальные по мере необходимости)

    # Plot types parameters
    plot_kind_changed = signal('plot_kind_changed')
    what_changed = signal('what_changed')
    pam_pers_changed = signal('pam_pers_changed')
    fullday_changed = signal('fullday_changed')
    # ... (добавим остальные)

    def __init__(self):
        """
        Инициализирует состояние значениями по умолчанию.
        (Портировано из initializeDRAWOPT)
        """
        print("Инициализация ApplicationState...")
        
        # --- Приватные переменные для хранения состояния ---
        self._gen = 1
        self._flux_version = 'v09'
        self._aux_version = 'v01'
        self._pre_version = 'v01'
        self._gen_version = 'v01'
        self._selection = 'ItalianH'
        self._geo_selection = 'RB3'
        self._stdbinning = 'P3L3E2'
        self._pitchb = 4
        self._lb = 3
        self._eb = 2
        
        self._period = ''
        self._tbin = 'day'
        
        self._plot_kind = 1
        self._what = 1
        
        self._l = []
        self._l_max = 1000.0

        self._pitch = []
        self._pitch_max = [] # В MATLAB это было отдельное поле
        self._d_alpha = 0.0

        # (Портировано из initializeDRAWOPT)
        self._e = []
        self._e_max = []
        self._rig = []
        self._rig_max = []
        self._d_e = 0.0
        self._is_e = True # E=true, R=false
        self._ror_e = 1   # 1=E, 2=R (для pan01_set03_Binnings)

        self._units = 1 # 0 = MeV, 1 = GeV (из pan02_set02_JunitsNmin)
        self._n_min = 0 # (из pan02_set02_JunitsNmin)
        self._pam_pers = [200] # (Список дней, по умолчанию 200)
        self._fullday = True   # (По умолчанию True)
        # ...
        self._plot_kind = 1
        
        # ... и так далее для всех полей из initializeDRAWOPT ...
        
        print("ApplicationState инициализирован.")

    # --- Свойства (Properties) для доступа к полям ---
    # (Это замена getDRAWOPT(field) и getDRAWOPT(field, value))

    @property
    def gen(self):
        return self._gen

    @gen.setter
    def gen(self, value):
        if self._gen != value:
            self._gen = value
            self.gen_changed.send(self, value=value) # Отправляем сигнал

    @property
    def flux_version(self):
        return self._flux_version

    @flux_version.setter
    def flux_version(self, value):
        if self._flux_version != value:
            self._flux_version = value
            self.flux_version_changed.send(self, value=value)

    @property
    def selection(self):
        return self._selection

    @selection.setter
    def selection(self, value):
        if self._selection != value:
            self._selection = value
            self.selection_changed.send(self, value=value)

    @property
    def geo_selection(self):
        return self._geo_selection

    @geo_selection.setter
    def geo_selection(self, value):
        if self._geo_selection != value:
            self._geo_selection = value
            self.geo_selection_changed.send(self, value=value)

    @property
    def stdbinning(self):
        return self._stdbinning

    @stdbinning.setter
    def stdbinning(self, value):
        if self._stdbinning != value:
            self._stdbinning = value
            self.stdbinning_changed.send(self, value=value)

    @property
    def pitchb(self):
        return self._pitchb

    @pitchb.setter
    def pitchb(self, value):
        if self._pitchb != value:
            self._pitchb = value
            self.pitchb_changed.send(self, value=value)

    @property
    def lb(self):
        return self._lb

    @lb.setter
    def lb(self, value):
        if self._lb != value:
            self._lb = value
            self.lb_changed.send(self, value=value)

    @property
    def eb(self):
        return self._eb

    @eb.setter
    def eb(self, value):
        if self._eb != value:
            self._eb = value
            self.eb_changed.send(self, value=value)
    
    @property
    def period(self):
        return self._period

    @period.setter
    def period(self, value):
        if self._period != value:
            self._period = value
            self.period_changed.send(self, value=value)

    @property
    def tbin(self):
        return self._tbin

    @tbin.setter
    def tbin(self, value):
        if self._tbin != value:
            self._tbin = value
            self.tbin_changed.send(self, value=value)
    @property
    def l(self):
        return self._l

    @l.setter
    def l(self, value):
        if self._l != value:
            self._l = value
            self.l_changed.send(self, value=value)

    @property
    def l_max(self):
        return self._l_max

    @l_max.setter
    def l_max(self, value):
        if self._l_max != value:
            self._l_max = value
            self.l_max_changed.send(self, value=value)

    @property
    def pitch(self):
        return self._pitch

    @pitch.setter
    def pitch(self, value):
        if self._pitch != value:
            self._pitch = value
            self.pitch_changed.send(self, value=value)

    @property
    def pitch_max(self):
        return self._pitch_max

    @pitch_max.setter
    def pitch_max(self, value):
        if self._pitch_max != value:
            self._pitch_max = value
            self.pitch_max_changed.send(self, value=value)

    @property
    def d_alpha(self):
        return self._d_alpha

    @d_alpha.setter
    def d_alpha(self, value):
        if self._d_alpha != value:
            self._d_alpha = value
            self.d_alpha_changed.send(self, value=value)

    @property
    def e(self): return self._e
    @e.setter
    def e(self, value):
        if self._e != value: self._e = value; self.e_changed.send(self, value=value)

    @property
    def e_max(self): return self._e_max
    @e_max.setter
    def e_max(self, value):
        if self._e_max != value: self._e_max = value; self.e_max_changed.send(self, value=value)

    @property
    def rig(self): return self._rig
    @rig.setter
    def rig(self, value):
        if self._rig != value: self._rig = value; self.rig_changed.send(self, value=value)

    @property
    def rig_max(self): return self._rig_max
    @rig_max.setter
    def rig_max(self, value):
        if self._rig_max != value: self._rig_max = value; self.rig_max_changed.send(self, value=value)

    @property
    def d_e(self): return self._d_e
    @d_e.setter
    def d_e(self, value):
        if self._d_e != value: self._d_e = value; self.d_e_changed.send(self, value=value)

    @property
    def is_e(self): return self._is_e
    @is_e.setter
    def is_e(self, value):
        if self._is_e != value: self._is_e = value; self.is_e_changed.send(self, value=value)
    @property
    def ror_e(self):
        return self._ror_e

    @ror_e.setter
    def ror_e(self, value):
        if self._ror_e != value:
            self._ror_e = value
            # (Мы пока не создавали сигнал ror_e_changed,
            # так как он используется только для binnings,
            # но можем добавить его позже, если понадобится)
            pass
    @property
    def plot_kind(self):
        return self._plot_kind

    @plot_kind.setter
    def plot_kind(self, value):
        if self._plot_kind != value:
            self._plot_kind = value
            self.plot_kind_changed.send(self, value=value)

    @property
    def what(self):
        return self._what

    @what.setter
    def what(self, value):
        if self._what != value:
            self._what = value
            self.what_changed.send(self, value=value)
    @property
    def units(self): return self._units
    @units.setter
    def units(self, value):
        if self._units != value: self._units = value; self.units_changed.send(self, value=value)

    @property
    def n_min(self): return self._n_min
    @n_min.setter
    def n_min(self, value):
        if self._n_min != value: self._n_min = value; self.n_min_changed.send(self, value=value)
    # ... (нужно будет добавить сеттеры/геттеры для ВСЕХ полей) ...
    # (RorE мы пока не используем, но Eb уже есть)
    @property
    def pam_pers(self):
        return self._pam_pers
        
    @pam_pers.setter
    def pam_pers(self, value):
        if self._pam_pers != value:
            self._pam_pers = value
            self.pam_pers_changed.send(self, value=value)

    @property
    def fullday(self):
        return self._fullday
        
    @fullday.setter
    def fullday(self, value):
        if self._fullday != value:
            self._fullday = value
            self.fullday_changed.send(self, value=value)
    def update_multiple(self, **kwargs):
        """
        Обновляет несколько полей сразу, отправляя сигнал 
        для каждого измененного поля.
        (Замена updateDRAWOPTAndUI / getDRAWOPT с неск. парами)
        """
        print(f"Обновление нескольких полей: {kwargs}")
        for key, value in kwargs.items():
            if hasattr(self, key):
                # setattr вызовет @setter, который отправит сигнал
                setattr(self, key, value)
            else:
                print(f"ВНИМАНИЕ: Попытка обновить несуществующее поле '{key}'")
