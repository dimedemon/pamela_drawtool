"""
Менеджер файлов (DEBUG EDITION).
Показывает каждый шаг поиска файлов и полные пути, которые проверяет программа.
"""
import os
from . import config

def get_input_filenames(app_state, data_type='flux'):
    files = []
    base = config.BASE_DATA_PATH 
    
    print(f"\n[FILE MANAGER] === НАЧАЛО ПОИСКА ===")
    print(f"[DEBUG PATH] Корневая папка (Base): {base}")

    # === AUX DATA (MagParam) ===
    if data_type == 'aux':
        if config.MAGPARAM_FILE and os.path.exists(config.MAGPARAM_FILE):
            return [config.MAGPARAM_FILE]
        return []

    # === FLUX DATA (Потоки) ===
    if not app_state.pam_pers: 
        print("[FILE MANAGER] ⚠️ Не выбраны дни для построения!")
        return []

    # 1. Параметры из интерфейса
    geo = app_state.geo_selection   # например: RB3
    sel = app_state.selection       # например: ItalianH
    ver = app_state.flux_version or 'v09'
    binn = app_state.stdbinning     # например: P3L4E4

    print(f"[DEBUG INFO] Geo='{geo}', Sel='{sel}', Ver='{ver}', Bin='{binn}'")

    # 2. Перебор дней
    for day in app_state.pam_pers:
        print(f"\n  > Обработка Дня: {day}")
        
        day_folder_name = f"day_{day}"
        
        # Формируем ожидаемые пути к папке дня
        # Вариант 1: Новая структура (с dirflux_newStructure)
        path_structure = os.path.join(base, 'dirflux_newStructure', geo, 'days', day_folder_name, sel, 'Loc', 'Fluxdata', ver)
        
        # Вариант 2: Старая структура (сразу в корне)
        path_root = os.path.join(base, geo, 'days', day_folder_name, sel, 'Loc', 'Fluxdata', ver)

        target_dir = None
        
        # ДЕБАГ ПРОВЕРКИ ПАПОК
        print(f"    [CHECK DIR 1] {path_structure}")
        if os.path.exists(path_structure):
            print("      -> НАЙДЕНО!")
            target_dir = path_structure
        else:
            print("      -> пусто")
            print(f"    [CHECK DIR 2] {path_root}")
            if os.path.exists(path_root):
                print("      -> НАЙДЕНО!")
                target_dir = path_root
            else:
                print("      -> пусто")

        if not target_dir:
            print(f"  [-] ПАПКА ДЛЯ ДНЯ {day} НЕ НАЙДЕНА ни по одному из путей.")
            continue

        # 3. Ищем ФАЙЛ внутри найденной папки
        candidates = [
            f"RBflux_{day}_stdbinning_{binn}.mat",      # Вариант 1 (ваш файл)
            f"RBflux_Day{day}_stdbinning_{binn}.mat",   # Вариант 2
            f"RBflux_{day}.mat"                         # Вариант 3
        ]

        found_file = None
        
        print(f"    [SEARCH FILE] Ищем один из: {candidates}")
        
        # А. Проверяем прямо в целевой папке
        for cand in candidates:
            p = os.path.join(target_dir, cand)
            # print(f"      [CHECK FILE] {p}") # Раскомментировать для супер-детальности
            if os.path.exists(p):
                found_file = p
                break
        
        # Б. Если не нашли, проверяем подпапку RBfullfluxes (иногда бывает)
        if not found_file:
            # print("      [INFO] Проверяем подпапку RBfullfluxes...")
            for cand in candidates:
                p = os.path.join(target_dir, 'RBfullfluxes', cand)
                if os.path.exists(p):
                    found_file = p
                    break
        
        if found_file:
            files.append(found_file)
            print(f"  [+] ФАЙЛ НАЙДЕН: {found_file}")
        else:
            print(f"  [-] Файл НЕ найден в папке {target_dir}")
            # Для помощи выведем, что там вообще лежит
            try:
                content = os.listdir(target_dir)
                mats = [f for f in content if f.endswith('.mat')]
                print(f"      В этой папке лежат ({len(mats)} шт): {mats[:3]} ...")
            except: pass

    print(f"[FILE MANAGER] Итог: найдено {len(files)} файлов.")
    return files
