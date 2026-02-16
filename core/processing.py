"""
Модуль Обработки (Processing Module) - DIMENSION AWARE
Исправляет "Большую Ошибку" перепутанных осей (L vs Pitch) путем 
сравнения размерностей файла с ожидаемыми размерами из BinningInfo.
"""
import os
import numpy as np
import warnings
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

# --- ГЛАВНАЯ ФУНКЦИЯ ПОСТРОЕНИЯ ---
def _generic_1d_plot(app_state, ax_index, mode='spectra'):
    print(f"\n[PROCESSING] -> Старт обработки (Exact Dimensions)")

    # 1. ЗАГРУЗКА ПАРАМЕТРОВ БИННИНГА
    try:
        idx_L = app_state.lb - 1
        idx_P = app_state.pitchb - 1
        idx_E = app_state.eb - 1
        
        # Получаем ожидаемое количество бинов для валидации осей
        n_L_bins = config.BIN_INFO['nL'][idx_L]
        n_P_bins = config.BIN_INFO['nPitch'][idx_P]
        
        # Границы для поиска индексов
        L_edges = config.BIN_INFO['Lbin'][idx_L]
        P_edges = config.BIN_INFO['pitchbin'][idx_P]
        
        if app_state.ror_e == 1: # Energy
            X_full = config.BIN_INFO['Ecenters'][idx_E]
            X_err_full = config.BIN_INFO['dE'][idx_E] / 2.0
            n_E_bins = len(X_full)
            x_label = "Kinetic Energy (GeV)"
        else: # Rigidity
            X_full = config.BIN_INFO['Rigcenters'][idx_E]
            X_err_full = config.BIN_INFO['dR'][idx_E] / 2.0
            n_E_bins = len(X_full)
            x_label = "Rigidity (GV)"
            
        print(f"[PROCESSING] Ожидаемые размерности: L={n_L_bins}, P={n_P_bins}, E={n_E_bins}")
    except Exception as e:
        print(f"[ERROR] Ошибка инициализации бинов: {e}")
        return []

    # 2. ИНДЕКСЫ ВЫБОРКИ
    target_l = app_state.l if (app_state.l and len(app_state.l) > 0) else [(L_edges[0] + L_edges[-1])/2]
    target_p = app_state.pitch if (app_state.pitch and len(app_state.pitch) > 0) else [45.0]

    L_indices = _find_bin_indices(L_edges, target_l)
    P_indices = _find_bin_indices(P_edges, target_p)
    
    print(f"[PROCESSING] Выбранные индексы: L={L_indices}, P={P_indices}")

    # 3. ПОИСК ФАЙЛОВ
    files = file_manager.get_input_filenames(app_state, 'flux')
    if not files: return []

    accumulated_spectra = []
    accumulated_errors = []
    
    for fpath in files:
        mat = _load_mat_file(fpath)
        if mat is None: continue
        
        keys = mat.keys()
        
        # --- ПОИСК ДАННЫХ ---
        data_raw = None
        for key in ['Flux', 'flux', 'Jday', 'J']:
            if key in keys: data_raw = mat[key]; break
        
        error_raw = None
        for key in ['dJ', 'dJday', 'Errors', 'dJfull']:
            if key in keys: error_raw = mat[key]; break
            
        if data_raw is None or data_raw.ndim != 3: continue
        if error_raw is None: error_raw = np.zeros_like(data_raw)

        # --- КЛЮЧЕВОЙ МОМЕНТ: ИДЕНТИФИКАЦИЯ ОСЕЙ ---
        shape = data_raw.shape # Например (3, 6, 16)
        
        # Ищем совпадения размеров. 
        # Если размеры совпадают, мы точно знаем, какая ось за что отвечает.
        
        # Кандидаты на оси
        ax_L = -1
        ax_P = -1
        ax_E = -1
        
        # 1. Поиск Энергии
        for i in range(3):
            if shape[i] == n_E_bins: ax_E = i; break
            
        # 2. Поиск L
        for i in range(3):
            if i != ax_E and shape[i] == n_L_bins: ax_L = i; break
            
        # 3. Поиск Pitch
        for i in range(3):
            if i != ax_E and i != ax_L and shape[i] == n_P_bins: ax_P = i; break
            
        # Fallback (если размеры совпадают, например L=16 и P=16, берем стандарт MATLAB)
        # Стандарт MATLAB (по коду DrawSpectra): (L, E, P) -> (0, 1, 2)
        if ax_L == -1 or ax_P == -1 or ax_E == -1:
            print(f"    [WARN] Неоднозначность осей {shape} vs (L={n_L_bins}, E={n_E_bins}, P={n_P_bins}). Использую стандарт (L, E, P).")
            ax_L, ax_E, ax_P = 0, 1, 2
        else:
            print(f"    [INFO] Оси определены: L=ax{ax_L}, E=ax{ax_E}, P=ax{ax_P}")

        # Транспонируем данные к виду (Energy, L, Pitch) для удобной нарезки
        # Нам нужно чтобы: 0->E, 1->L, 2->P
        # data_sorted = data_raw.transpose(ax_E, ax_L, ax_P)
        
        try:
            data_sorted = np.transpose(data_raw, (ax_E, ax_L, ax_P))
            error_sorted = np.transpose(error_raw, (ax_E, ax_L, ax_P))
        except:
            continue

        # --- СРЕЗ ---
        try:
            # Теперь data_sorted точно (Energy, L, Pitch)
            # Можем смело использовать индексы
            
            # Проверка границ
            if np.max(L_indices) >= data_sorted.shape[1]:
                print(f"    [WARN] Индекс L {L_indices} выходит за границы {data_sorted.shape[1]}")
                continue
            if np.max(P_indices) >= data_sorted.shape[2]:
                print(f"    [WARN] Индекс P {P_indices} выходит за границы {data_sorted.shape[2]}")
                continue

            # Срез
            subset_data = data_sorted[:, L_indices, :][:, :, P_indices]
            subset_err = error_sorted[:, L_indices, :][:, :, P_indices]
            
            subset_data[subset_data == 0] = np.nan
            
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", category=RuntimeWarning)
                # Усредняем по L и P (оси 1 и 2), оставляя спектр (ось 0)
                daily_spectrum = np.nanmean(subset_data, axis=(1, 2))
                
                # Ошибки
                n_points = np.sum(~np.isnan(subset_data), axis=(1, 2))
                sum_sq_err = np.nansum(subset_err**2, axis=(1, 2))
                daily_error = np.sqrt(sum_sq_err) / np.maximum(n_points, 1)

            if np.all(np.isnan(daily_spectrum)): continue
            
            accumulated_spectra.append(daily_spectrum)
            accumulated_errors.append(daily_error)
            
        except Exception as e:
            print(f"    [ERROR] {e}")
            continue

    # 4. ФИНАЛЬНАЯ СБОРКА
    if not accumulated_spectra:
        print("[PROCESSING] Нет данных.")
        return []

    all_spectra = np.array(accumulated_spectra)
    all_errors = np.array(accumulated_errors)
    
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        final_flux = np.nanmean(all_spectra, axis=0)
        
        # Если несколько файлов - берем std dev, если один - берем его ошибку
        if len(accumulated_spectra) > 1:
            final_y_err = np.nanstd(all_spectra, axis=0) / np.sqrt(len(accumulated_spectra))
        else:
            final_y_err = all_errors[0]

    min_len = min(len(X_full), len(final_flux), len(final_y_err), len(X_err_full))
    
    x_out = X_full[:min_len]
    y_out = final_flux[:min_len]
    yerr_out = final_y_err[:min_len]
    xerr_out = X_err_full[:min_len]

    valid_mask = ~np.isnan(y_out) & (y_out > 0)
    
    if not np.any(valid_mask):
        print("[PROCESSING] Все значения <= 0.")
        return []

    print(f"[PROCESSING] Успех! Точек: {np.sum(valid_mask)}")

    return [{
        "ax_index": ax_index,
        "plot_type": "errorbar",
        "x": x_out[valid_mask],
        "y": y_out[valid_mask],
        "y_err": yerr_out[valid_mask], 
        "x_err": xerr_out[valid_mask],
        "xlabel": x_label,
        "ylabel": "Flux",
        "xscale": "log",
        "yscale": "log",
        "label": f"Spectrum (N={len(files)})"
    }]

def get_plot_data(app_state, ax_index=0):
    pk = app_state.plot_kind
    if pk in [1, 2]: return _generic_1d_plot(app_state, ax_index)
    return []
