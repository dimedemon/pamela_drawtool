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
        fname = f"RBflux_{day}_stdbinning_{binn}.mat"
        
        # ВАРИАНТ А: Стандартная "плоская" структура
        # Base / ItalianH / Loc / Fluxdata / v09 / RBfullfluxes / File
        path_a = os.path.join(base, sel, 'Loc', 'Fluxdata', ver, 'RBfullfluxes', fname)
        
        # ВАРИАНТ Б: Структура "по дням" (как у вас)
        # Base / days / day_303 / ItalianH / Loc / Fluxdata / v09 / RBfullfluxes / File
        # (Иногда RBfullfluxes может не быть внутри v09, проверяем варианты)
        path_b = os.path.join(base, 'days', f"day_{day}", sel, 'Loc', 'Fluxdata', ver, 'RBfullfluxes', fname)
        
        # ВАРИАНТ В: То же, но без папки RBfullfluxes
        path_c = os.path.join(base, 'days', f"day_{day}", sel, 'Loc', 'Fluxdata', ver, fname)

        # Проверка
        if os.path.exists(path_a):
            files.append(path_a)
        elif os.path.exists(path_b):
            files.append(path_b)
        elif os.path.exists(path_c):
            files.append(path_c)
        else:
            # Если не нашли, выводим отладку (первый раз)
            if len(files) == 0: 
                print(f"DEBUG: Не могу найти файл для дня {day}.")
                print(f"Искал здесь:\n1) {path_a}\n2) {path_b}\n3) {path_c}")
    
    return files
