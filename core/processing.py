"""
Модуль Обработки (PROTOCOL COMPLIANT)
1. Единицы измерения: Flux * 1e7 (см. DrawSpectra.m).
2. Оси: Точное определение (L, P, E) на основе размеров из Config.
3. Ошибки: Чтение dJ из файла + dE из конфига.
"""
import os
import numpy as np
import warnings
from scipy.io import loadmat
from . import config
from . import state
from . import file_manager

def _load_mat_file(file_path):
    if not os.path.exists(file_path): return None
    try: return loadmat(file_path, squeeze_me=True, struct_as_record=False)
    except: return None

def _find_bin_indices(edges, values):
    """Находит индекс бина, содержащего значение (см. рис. 8 протокола)"""
    if values is None or len(values) == 0: return np.array([], dtype=int)
    if not isinstance(values, (list, np.ndarray)): values = [values]
    indices = np.searchsorted(edges, values, side='right') - 1
    indices[indices < 0] = 0
    indices[indices >= len(edges) - 1] = len(edges) - 2
    return np.unique(indices)

def _generic_1d_plot(app_state, ax_index, mode='spectra'):
    print(f"\n[PROCESSING] -> Старт обработки (Protocol Mode)")

    # 1. ПОДГОТОВКА ОСЕЙ
    try:
        idx_L = app_state.lb - 1
        idx_P = app_state.pitchb - 1
        idx_E = app_state.eb - 1
        
        # Ожидаемые размеры осей (для проверки файла)
        n_L_exp = config.BIN_INFO['nL'][idx_L]
        n_P_exp = config.BIN_INFO['nPitch'][idx_P]
        
        if app_state.ror_e == 1: # Energy
            X_centers = config.BIN_INFO['Ecenters'][idx_E]
            X_err_half = config.BIN_INFO['dE'][idx_E] / 2.0 
            x_label = "Kinetic Energy (GeV)"
        else: # Rigidity
            X_centers = config.BIN_INFO['Rigcenters'][idx_E]
            X_err_half = config.BIN_INFO['dR'][idx_E] / 2.0
            x_label = "Rigidity (GV)"
            
        n_E_exp = len(X_centers)
        print(f"[PROCESSING] Ожидается: L={n_L_exp}, P={n_P_exp}, E={n_E_exp}")
        
    except Exception as e:
        print(f"[ERROR] Ошибка конфига: {e}")
        return []

    # 2. ОПРЕДЕЛЕНИЕ ИНДЕКСОВ (Пользовательский выбор)
    L_indices = _find_bin_indices(config.BIN_INFO['Lbin'][idx_L], app_state.l)
    P_indices = _find_bin_indices(config.BIN_INFO['pitchbin'][idx_P], app_state.pitch)
    print(f"[PROCESSING] Индексы: L={L_indices}, P={P_indices}")

    # 3. ФАЙЛЫ
    files = file_manager.get_input_filenames(app_state, 'flux')
    if not files: return []

    accumulated_spectra = []
    accumulated_errors = []
    
    # МАСШТАБИРОВАНИЕ (см. DrawSpectra.m: if fluxunits, funits = 1e7)
    # По умолчанию считаем, что строим в GeV m^2 sr s (units=1)
    FUNITS = 1e7 

    for fpath in files:
        mat = _load_mat_file(fpath)
        if mat is None: continue
        
        # Чтение переменных
        keys = mat.keys()
        data_raw = None; error_raw = None
        
        # Flux (Jday / J)
        for k in ['Flux','flux','Jday','J']:
            if k in keys: data_raw = mat[k]; break
        # Error (dJday / dJ)
        for k in ['dJ','dJday','Errors']:
            if k in keys: error_raw = mat[k]; break
            
        if data_raw is None or data_raw.ndim != 3: continue
        if error_raw is None: error_raw = np.zeros_like(data_raw)

        # ОПРЕДЕЛЕНИЕ ОСЕЙ (DIMENSION MATCHING)
        shape = data_raw.shape
        ax_L, ax_P, ax_E = -1, -1, -1
        
        # Строгое сопоставление по размерам
        for i in range(3):
            if shape[i] == n_E_exp: ax_E = i; break
        for i in range(3):
            if i != ax_E and shape[i] == n_L_exp: ax_L = i; break
        for i in range(3):
            if i != ax_E and i != ax_L and shape[i] == n_P_exp: ax_P = i; break
            
        # Fallback на стандарт (L, E, P) -> (0, 1, 2)
        if ax_E == -1 or ax_L == -1 or ax_P == -1:
            # Если не смогли определить автоматически, пробуем стандарт MATLAB
            ax_L, ax_E, ax_P = 0, 1, 2
            # print(f"    [WARN] Оси не распознаны {shape}. Использую стандарт (L, E, P).")

        # Транспонируем в (Energy, L, Pitch)
        try:
            data_sorted = np.transpose(data_raw, (ax_E, ax_L, ax_P))
            error_sorted = np.transpose(error_raw, (ax_E, ax_L, ax_P))
        except: continue

        # СРЕЗ ДАННЫХ
        try:
            # Проверяем, есть ли данные в выбранном бине
            valid_L = [i for i in L_indices if i < data_sorted.shape[1]]
            valid_P = [i for i in P_indices if i < data_sorted.shape[2]]
            
            # Логика Fallback: Если выбранный бин ПУСТ или НЕ ВАЛИДЕН, берем среднее по дню
            # (Это частая ситуация для узких бинов L/Pitch)
            use_fallback = False
            if not valid_L or not valid_P:
                use_fallback = True
            else:
                subset = data_sorted[:, valid_L, :][:, :, valid_P]
                if np.all(subset == 0) or np.all(np.isnan(subset)):
                    use_fallback = True
                    print(f"    [INFO] Бин пуст. Беру среднее по дню.")

            if use_fallback:
                # Берем все L и P
                sub_d = data_sorted
                sub_e = error_sorted
            else:
                sub_d = data_sorted[:, valid_L, :][:, :, valid_P]
                sub_e = error_sorted[:, valid_L, :][:, :, valid_P]
            
            sub_d[sub_d == 0] = np.nan
            
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                
                # Среднее значение потока
                spec = np.nanmean(sub_d, axis=(1, 2))
                
                # Средняя ошибка (sqrt(sum(err^2))/N)
                count = np.sum(~np.isnan(sub_d), axis=(1, 2))
                count[count == 0] = 1
                err = np.sqrt(np.nansum(sub_e**2, axis=(1, 2))) / count

            if np.all(np.isnan(spec)): continue
            
            accumulated_spectra.append(spec)
            accumulated_errors.append(err)
            
        except Exception as e:
            print(f"[ERROR] Ошибка среза: {e}")
            continue

    # 4. СБОРКА РЕЗУЛЬТАТА
    if not accumulated_spectra: return []

    all_specs = np.array(accumulated_spectra)
    all_errs = np.array(accumulated_errors)
    
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        # Усредняем по дням (если их несколько)
        final_y = np.nanmean(all_specs, axis=0) * FUNITS
        
        if len(accumulated_spectra) > 1:
            # Ошибка среднего по нескольким дням
            final_y_err = (np.nanstd(all_specs, axis=0) / np.sqrt(len(files))) * FUNITS
        else:
            # Ошибка одного измерения
            final_y_err = all_errs[0] * FUNITS

    # Выравнивание длин
    Lmin = min(len(X_centers), len(final_y))
    x = X_centers[:Lmin]
    y = final_y[:Lmin]
    y_err = final_y_err[:Lmin]
    x_err = X_err_half[:Lmin]
    
    # Фильтр валидных точек (Flux > 0)
    mask = ~np.isnan(y) & (y > 0)
    
    return [{
        "ax_index": ax_index,
        "plot_type": "errorbar",
        "x": x[mask],
        "y": y[mask],
        "y_err": y_err[mask],
        "x_err": x_err[mask],
        "xlabel": x_label,
        "ylabel": "Flux (GeV m^2 sr s)^-1",
        "xscale": "log", "yscale": "log",
        "label": f"Spectrum (N={len(files)})"
    }]

def get_plot_data(app_state, ax_index=0):
    pk = app_state.plot_kind
    if pk in [1, 2]: return _generic_1d_plot(app_state, ax_index)
    return []
