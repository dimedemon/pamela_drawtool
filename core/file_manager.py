"""
Менеджер Файлов (core/file_manager.py) - SMART EDITION

Поддерживает два типа структур:
1. MODERN (Рекомендуемая): Data/Geo/Selection/Binning/RBflux_Day.mat
2. LEGACY (Matlab): Data/Geo/day/day_Day/Selection/Loc/Binning/RBdayfluxes/RBflux_Day.mat
"""

import os
from . import config
from . import state

def get_input_filenames(app_state: state.ApplicationState, file_type: str = 'flux'):
    """
    Возвращает список полных путей к файлам.
    Проверяет Modern путь, затем Legacy путь.
    """
    
    full_paths = []
    
    # 1. Определяем список периодов (дней)
    if app_state.tbin == 'Separate Periods':
        periods = [app_state.period]
    else:
        periods = app_state.pam_pers
        if not periods: return []

    # 2. Формируем строку биннинга (P3L3E3)
    if app_state.ror_e == 2:
        er_str = f"R{app_state.eb}"
    else:
        er_str = f"E{app_state.eb}"
        
    # Очищаем название биннинга от лишнего (на всякий случай)
    # Если stdbinning уже содержит имя, используем его, иначе собираем
    if app_state.stdbinning:
        binning_name = app_state.stdbinning
    else:
        binning_name = f"stdbinning_P{app_state.pitchb}L{app_state.lb}{er_str}"
    
    # Убираем префикс 'stdbinning_', если он есть, для чистоты новой структуры
    clean_binning_name = binning_name.replace('stdbinning_', '')
    # Но для Legacy путей нам нужен префикс
    legacy_binning_name = binning_name if binning_name.startswith('stdbinning_') else f"stdbinning_{binning_name}"

    # 3. Цикл по дням
    for per in periods:
        filename_flux = f"RBflux_{per}.mat"
        
        # --- ВАРИАНТ А: MODERN (Чистый) ---
        # Data / RB3 / ItalianH / P3L3E3 / RBflux_200.mat
        path_modern = os.path.join(
            config.GEN_PATH,         # data/dirflux_newStructure
            app_state.geo_selection, # RB3
            app_state.selection,     # ItalianH
            clean_binning_name,      # P3L3E3
            filename_flux
        )
        
        # --- ВАРИАНТ Б: LEGACY (Matlab Style) ---
        # Data / RB3 / day / day_200 / ItalianH / Loc / stdbinning_P3L3E3 / RBdayfluxes / RBflux_200.mat
        if app_state.tbin == 'Separate Periods':
            per_folder = str(per)
        else:
            per_folder = f"{app_state.tbin}_{per}" # day_200

        path_legacy = os.path.join(
            config.GEN_PATH,
            app_state.geo_selection, # RB3
            app_state.tbin,          # day
            per_folder,              # day_200
            app_state.selection,     # ItalianH
            'Loc',
            legacy_binning_name,     # stdbinning_P3L3E3
            'RBdayfluxes' if app_state.tbin == 'day' else 'RBfullfluxes',
            filename_flux
        )

        # --- ЛОГИКА ВЫБОРА ---
        if os.path.exists(path_modern):
            full_paths.append(path_modern)
            # print(f"Найден (Modern): {path_modern}") # Debug
        elif os.path.exists(path_legacy):
            full_paths.append(path_legacy)
            # print(f"Найден (Legacy): {path_legacy}") # Debug
        else:
            # Если файл не найден нигде, добавляем Modern путь (чтобы ошибка была понятной)
            # или пропускаем. Лучше добавить, чтобы processing.py выдал ошибку.
            full_paths.append(path_modern)

    return full_paths
