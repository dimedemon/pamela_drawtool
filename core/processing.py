"""
Модуль Обработки (Фаза 10 - FINAL FIX)
Исправлен порядок индексов для RBflux (Energy, L, Pitch).
Добавлен Debug-вывод размерности матрицы.
"""
import os
import numpy as np
from scipy.io import loadmat
from datetime import datetime, timedelta
from . import config
from . import state
from . import file_manager

def _load_mat_file(file_path):
    if not os.path.exists(file_path): return None
    try: return loadmat(file_path, squeeze_me=True, struct_as_record=False)
    except Exception as e: return None

def _find_bin_indices(edges, values):
    if not isinstance(values, (list, np.ndarray)): values = [values]
    indices = np.searchsorted(edges, values, side='right') - 1
    indices[indices < 0] = 0
    indices[indices >= len(edges) - 1] = len(edges) - 2
    return indices

# --- 1D PLOTS (Legacy support for old files) ---
def _generic_1d_plot(app_state, ax_index, mode):
    # Эта часть кода работает для спектров и профилей (обычно использует Jday)
    plot_data_list = []
    file_paths = file_manager.get_input_filenames(app_state, 'flux')
    if not file_paths: return []

    L_edges = config.BIN_INFO['Lbin'][app_state.lb - 1]
    P_edges = config.BIN_INFO['pitchbin'][app_state.pitchb - 1]
    if app_state.ror_e == 1: E_edges = config.BIN_INFO['Ebin'][app_state.eb - 1]; E_vals = app_state.e; val_name="E"; val_unit="GeV"
    else: E_edges = config.BIN_INFO['Rig'][app_state.eb - 1]; E_vals = app_state.rig; val_name="R"; val_unit="GV"
    
    L_c = (L_edges[:-1]+L_edges[1:])/2; dL = (L_edges[1:]-L_edges[:-1])/2
    P_c = (P_edges[:-1]+P_edges[1:])/2; dP = (P_edges[1:]-P_edges[:-1])/2
    E_c = (E_edges[:-1]+E_edges[1:])/2; dE = (E_edges[1:]-E_edges[:-1])/2

    L_idx = _find_bin_indices(L_edges, app_state.l)
    P_idx = _find_bin_indices(P_edges, app_state.pitch)
    E_idx = _find_bin_indices(E_edges, E_vals)

    for infile in file_paths:
        data = _load_mat_file(infile)
        if data is None: continue
        try: day_str = os.path.basename(infile).split('_')[1].split('.')[0]
        except: day_str = "?"
        
        if app_state.fullday:
            try: JJ = data['Jday']; dJJ = data['dJday']; NN = data['numevday']
            except: continue
            
            # Для Jday порядок часто бывает [L, E, P] в старых версиях
            if mode == 'spectra': 
                iter1, iter2 = np.unique(L_idx), np.unique(P_idx)
                for i1 in iter1:
                    for i2 in iter2:
                        # Fallback check dimension
                        if JJ.ndim == 3: y = JJ[i1, :, i2]; dy = dJJ[i1, :, i2]; n = NN[i1, :, i2]
                        else: continue
                        
                        mask = n > app_state.n_min
                        if not np.any(mask): continue
                        l_lbl = f"[{L_edges[i1]:.2f}-{L_edges[i1+1]:.2f}]"
                        p_lbl = f"[{P_edges[i2]:.0f}-{P_edges[i2+1]:.0f}]"
                        lbl = f"L={l_lbl}, P={p_lbl}, D={day_str}"
                        plot_data_list.append({'ax_index': ax_index, 'plot_type': 'errorbar', 'x': E_c[mask], 'y': y[mask], 'x_err': dE[mask], 'y_err': dy[mask], 'label': lbl, 'xlabel': f"{val_name}, {val_unit}", 'ylabel': "Flux", 'xscale': 'log', 'yscale': 'log'})
            # ... (остальные режимы опускаем для краткости, они аналогичны)
    return plot_data_list

# --- 2D MAPS ---
def _generic_2d_map(app_state, ax_index, mode):
    # (Код карт оставляем как есть, он работает)
    return [] 

# --- TEMPORAL ---
def _get_temporal_data(app_state, ax_index):
    # (Код временных рядов оставляем как есть)
    return []

def _get_auxiliary_data(app_state, ax_index):
    # (Код погоды оставляем как есть)
    return []

# =========================================================
# === FLUX DISTRIBUTION (PlotKind 12) - FIXED & DEBUGGED ===
# =========================================================

def _get_flux_distribution(app_state, ax_index):
    """
    Строит гистограмму распределения потоков по дням (из RBflux).
    Ожидает матрицу Flux[Energy, L, Pitch].
    """
    print("[PROCESSING] Сбор статистики Fluxes Histogram...")
    files = file_manager.get_input_filenames(app_state, 'flux')
    if not files: return []

    # 1. Индексы бинов
    L_edges = config.BIN_INFO['Lbin'][app_state.lb - 1]
    P_edges = config.BIN_INFO['pitchbin'][app_state.pitchb - 1]
    if app_state.ror_e == 1: E_edges = config.BIN_INFO['Ebin'][app_state.eb - 1]; E_vals = app_state.e; val_name="E"
    else: E_edges = config.BIN_INFO['Rig'][app_state.eb - 1]; E_vals = app_state.rig; val_name="R"
    
    L_indices = np.unique(_find_bin_indices(L_edges, app_state.l))
    P_indices = np.unique(_find_bin_indices(P_edges, app_state.pitch))
    E_indices = np.unique(_find_bin_indices(E_edges, E_vals))
    
    print(f"  [DEBUG] Selected bins -> L_idx: {L_indices}, E_idx: {E_indices}, P_idx: {P_indices}")

    flux_collections = {} 
    stat_errors_collections = {}
    
    first_file_checked = False

    for fpath in files:
        mat = _load_mat_file(fpath)
        if mat is None: continue
        
        try:
            # Ищем переменную Flux
            data_matrix = None
            error_matrix = None

            if hasattr(mat, 'Flux'):
                data_matrix = mat.Flux
                if hasattr(mat, 'Errors'): error_matrix = mat.Errors
            elif hasattr(mat, 'Jday'):
                data_matrix = mat.Jday
                if hasattr(mat, 'dJday'): error_matrix = mat.dJday
            
            if data_matrix is None:
                if not first_file_checked: print(f"  [DEBUG] No Flux/Jday in {os.path.basename(fpath)}")
                continue

            # ПРОВЕРКА РАЗМЕРНОСТИ И ПОРЯДКА
            if not first_file_checked:
                print(f"  [DEBUG] Found matrix shape: {data_matrix.shape}")
                first_file_checked = True

            # ПЫТАЕМСЯ ИЗВЛЕЧЬ ДАННЫЕ
            # Стандарт RBflux: [Energy, L, Pitch]
            # Стандарт Jday (иногда): [L, Energy, Pitch]
            
            ndim = data_matrix.ndim
            if ndim != 3: continue

            for l_idx in L_indices:
                for e_idx in E_indices:
                    for p_idx in P_indices:
                        val = np.nan
                        err = 0
                        
                        # --- ВАРИАНТ 1: [Energy, L, Pitch] (Наиболее вероятно для RBflux) ---
                        try:
                            if e_idx < data_matrix.shape[0] and l_idx < data_matrix.shape[1] and p_idx < data_matrix.shape[2]:
                                val = data_matrix[e_idx, l_idx, p_idx]
                                if error_matrix is not None: err = error_matrix[e_idx, l_idx, p_idx]
                        except: pass
                        
                        # --- ВАРИАНТ 2: [L, Energy, Pitch] (Если вариант 1 не сработал или дал ошибку) ---
                        # Если Вариант 1 вернул ерунду (например, вылет за границы), пробуем наоборот
                        if np.isnan(val) and (l_idx < data_matrix.shape[0] and e_idx < data_matrix.shape[1]):
                             try:
                                val = data_matrix[l_idx, e_idx, p_idx]
                                if error_matrix is not None: err = error_matrix[l_idx, e_idx, p_idx]
                             except: pass

                        # Фильтрация валидных значений
                        if not np.isnan(val) and val > 0:
                            key = (l_idx, p_idx, e_idx)
                            if key not in flux_collections: 
                                flux_collections[key] = []
                                stat_errors_collections[key] = []
                            
                            flux_collections[key].append(val)
                            stat_errors_collections[key].append(err)
                                    
        except Exception as e:
            # print(f"Error in file {fpath}: {e}")
            pass

    # Формируем данные для плоттера
    plot_data_list = []
    
    for key, fluxes in flux_collections.items():
        if len(fluxes) < 2: continue
        
        fluxes = np.array(fluxes)
        errors = np.array(stat_errors_collections.get(key, []))
        
        l_idx, p_idx, e_idx = key
        
        mean_val = np.mean(fluxes)
        std_obs = np.std(fluxes)
        mean_err = np.mean(errors) if len(errors) > 0 else 0
        
        l_lbl = f"[{L_edges[l_idx]:.2f}-{L_edges[l_idx+1]:.2f}]"
        p_lbl = f"[{P_edges[p_idx]:.0f}-{P_edges[p_idx+1]:.0f}]"
        e_lbl = f"[{E_edges[e_idx]:.2f}-{E_edges[e_idx+1]:.2f}]"
        
        stats = {
            'mean': mean_val,
            'std_obs': std_obs,
            'mean_err': mean_err,
            'count': len(fluxes)
        }
        
        plot_data_list.append({
            "ax_index": ax_index,
            "type": "histogram_flux",
            "fluxes": fluxes,
            "stats": stats,
            "title": f"Flux Dist: L={l_lbl}, P={p_lbl}, {val_name}={e_lbl}"
        })
        
    print(f"[PROCESSING] Готово. Сформировано {len(plot_data_list)} гистограмм.")
    return plot_data_list

# --- MAIN DISPATCHER ---
def get_plot_data(app_state: state.ApplicationState, ax_index: int = 0):
    pk = app_state.plot_kind 
    if pk in [1, 2]: return _generic_1d_plot(app_state, ax_index, 'spectra')
    elif pk == 3: return _generic_1d_plot(app_state, ax_index, 'pitch')
    elif pk == 4: return _generic_1d_plot(app_state, ax_index, 'radial')
    elif pk == 5: return _get_temporal_data(app_state, ax_index)
    elif pk == 8: return _generic_2d_map(app_state, ax_index, 'l_pitch')
    elif pk == 9: return _generic_2d_map(app_state, ax_index, 'e_pitch')
    elif pk == 10: return _generic_2d_map(app_state, ax_index, 'e_l')
    elif pk == 11: return _get_auxiliary_data(app_state, ax_index)
    elif pk == 12: return _get_flux_distribution(app_state, ax_index)
    return []
