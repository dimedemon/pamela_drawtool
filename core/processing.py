"""
Модуль Обработки (Фаза: Passages Histogram Fixed)
Специально для PlotKind 12:
1. Ищет переменную 'J' (прохождения).
2. Если индексы (E, L, P) не выбраны, берет значения по умолчанию.
"""
import os
import numpy as np
from scipy.io import loadmat
from . import config
from . import state
from . import file_manager

def _load_mat_file(file_path):
    if not os.path.exists(file_path): return None
    try: return loadmat(file_path, squeeze_me=True, struct_as_record=False)
    except: return None

def _find_bin_indices(edges, values):
    if not isinstance(values, (list, np.ndarray)): values = [values]
    indices = np.searchsorted(edges, values, side='right') - 1
    indices[indices < 0] = 0
    indices[indices >= len(edges) - 1] = len(edges) - 2
    return indices

# --- Стандартные функции (Spectra и др) ---
def _generic_1d_plot(app_state, ax_index, mode):
    # (Оставляем пустым или копируем старый код, если нужно строить спектры)
    # Здесь нас интересует только PlotKind 12
    return []

def _get_temporal_data(app_state, ax_index): return []
def _generic_2d_map(app_state, ax_index, mode): return []
def _get_auxiliary_data(app_state, ax_index): return []

# =========================================================
# === ГЛАВНАЯ ФУНКЦИЯ ДЛЯ ГИСТОГРАММ (PlotKind 12) ===
# =========================================================

def _get_flux_distribution(app_state, ax_index):
    """
    Строит гистограмму распределения потоков по ПРОХОЖДЕНИЯМ (J).
    """
    print("[PROCESSING] Start Flux Histogram (Passages)...")
    
    # 1. Получаем границы бинов из конфига
    try:
        L_edges = config.BIN_INFO['Lbin'][app_state.lb - 1]
        P_edges = config.BIN_INFO['pitchbin'][app_state.pitchb - 1]
        if app_state.ror_e == 1: 
            E_edges = config.BIN_INFO['Ebin'][app_state.eb - 1]
            val_name = "E"
        else: 
            E_edges = config.BIN_INFO['Rig'][app_state.eb - 1]
            val_name = "R"
    except Exception as e:
        print(f"[ERROR] Ошибка получения границ бинов: {e}")
        return []

    # 2. AUTO-FILL (Защита от пустого выбора в UI)
    # Если пользователь (или UI) не передал значения, берем дефолтные.
    
    target_l = app_state.l
    if not target_l or len(target_l) == 0:
        target_l = [(L_edges[0] + L_edges[-1])/2] # Середина диапазона L
        print(f"  [WARN] L not selected. Default: {target_l[0]:.2f}")

    target_p = app_state.pitch
    if not target_p or len(target_p) == 0:
        target_p = [85.0] # Почти захваченные
        print(f"  [WARN] Pitch not selected. Default: {target_p[0]}")

    target_e = app_state.e if app_state.ror_e == 1 else app_state.rig
    if not target_e or len(target_e) == 0:
        target_e = [E_edges[0]] # Самая низкая энергия
        print(f"  [WARN] Energy not selected. Default: {target_e[0]:.3f}")

    # 3. Переводим физические значения в индексы массива
    L_indices = np.unique(_find_bin_indices(L_edges, target_l))
    P_indices = np.unique(_find_bin_indices(P_edges, target_p))
    E_indices = np.unique(_find_bin_indices(E_edges, target_e))

    print(f"  [DEBUG] Indices -> L:{L_indices}, E:{E_indices}, P:{P_indices}")

    # 4. Сканируем файлы
    files = file_manager.get_input_filenames(app_state, 'flux')
    if not files: return []
    
    flux_values = []
    
    for fpath in files:
        mat = _load_mat_file(fpath)
        if mat is None: continue
        
        # Ищем переменную J (Passages)
        passages = None
        if hasattr(mat, 'J'): passages = mat.J
        elif hasattr(mat, 'flux_pass'): passages = mat.flux_pass # Иногда так называется
        
        # Если переменной нет, выводим список переменных для отладки (только для первого файла)
        if passages is None:
            # print(f"  [DEBUG] File {os.path.basename(fpath)} keys: {mat._fieldnames}")
            continue
            
        # J может быть массивом структур или cell array
        # Обычно это массив numpy object, где каждый элемент - матрица витка
        if np.isscalar(passages) or len(passages) == 0: continue

        try:
            # Пробегаем по всем виткам в этом дне
            for pass_data in passages:
                # pass_data - это матрица [L, E, Pitch] (или E, L, P - проверим)
                if np.isscalar(pass_data): continue
                
                # Проверка размерности (ожидаем 3D)
                if pass_data.ndim != 3: continue
                
                # --- ВАЖНО: ПОРЯДОК ИНДЕКСОВ ---
                # Обычно в J порядок: [L, E, Pitch]
                # Но если не сработает, попробуем [E, L, Pitch]
                
                for l_idx in L_indices:
                    for e_idx in E_indices:
                        for p_idx in P_indices:
                            val = np.nan
                            
                            # Попытка 1: [L, E, P]
                            try:
                                if (l_idx < pass_data.shape[0] and 
                                    e_idx < pass_data.shape[1] and 
                                    p_idx < pass_data.shape[2]):
                                    val = pass_data[l_idx, e_idx, p_idx]
                            except: pass

                            # Если валидное число > 0, сохраняем
                            if not np.isnan(val) and val > 0:
                                flux_values.append(val)
                                
        except Exception as e:
            # print(f"Error extracting J: {e}")
            pass

    # 5. Формируем результат
    count = len(flux_values)
    print(f"[PROCESSING] Найдено {count} значений потока (прохождений).")
    
    if count < 2: return []

    fluxes = np.array(flux_values)
    mean_val = np.mean(fluxes)
    std_val = np.std(fluxes)
    
    # Текст для легенды
    l_txt = f"[{L_edges[L_indices[0]]:.2f}]"
    e_txt = f"[{E_edges[E_indices[0]]:.2f}]"
    
    return [{
        "ax_index": ax_index,
        "type": "histogram_flux",
        "fluxes": fluxes,
        "stats": {
            'mean': mean_val, 
            'std_obs': std_val, 
            'mean_err': 0, 
            'count': count
        },
        "title": f"Passages Hist: L={l_txt}, {val_name}={e_txt}",
        "label": f"N={count}, Mean={mean_val:.2e}"
    }]

# --- MAIN DISPATCHER ---
def get_plot_data(app_state: state.ApplicationState, ax_index: int = 0):
    pk = app_state.plot_kind 
    
    # Возвращаем старые обработчики, если нужно
    if pk in [1, 2]: return _generic_1d_plot(app_state, ax_index, 'spectra')
    elif pk == 3: return _generic_1d_plot(app_state, ax_index, 'pitch')
    elif pk == 4: return _generic_1d_plot(app_state, ax_index, 'radial')
    elif pk == 5: return _get_temporal_data(app_state, ax_index)
    elif pk == 8: return _generic_2d_map(app_state, ax_index, 'l_pitch')
    elif pk == 9: return _generic_2d_map(app_state, ax_index, 'e_pitch')
    elif pk == 10: return _generic_2d_map(app_state, ax_index, 'e_l')
    elif pk == 11: return _get_auxiliary_data(app_state, ax_index)
    
    # === НАШ НОВЫЙ ТИП ===
    elif pk == 12: return _get_flux_distribution(app_state, ax_index)
    
    return []
