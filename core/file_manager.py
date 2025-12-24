"""
Менеджер файлов (Local Smart Edition).
Ищет файлы внутри локальной папки data, понимая структуру dirflux.
"""
import os
from . import config

def get_input_filenames(app_state, data_type='flux'):
    files = []
    base = config.BASE_DATA_PATH # .../pamela_drawtool/data
    print(f"\n[DEBUG FileManager]")
    print(f"Базовая папка: {base}")
    # --- Aux Data ---
    if data_type == 'aux':
        # Ищем MagParam2.mat где угодно внутри data
        # (Самый надежный способ, если мы не знаем точную структуру)
        candidates = [
            os.path.join(base, 'SolarHelioParams', 'MagParam2.mat'),
            os.path.join(base, 'dirflux_newStructure', 'SolarHelioParams', 'MagParam2.mat')
        ]
        for p in candidates:
            if os.path.exists(p): return [p]
        return []

    # --- Flux Data ---
    if not app_state.pam_pers: return []

    geo = app_state.geo_selection    # RB3
    sel = app_state.selection        # ItalianH
    ver = app_state.flux_version     # v09
    binn = app_state.stdbinning      # P3L4E4
    
    for day in app_state.pam_pers:
        fname = f"RBflux_{day}_stdbinning_{binn}.mat"
        
        # Мы проверяем два варианта:
        # 1. Вы скопировали содержимое dirflux_newStructure прямо в data
        #    Путь: data/RB3/days/day_XXX/...
        path_1 = os.path.join(base, geo, 'days', f"day_{day}", sel, 'Loc', 'Fluxdata', ver)
        
        # 2. Вы скопировали саму папку dirflux_newStructure в data
        #    Путь: data/dirflux_newStructure/RB3/days/day_XXX/...
        path_2 = os.path.join(base, 'dirflux_newStructure', geo, 'days', f"day_{day}", sel, 'Loc', 'Fluxdata', ver)
        
        target_dir = None
        if os.path.exists(path_1): target_dir = path_1
        elif os.path.exists(path_2): target_dir = path_2
        
        if target_dir:
            # Внутри папки версии ищем файл (он может быть в RBfullfluxes или в корне)
            p_full = os.path.join(target_dir, 'RBfullfluxes', fname)
            p_root = os.path.join(target_dir, fname)
            
            if os.path.exists(p_full): files.append(p_full)
            elif os.path.exists(p_root): files.append(p_root)
            # else: print(f"DEBUG: File not found in {target_dir}")
        else:
            # Если это первый файл, выведем отладку, чтобы понять, куда вы положили данные
            if len(files) == 0:
                pass
                # print(f"DEBUG: Directory not found for day {day}")
                # print(f"Checked: {path_1}")
                # print(f"Checked: {path_2}")

    return files
