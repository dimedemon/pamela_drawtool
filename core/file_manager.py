"""
Менеджер файлов (FLEXIBLE FILENAME EDITION).
1. Работает с config.BASE_DATA_PATH (ваша папка PAMELA_DATA).
2. Поддерживает имена файлов "RBflux_Day192..." И "RBflux_192..." (без Day).
3. Выводит подробный лог, если папка есть, а файл не найден.
"""
import os
from . import config

def get_input_filenames(app_state, data_type='flux'):
    files = []
    base = config.BASE_DATA_PATH # /Volumes/T7 Touch/PAMELA_DATA
    
    print(f"\n[FILE MANAGER] Поиск данных в: {base}")

    # === AUX DATA (MagParam) ===
    if data_type == 'aux':
        # Пытаемся найти MagParam2.mat через конфиг (он знает где искать)
        if config.MAGPARAM_FILE and os.path.exists(config.MAGPARAM_FILE):
            return [config.MAGPARAM_FILE]
        return []

    # === FLUX DATA (Потоки) ===
    if not app_state.pam_pers: 
        print("[FILE MANAGER] ⚠️ Не выбраны дни для построения!")
        return []

    # 1. Параметры из интерфейса
    geo = app_state.geo_selection   # RB3
    sel = app_state.selection       # ItalianH
    ver = app_state.flux_version or 'v09'
    binn = app_state.stdbinning     # P3L4E4

    print(f"[FILE MANAGER] Конфигурация: Geo={geo}, Sel={sel}, Ver={ver}, Bin={binn}")

    # 2. Перебор дней
    for day in app_state.pam_pers:
        # Формируем путь к ПАПКЕ дня
        # Структура: dirflux_newStructure / RB3 / days / day_192 / ItalianH / Loc / Fluxdata / v09
        day_folder_name = f"day_{day}"
        
        # Пробуем найти папку внутри dirflux_newStructure
        # Путь 1: dirflux_newStructure/RB3...
        path_structure = os.path.join(base, 'dirflux_newStructure', geo, 'days', day_folder_name, sel, 'Loc', 'Fluxdata', ver)
        
        # Путь 2: Прямо в корне (на всякий случай)
        path_root = os.path.join(base, geo, 'days', day_folder_name, sel, 'Loc', 'Fluxdata', ver)

        target_dir = None
        if os.path.exists(path_structure):
            target_dir = path_structure
        elif os.path.exists(path_root):
            target_dir = path_root

        if not target_dir:
            print(f"  [-] Папка не найдена: .../{day_folder_name}/{sel}/.../{ver}")
            # print(f"      Искал тут: {path_structure}")
            continue

        # 3. Ищем ФАЙЛ внутри папки (Гибкий поиск)
        # Варианты имен файлов:
        candidates = [
            f"RBflux_{day}_stdbinning_{binn}.mat",      # Вариант БЕЗ Day (как у вас)
            f"RBflux_Day{day}_stdbinning_{binn}.mat",   # Вариант С Day (стандарт)
            f"RBflux_{day}.mat",                        # Короткий без Day
            f"RBflux_Day{day}.mat"                      # Короткий с Day
        ]

        found_file = None
        
        # А. Проверяем прямо в папке версии (v09)
        for cand in candidates:
            p = os.path.join(target_dir, cand)
            if os.path.exists(p):
                found_file = p
                break
        
        # Б. Если не нашли, проверяем подпапку RBfullfluxes (иногда бывает)
        if not found_file:
            for cand in candidates:
                p = os.path.join(target_dir, 'RBfullfluxes', cand)
                if os.path.exists(p):
                    found_file = p
                    break
        
        if found_file:
            files.append(found_file)
            print(f"  [+] День {day}: Файл найден! ({os.path.basename(found_file)})")
        else:
            print(f"  [-] День {day}: Папка есть, но файл не найден.")
            print(f"      Ожидались имена типа: {candidates[0]} или {candidates[1]}")
            # Выведем список файлов в папке, чтобы понять, что там лежит
            try:
                existing = os.listdir(target_dir)
                valid_ext = [f for f in existing if f.endswith('.mat')]
                if valid_ext:
                    print(f"      В папке лежат: {valid_ext[:3]} ...")
                else:
                    print(f"      Папка пуста или нет .mat файлов.")
            except: pass

    print(f"[FILE MANAGER] Итог: {len(files)} файлов отправлено на обработку.")
    return files
