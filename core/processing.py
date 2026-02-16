"""
Модуль Обработки (Processing Module) - DICT FIX + SMART RECOVERY
Исправлена ошибка доступа к ключам словаря .mat файла.
"""
import os
import numpy as np
from scipy.io import loadmat
from . import config
from . import state
from . import file_manager

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---
def _load_mat_file(file_path):
    if not os.path.exists(file_path): return None
    try: 
        # loadmat возвращает DICT
        return loadmat(file_path, squeeze_me=True, struct_as_record=False)
    except: return None

def _find_bin_indices(edges, values):
    if values is None or len(values) == 0: return np.array([], dtype=int)
    if not isinstance(values, (list, np.ndarray)): values = [values]
    indices = np.searchsorted(edges, values, side='right') - 1
    indices[indices < 0] = 0
    indices[indices >= len(edges) - 1] = len(edges) - 2
    return np.unique(indices)

# --- ЛОГИКА ПОСТРОЕНИЯ СПЕКТРОВ ---
def _generic_1d_plot(app_state, ax_index, mode='spectra'):
    print(f"\n[PROCESSING] -> Старт обработки _generic_1d_plot")

    # 1. Инициализация осей из конфига
    try:
        # Индексы в state 1-based, поэтому -1
        L_edges = config.BIN_INFO['Lbin'][app_state.lb - 1]
        P_edges = config.BIN_INFO['pitchbin'][app_state.pitchb - 1]
        
        if app_state.ror_e == 1: # Energy
            X_edges = config.BIN_INFO['Ebin'][app_state.eb - 1]
            x_label = "Kinetic Energy (GeV)"
        else: # Rigidity
            X_edges = config.BIN_INFO['Rig'][app_state.eb - 1] # Обычно совпадает индексом
            x_label = "Rigidity (GV)"
            
        X_centers = np.sqrt(X_edges[:-1] * X_edges[1:])
        print(f"[PROCESSING] Конфиг ожидает {len(X_centers)} точек по оси X.")
    except Exception as e:
        print(f"[ERROR] Ошибка инициализации бинов: {e}")
        return []

    # 2. Индексы выборки (Selection)
    target_l = app_state.l if (app_state.l and len(app_state.l) > 0) else [(L_edges[0] + L_edges[-1])/2]
    target_p = app_state.pitch if (app_state.pitch and len(app_state.pitch) > 0) else [45.0]

    L_indices = _find_bin_indices(L_edges, target_l)
    P_indices = _find_bin_indices(P_edges, target_p)

    # 3. Поиск файлов
    files = file_manager.get_input_filenames(app_state, 'flux')
    if not files: return []

    accumulated_spectra = []
    real_x_axis = None # Суррогатная ось, если биннинг не совпадет

    for fpath in files:
        mat = _load_mat_file(fpath)
        if mat is None: continue
        
        # Получаем ключи словаря (для дебага и поиска)
        mat_keys = mat.keys()
        
        # --- SMART VARIABLE SEARCH (DICT MODE) ---
        data_3d = None
        var_name = "Unknown"
        
        # Ищем переменную в ключах словаря
        if 'Flux' in mat_keys: 
            data_3d = mat['Flux']; var_name = "Flux"
        elif 'flux' in mat_keys: 
            data_3d = mat['flux']; var_name = "flux"
        elif 'Jday' in mat_keys:
            data_3d = mat['Jday']; var_name = "Jday"
            
            # --- АВТО-КОРРЕКЦИЯ Jday ---
            # Jday часто имеет структуру (Pitch, L, Energy) -> (3, 6, 16)
            # Нам нужно (Energy, L, Pitch)
            if data_3d.ndim == 3:
                # Эвристика: если 1-я ось маленькая (Pitch=3), а последняя большая (Energy=16)
                if data_3d.shape[0] < data_3d.shape[2]: 
                    print(f"    [AUTO-FIX] Транспонирую Jday {data_3d.shape} -> (Energy, L, Pitch)")
                    # axis 0->2 (Pitch в конец), axis 1->1 (L на месте), axis 2->0 (Energy в начало)
                    data_3d = np.transpose(data_3d, (2, 1, 0))
        
        elif 'J' in mat_keys:
            data_3d = mat['J']; var_name = "J"
            
        if data_3d is None:
            # Выводим реальные ключи файла, исключая служебные
            clean_keys = [k for k in mat_keys if not k.startswith('__')]
            print(f"    [WARN] В файле {os.path.basename(fpath)} нет Flux/Jday. Доступны: {clean_keys}")
            continue

        # --- ОБРАБОТКА РАЗМЕРНОСТЕЙ ---
        if data_3d.ndim != 3:
            print(f"    [WARN] {var_name} имеет странную размерность {data_3d.shape}. Пропуск.")
            continue
            
        # Проверка биннинга по энергии (ось 0)
        file_n_energy = data_3d.shape[0]
        config_n_energy = len(X_centers)
        
        # Если количество точек энергии в файле не совпадает с конфигом
        if file_n_energy != config_n_energy:
            print(f"    [WARN] Несовпадение бинов! Файл: {file_n_energy}, Конфиг: {config_n_energy}.")
            if real_x_axis is None:
                print("    [FIX] Создаю суррогатную ось X (линейную), чтобы отобразить данные.")
                # Делаем линейную шкалу от мин до макс энергии конфига, но с шагом файла
                real_x_axis = np.geomspace(X_centers[0], X_centers[-1], file_n_energy)

        # Вырезаем данные
        try:
            # Защита от выхода за границы индексов L и P
            # data_3d shape теперь (Energy, L, Pitch)
            valid_L = [i for i in L_indices if i < data_3d.shape[1]]
            valid_P = [i for i in P_indices if i < data_3d.shape[2]]
            
            if not valid_L or not valid_P:
                print(f"    [WARN] Индексы выходят за границы. L_file={data_3d.shape[1]}, P_file={data_3d.shape[2]}")
                continue

            # Срез: [Все энергии, Выбранные L, Выбранные P]
            # np.ix_ сложен для 3D, делаем поэтапно
            subset = data_3d[:, valid_L, :][:, :, valid_P]
            
            subset[subset == 0] = np.nan
            # Усредняем по L и Pitch (оси 1 и 2)
            daily_spectrum = np.nanmean(subset, axis=(1, 2))
            
            accumulated_spectra.append(daily_spectrum)
            
        except Exception as e:
            print(f"    [ERROR] Ошибка среза: {e}")
            continue

    # 4. СБОРКА РЕЗУЛЬТАТА
    if not accumulated_spectra:
        print("[PROCESSING] Данных нет после обработки.")
        return []

    all_spectra = np.array(accumulated_spectra)
    final_flux = np.nanmean(all_spectra, axis=0)
    
    # Выбор оси X (Конфиг или Суррогат)
    final_X = real_x_axis if real_x_axis is not None else X_centers
    
    # Финальная подгонка длин (на случай смешанных ошибок)
    min_len = min(len(final_X), len(final_flux))
    final_X = final_X[:min_len]
    final_flux = final_flux[:min_len]

    valid_mask = ~np.isnan(final_flux) & (final_flux > 0)
    
    if not np.any(valid_mask):
         print("[PROCESSING] Все данные NaN или 0.")
         return []

    print(f"[PROCESSING] График готов! Точек: {np.sum(valid_mask)}")

    return [{
        "ax_index": ax_index,
        "type": "spectra",
        "x_values": final_X[valid_mask],
        "y_values": final_flux[valid_mask],
        "y_err": np.zeros_like(final_flux[valid_mask]),
        "x_label": x_label,
        "y_label": f"Flux ({var_name})",
        "x_scale": "log", "y_scale": "log",
        "title": f"Spectrum (L={app_state.l}, P={app_state.pitch})",
        "label": f"N_days={len(files)}"
    }]

def get_plot_data(app_state, ax_index=0):
    pk = app_state.plot_kind
    if pk in [1, 2]: return _generic_1d_plot(app_state, ax_index)
    elif pk == 12: return [] 
    print(f"[WARN] PlotKind {pk} не поддерживается.")
    return []
