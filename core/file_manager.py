"""
Менеджер Файлов (core/file_manager.py)

Порт getInputFilenames.m.
Отвечает за генерацию путей к файлам и списков имен файлов
на основе текущего состояния приложения (ApplicationState).
"""

import os
from . import config
from . import state

def get_input_filenames(app_state: state.ApplicationState, file_type: str = 'flux'):
    """
    Генерирует список файлов и базовый путь к ним.
    
    Args:
        app_state: Текущее состояние приложения.
        file_type: Тип файлов ('flux', 'aux', 'sat', 'pre').
        
    Returns:
        tuple: (list_of_filenames, full_folder_path)
    """
    
    # 1. Определяем часть пути для биннинга (binningpath)
    # Логика RorE (Energy vs Rigidity)
    if app_state.ror_e == 2: # 2 = R
        er_str = f"R{app_state.eb}"
    else: # 1 = E
        er_str = f"E{app_state.eb}"

    # Логика версий (v09 -> 9.0)
    try:
        version_num = float(app_state.flux_version.replace('v', ''))
    except ValueError:
        version_num = 9.0 # Fallback

    if version_num < 5.0:
        # Старый формат: stdbinning33e3
        binning_path = f"stdbinning{app_state.pitchb}{app_state.lb}e{app_state.eb}"
    else:
        # Новый формат: stdbinning_P3L3E3
        binning_path = f"stdbinning_P{app_state.pitchb}L{app_state.lb}{er_str}"

    # 2. Определяем папку категории потоков (FCpath)
    if app_state.tbin == 'Separate Periods':
        fc_path = 'RBfullfluxes'
    else:
        fc_path = f"RB{app_state.tbin}fluxes"

    # 3. Собираем полный путь к папке
    # Для 'pre' и 'aux' пути могут отличаться, но пока следуем логике flux
    base_path = os.path.join(
        config.GEN_PATH, 
        'Loc', 
        app_state.flux_version,
        app_state.selection, 
        binning_path, 
        fc_path
    )

    # 4. Генерируем список имен файлов (filenames)
    filenames = []
    
    # Используем список дней/периодов из состояния
    # Если 'Separate Periods', используем app_state.period
    # Иначе используем app_state.pam_pers
    
    if app_state.tbin == 'Separate Periods':
        periods = [app_state.period]
    else:
        periods = app_state.pam_pers
        # Защита от пустого списка (как было в processing.py)
        if not periods:
            periods = [200] # Тестовое значение по умолчанию

    # --- Генерация имен в зависимости от типа ---
    
    if file_type == 'flux':
        # Пример: RBflux_200.mat
        for per in periods:
            filenames.append(f"RBflux_{per}.mat")
            
    elif file_type == 'sat':
        # Пример: SatData_200.mat (как в MATLAB case 'sat')
        # Путь для sat может отличаться, в MATLAB он строится иначе:
        # path = [GENPATH 'SatData\'];
        # Но здесь мы пока оставим общую логику, если нужно - поправим
        base_path = os.path.join(config.GEN_PATH, 'SatData')
        for per in periods:
            filenames.append(f"SatData_{per}.mat")
            
    elif file_type == 'aux':
        # Пример: dirflux_200_pass_1_aux.mat
        # Требует логики пролетов (passages)
        # Пока заглушка для дней
        base_path = os.path.join(
            config.GEN_PATH, 
            'Loc', 
            app_state.flux_version,
            app_state.selection, 
            'preFluxdata'
        )
        for per in periods:
            # В MATLAB здесь сложная логика с day_.../dirflux_...
            # Мы вернемся к этому, когда будем делать Aux графики
            day_path = os.path.join(base_path, f"day_{per}")
            filenames.append(f"dirflux_{per}_gen.mat") # Упрощено
            
    # TODO: Добавить case 'pre' и другие, если понадобятся

    return filenames, base_path
