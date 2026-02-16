"""
Модуль Обработки (Processing Module) - ADAPTIVE DIMENSION SOLVER
Автоматически определяет оси (Energy, L, Pitch) на основе совпадения с конфигом.
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
    print(f"\n[PROCESSING] -> Старт обработки (Adaptive Mode)")

    # 1. Инициализация осей из конфига
    try:
        # Индексы state 1-based -> 0-based
        L_edges = config.BIN_INFO['Lbin'][app_state.lb - 1]
        P_edges = config.BIN_INFO['pitchbin'][app_state.pitchb - 1]
        
        if app_state.ror_e == 1: # Energy
            X_edges = config.BIN_INFO['Ebin'][app_state.eb - 1]
            x_label = "Kinetic Energy (GeV)"
        else: # Rigidity
            X_edges = config.BIN_INFO['Rig'][app_state.eb - 1]
            x_label = "Rigidity (GV)"
            
        X_centers = np.sqrt(X_edges[:-1] * X_edges[1:])
        config_n_E = len(X_centers)
        print(f"[PROCESSING] Конфиг: Energy={config_n_E} bins.")
    except Exception as e:
        print(f"[ERROR] Ошибка инициализации бинов: {e}")
        return []

    # 2. Индексы выборки
    target_l = app_state.l if (app_state.l and len(app_state.l) > 0) else [(L_edges[0] + L_edges[-1])/2]
    target_p = app_state.pitch if (app_state.pitch and len(app_state.pitch) > 0) else [45.0]

    L_indices = _find_bin_indices(L_edges, target_l)
    P_indices = _find_bin_indices(P_edges, target_p)
    print(f"[PROCESSING] Selected Indices -> L:{L_indices}, P:{P_indices}")

    # 3. Поиск файлов
    files = file_manager.get_input_filenames(app_state, 'flux')
    if not files: return []

    accumulated_spectra = []
    
    for fpath in files:
        mat = _load_mat_file(fpath)
        if mat is None: continue
        
        # Поиск переменной (Flux, flux, Jday, J)
        data_raw = None
        var_name = "Unknown"
        keys = mat.keys()
        
        for key in ['Flux', 'flux', 'Jday', 'J']:
            if key in keys:
                data_raw = mat[key]
                var_name = key
                break
        
        if data_raw is None:
            print(f"    [WARN] {os.path.basename(fpath)}: Переменные Flux/Jday не найдены.")
            continue

        if data_raw.ndim != 3:
            print(f"    [WARN] {var_name} имеет размерность {data_raw.shape} != 3. Пропуск.")
            continue

        # --- АДАПТИВНОЕ ОПРЕДЕЛЕНИЕ ОСЕЙ ---
        # Нам нужно привести данные к виду (Energy, L, Pitch)
        
        shape = data_raw.shape
        dims = [0, 1, 2]
        
        # 1. Ищем ось Энергии (совпадение с config_n_E)
        e_axis = -1
        if shape[0] == config_n_E: e_axis = 0
        elif shape[1] == config_n_E: e_axis = 1
        elif shape[2] == config_n_E: e_axis = 2
        
        if e_axis == -1:
            print(f"    [WARN] {os.path.basename(fpath)}: Не найдена ось длины {config_n_E}. Shape={shape}")
            # Fallback: предполагаем, что Energy - это ось 0 (стандарт)
            # Или создадим суррогатную ось, но пока пропустим для чистоты
            continue
            
        # 2. Оставшиеся оси распределяем между Pitch и L
        # Обычно Pitch < L. 
        rem_axes = [d for d in dims if d != e_axis] # Два оставшихся индекса
        
        size_a = shape[rem_axes[0]]
        size_b = shape[rem_axes[1]]
        
        if size_a < size_b:
            p_axis = rem_axes[0]
            l_axis = rem_axes[1]
        else:
            p_axis = rem_axes[1]
            l_axis = rem_axes[0]

        # 3. Транспонируем в (Energy, L, Pitch)
        # target order: [e_axis, l_axis, p_axis]
        if [e_axis, l_axis, p_axis] != [0, 1, 2]:
            print(f"    [AUTO-FIX] {var_name} {shape}. Mapping: E(ax{e_axis})={shape[e_axis]}, L(ax{l_axis})={shape[l_axis]}, P(ax{p_axis})={shape[p_axis]}")
            data_sorted = np.transpose(data_raw, (e_axis, l_axis, p_axis))
        else:
            data_sorted = data_raw

        # Теперь data_sorted гарантированно (Energy, L, Pitch)
        # E=6, L=16 (например), P=3 (например)
        
        # --- СРЕЗ ДАННЫХ ---
        try:
            # Проверяем границы
            n_L = data_sorted.shape[1]
            n_P = data_sorted.shape[2]
            
            # Фильтруем индексы, которые выходят за границы файла
            valid_L = [i for i in L_indices if i < n_L]
            valid_P = [i for i in P_indices if i < n_P]
            
            if len(valid_L) == 0:
                print(f"    [WARN] Нет валидных индексов L. Запрошено: {L_indices}, Доступно: 0..{n_L-1}")
                continue
            if len(valid_P) == 0:
                print(f"    [WARN] Нет валидных индексов P. Запрошено: {P_indices}, Доступно: 0..{n_P-1}")
                continue

            # Срезаем
            subset = data_sorted[:, valid_L, :][:, :, valid_P]
            
            # Усредняем
            subset[subset == 0] = np.nan
            daily_spectrum = np.nanmean(subset, axis=(1, 2))
            
            accumulated_spectra.append(daily_spectrum)
            
        except Exception as e:
            print(f"    [ERROR] Ошибка среза: {e}")
            continue

    # 4. ФИНАЛИЗАЦИЯ
    if not accumulated_spectra:
        print("[PROCESSING] Данных нет.")
        return []

    all_spectra = np.array(accumulated_spectra)
    final_flux = np.nanmean(all_spectra, axis=0)
    
    # Расчет ошибки
    if len(accumulated_spectra) > 1:
        final_err = np.nanstd(all_spectra, axis=0) / np.sqrt(len(accumulated_spectra))
    else:
        final_err = np.zeros_like(final_flux)

    valid_mask = ~np.isnan(final_flux) & (final_flux > 0)
    
    if not np.any(valid_mask):
         print("[PROCESSING] Все данные NaN/Zero.")
         return []

    print(f"[PROCESSING] График готов! Точек: {np.sum(valid_mask)}")

    return [{
        "ax_index": ax_index,
        "type": "spectra",
        "x_values": X_centers[valid_mask],
        "y_values": final_flux[valid_mask],
        "y_err": final_err[valid_mask],
        "x_label": x_label,
        "y_label": f"Flux",
        "x_scale": "log", "y_scale": "log",
        "title": f"Spectrum (E={config_n_E} bins)",
        "label": f"Days: {len(files)}"
    }]

def get_plot_data(app_state, ax_index=0):
    pk = app_state.plot_kind
    if pk in [1, 2]: return _generic_1d_plot(app_state, ax_index)
    elif pk == 12: return []
    return []
