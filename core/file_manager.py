"""
Менеджер файлов.
Отвечает за поиск и формирование путей к данным.
"""
import os
from . import config

def get_input_filenames(app_state, data_type='flux'):
    """
    Возвращает список полных путей к файлам для выбранных дней.
    data_type: 'flux' (RBflux) или 'aux' (MagParam).
    """
    files = []
    
    # --- 1. AUX DATA (MagParam) ---
    if data_type == 'aux':
        # Обычно это один файл на все времена
        path = os.path.join(config.BASE_DATA_PATH, 'SolarHelioParams', 'MagParam2.mat')
        if os.path.exists(path):
            return [path]
        return []

    # --- 2. FLUX DATA (RBflux) ---
    if not app_state.pam_pers:
        return []

    sel = app_state.selection       # ItalianH
    ver = app_state.flux_version    # v09
    binn = app_state.stdbinning     # P3L4E4
    
    # Базовые папки
    base = config.BASE_DATA_PATH
    
    for day in app_state.pam_pers:
