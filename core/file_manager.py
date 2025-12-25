"""
Менеджер файлов (SMART STRUCTURE EDITION).
Строит путь к файлам на основе иерархии dirflux_newStructure.
"""
import os
from . import config

def get_input_filenames(app_state, data_type='flux'):
    files = []
    base = config.BASE_DATA_PATH # Ожидается "/Volumes/T7 Touch"
    
    print(f"\n[FILE MANAGER] База поиска: {base}")
    
    # === AUX DATA ===
    if data_type == 'aux':
        # Ищем MagParam2.mat в стандартном месте этой структуры
        # Обычно это: dirflux_newStructure / SolarHelioParams / MagParam2.mat
        p = os.path.join(base, 'dirflux_newStructure', 'SolarHelioParams', 'MagParam2.mat')
        if os.path.exists(p):
            return [p]
        # Резервный поиск (если лежит в корне)
        p_root = os.path.join(base, 'MagParam2.mat')
        if os.path.exists(p_root):
             return [p_root]
        return []

    # === FLUX DATA ===
    if not app_state.pam_pers: 
        print("[FILE MANAGER] Нет выбранных дней.")
        return []

    # 1. Считываем параметры селекции из интерфейса
    geo = app_state.geo_selection   # "RB3", "POLAR8" и т.д.
    sel = app_state.selection       # "ItalianH"
    ver = app_state.flux_version    # "v09" (обычно задано в state)
    
    # Если версия пустая, ставим дефолт v09
    if not ver: ver = 'v09'

    # Биннинг для формирования имени файла
    binn = app_state.stdbinning     # "P3L4E4"

    print(f"[FILE MANAGER] Параметры: Geo={geo}, Sel={sel}, Ver={ver}")

    # 2. Пробегаем по выбранным дням
    for day in app_state.pam_pers:
        # Формируем имя файла
        # Обычно: RBflux_Day192_stdbinning_P3L4E4.mat
        # Но иногда бывает просто RBflux_Day192.mat. Проверим оба.
        fname_long = f"RBflux_Day{day}_stdbinning_{binn}.mat"
        fname_short = f"RBflux_Day{day}.mat"
        
        # СТРОИМ ПУТЬ
        # /Volumes/T7 Touch/dirflux_newStructure/RB3/days/day_192/ItalianH/Loc/Fluxdata/v09
        day_folder = f"day_{day}"
        
        dir_path = os.path.join(base, 'dirflux_newStructure', geo, 'days', day_folder, sel, 'Loc', 'Fluxdata', ver)
        
        # Проверяем существование папки
        if not os.path.exists(dir_path):
            print(f"  [-] Папка не найдена: {dir_path}")
            continue

        # Ищем файл внутри
        # Иногда файлы лежат в подпапке 'RBfullfluxes', иногда прямо в 'v09'
        candidates = [
            os.path.join(dir_path, fname_long),                 # Прямо в v09 (длинное имя)
            os.path.join(dir_path, 'RBfullfluxes', fname_long), # В подпапке (длинное имя)
            os.path.join(dir_path, fname_short),                # Прямо в v09 (короткое имя)
            os.path.join(dir_path, 'RBfullfluxes', fname_short) # В подпапке (короткое имя)
        ]
        
        found = False
        for p in candidates:
            if os.path.exists(p):
                files.append(p)
                print(f"  [+] Нашел: .../{day_folder}/.../{os.path.basename(p)}")
                found = True
                break
        
        if not found:
             print(f"  [-] Файл не найден в {dir_path}")

    print(f"[FILE MANAGER] Итог: {len(files)} файлов готово к загрузке.")
    return files
