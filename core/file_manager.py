"""
Менеджер файлов (External Drive Edition).
Формирует пути с учетом GeoSelection (RB3) и структуры dirflux_newStructure.
"""
import os
from . import config

def get_input_filenames(app_state, data_type='flux'):
    """
    Возвращает список путей к файлам для выбранных дней.
    """
    files = []
    base = config.BASE_DATA_PATH
    
    # --- 1. AUX DATA (MagParam) ---
    if data_type == 'aux':
        # Путь: .../SolarHelioParams/MagParam2.mat
        # Предполагаем, что эта папка лежит в корне dirflux_newStructure
        path = os.path.join(base, 'SolarHelioParams', 'MagParam2.mat')
        if os.path.exists(path):
            return [path]
        return []

    # --- 2. FLUX DATA (RBflux) ---
    if not app_state.pam_pers:
        return []

    sel = app_state.selection        # ItalianH
    ver = app_state.flux_version     # v09
    binn = app_state.stdbinning      # P3L4E4
    geo = app_state.geo_selection    # RB3 (Важно! Добавили это)
    
    for day in app_state.pam_pers:
        # Имя файла: RBflux_315_stdbinning_P3L4E4.mat
        fname = f"RBflux_{day}_stdbinning_{binn}.mat"
        
        # --- СТРУКТУРА ПУТЕЙ ---
        # User path: /Volumes/T7 Touch/dirflux_newStructure/RB3/days/day_315/ItalianH/Loc/Fluxdata/v09/...
        
        # Путь к папке версии
        # base / RB3 / days / day_315 / ItalianH / Loc / Fluxdata / v09
        ver_dir = os.path.join(base, geo, 'days', f"day_{day}", sel, 'Loc', 'Fluxdata', ver)
        
        # Внутри v09 файлы могут лежать в корне или в RBfullfluxes
        path_with_folder = os.path.join(ver_dir, 'RBfullfluxes', fname)
        path_direct = os.path.join(ver_dir, fname)

        # Проверка
        if os.path.exists(path_with_folder):
            files.append(path_with_folder)
        elif os.path.exists(path_direct):
            files.append(path_direct)
        else:
            # Отладка (выведется только 1 раз для первого файла)
            if len(files) == 0:
                print(f"DEBUG: Файл не найден: {fname}")
                print(f"Проверял пути:\n1) {path_with_folder}\n2) {path_direct}")
                # На всякий случай проверим, видит ли питон диск вообще
                if not os.path.exists(base):
                    print(f"КРИТИЧНО: Не найдена корневая папка: {base}")
    
    return files
