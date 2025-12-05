"""
Модуль Обработки (Фаза 3 - MEGA UPDATE)
Поддерживает 1D спектры, Радиальное распределение и 2D Карты.
"""
import os
import numpy as np
from scipy.io import loadmat
from . import config
from . import state
from . import file_manager
from datetime import datetime, timedelta

def _load_mat_file(file_path):
    if not os.path.exists(file_path):
        print(f"ВНИМАНИЕ: Файл не найден: {file_path}")
        return None
    try: return loadmat(file_path, squeeze_me=True, struct_as_record=False)
    except Exception as e: print(f"Ошибка чтения .mat: {e}"); return None

def _find_bin_indices(edges, values):
    if not isinstance(values, (list, np.ndarray)): values = [values]
    indices = np.searchsorted(edges, values, side='right') - 1
    indices[indices < 0] = 0
    indices[indices >= len(edges) - 1] = len(edges) - 2
    return indices

# --- 1D PLOTS ---

def _get_spectra_data(app_state, ax_index):
    # (Код спектров остается тем же, я его свернул для краткости)
    # ... (Используйте код из предыдущего рабочего варианта) ...
    # Для надежности я вставлю его полную версию ниже в финальном блоке
    return _generic_1d_plot(app_state, ax_index, mode='spectra')

def _get_radial_data(app_state, ax_index):
    return _generic_1d_plot(app_state, ax_index, mode='radial')

def _get_pitch_data(app_state, ax_index):
    return _generic_1d_plot(app_state, ax_index, mode='pitch')

# --- 2D MAPS ---

def _get_l_pitch_map(app_state, ax_index):
    """L vs Pitch Map (PlotKind 8)."""
    return _generic_2d_map(app_state, ax_index, mode='l_pitch')

def _get_e_pitch_map(app_state, ax_index):
    """E vs Pitch Map (PlotKind 9)."""
    return _generic_2d_map(app_state, ax_index, mode='e_pitch')

def _get_e_l_map(app_state, ax_index):
    """E vs L Map (PlotKind 10)."""
    return _generic_2d_map(app_state, ax_index, mode='e_l')

# --- GENERIC FUNCTIONS (DRY Principle) ---

def _generic_1d_plot(app_state, ax_index, mode):
    plot_data_list = []
    file_paths = file_manager.get_input_filenames(app_state, 'flux')
    if not file_paths: return []

    L_edges = config.BIN_INFO['Lbin'][app_state.lb - 1]
    P_edges = config.BIN_INFO['pitchbin'][app_state.pitchb - 1]
    
    if app_state.ror_e == 1: # E
        E_edges = config.BIN_INFO['Ebin'][app_state.eb - 1]
        E_vals = app_state.e
    else: # R
        E_edges = config.BIN_INFO['Rig'][app_state.eb - 1]
        E_vals = app_state.rig
    
    # Centers & Deltas
    L_c = (L_edges[:-1]+L_edges[1:])/2; dL = (L_edges[1:]-L_edges[:-1])/2
    P_c = (P_edges[:-1]+P_edges[1:])/2; dP = (P_edges[1:]-P_edges[:-1])/2
    E_c = (E_edges[:-1]+E_edges[1:])/2; dE = (E_edges[1:]-E_edges[:-1])/2

    # Indices
    L_idx = _find_bin_indices(L_edges, app_state.l)
    P_idx = _find_bin_indices(P_edges, app_state.pitch)
    E_idx = _find_bin_indices(E_edges, E_vals)

    for infile in file_paths:
        data = _load_mat_file(infile)
        if data is None: continue
        try: day_str = os.path.basename(infile).split('_')[1].split('.')[0]
        except: day_str = "?"
        
        if app_state.fullday:
            try:
                JJ = data['Jday']; dJJ = data['dJday']; NN = data['numevday']
            except: continue
            
            # Loop structure depends on mode
            if mode == 'spectra': # X=E, Fix=L,P
                iter1, iter2 = np.unique(L_idx), np.unique(P_idx)
                for i1 in iter1:
                    for i2 in iter2:
                        y = JJ[i1, :, i2]; dy = dJJ[i1, :, i2]; n = NN[i1, :, i2]
                        mask = n > app_state.n_min
                        if not np.any(mask): continue
                        lbl = f"L=[{L_edges[i1]:.2f}], P=[{P_edges[i2]:.0f}], D={day_str}"
                        plot_data_list.append({'ax_index': ax_index, 'plot_type': 'errorbar',
                            'x': E_c[mask], 'y': y[mask], 'x_err': dE[mask], 'y_err': dy[mask],
                            'label': lbl, 'xlabel': 'E' if app_state.ror_e==1 else 'R',
                            'ylabel': 'J', 'xscale': 'log', 'yscale': 'log'})
                            
            elif mode == 'radial': # X=L, Fix=E,P
                iter1, iter2 = np.unique(E_idx), np.unique(P_idx)
                for i1 in iter1:
                    for i2 in iter2:
                        y = JJ[:, i1, i2]; dy = dJJ[:, i1, i2]; n = NN[:, i1, i2]
                        mask = n > app_state.n_min
                        if not np.any(mask): continue
                        lbl = f"E=[{E_edges[i1]:.2f}], P=[{P_edges[i2]:.0f}], D={day_str}"
                        plot_data_list.append({'ax_index': ax_index, 'plot_type': 'errorbar',
                            'x': L_c[mask], 'y': y[mask], 'x_err': dL[mask], 'y_err': dy[mask],
                            'label': lbl, 'xlabel': 'L', 'ylabel': 'J',
                            'xscale': 'linear', 'yscale': 'log'})

            elif mode == 'pitch': # X=P, Fix=L,E
                iter1, iter2 = np.unique(L_idx), np.unique(E_idx)
                for i1 in iter1:
                    for i2 in iter2:
                        y = JJ[i1, i2, :]; dy = dJJ[i1, i2, :]; n = NN[i1, i2, :]
                        mask = n > app_state.n_min
                        if not np.any(mask): continue
                        lbl = f"L=[{L_edges[i1]:.2f}], E=[{E_edges[i2]:.2f}], D={day_str}"
                        plot_data_list.append({'ax_index': ax_index, 'plot_type': 'errorbar',
                            'x': P_c[mask], 'y': y[mask], 'x_err': dP[mask], 'y_err': dy[mask],
                            'label': lbl, 'xlabel': 'Pitch', 'ylabel': 'J',
                            'xscale': 'linear', 'yscale': 'log'})

    return plot_data_list

def _generic_2d_map(app_state, ax_index, mode):
    plot_data_list = []
    file_paths = file_manager.get_input_filenames(app_state, 'flux')
    if not file_paths: return []

    L_edges = config.BIN_INFO['Lbin'][app_state.lb - 1]
    P_edges = config.BIN_INFO['pitchbin'][app_state.pitchb - 1]
    if app_state.ror_e == 1: E_edges = config.BIN_INFO['Ebin'][app_state.eb - 1]
    else: E_edges = config.BIN_INFO['Rig'][app_state.eb - 1]
    
    # Indices needed for FIXED parameter
    L_idx = _find_bin_indices(L_edges, app_state.l)
    P_idx = _find_bin_indices(P_edges, app_state.pitch)
    E_idx = _find_bin_indices(E_edges, app_state.e if app_state.ror_e==1 else app_state.rig)

    for infile in file_paths:
        data = _load_mat_file(infile)
        if data is None: continue
        try: day_str = os.path.basename(infile).split('_')[1].split('.')[0]
        except: day_str = "?"
        
        if app_state.fullday:
            try: JJ = data['Jday']
            except: continue
            
            if mode == 'l_pitch': # X=L, Y=Pitch, Fix=E
                # Z = JJ[:, e_idx, :] -> (L, Pitch)
                # Внимание: Pcolormesh ожидает Z[y, x]. У нас J(L, E, P).
                # Если X=L, Y=P, то Z должен быть (P, L). Значит надо транспонировать.
                for i_fixed in np.unique(E_idx):
                    Z = JJ[:, i_fixed, :].T # Transpose to (Pitch, L)
                    lbl = f"L-Pitch Map (E={E_edges[i_fixed]:.2f}), D={day_str}"
                    plot_data_list.append({
                        'ax_index': ax_index, 'plot_type': 'pcolor',
                        'x': L_edges, 'y': P_edges, 'z': Z,
                        'label': lbl, 'xlabel': 'L', 'ylabel': 'Pitch', 'zlabel': 'Flux',
                        'xscale': 'linear', 'yscale': 'linear', 'zscale': 'log'
                    })

            elif mode == 'e_pitch': # X=E, Y=Pitch, Fix=L
                for i_fixed in np.unique(L_idx):
                    Z = JJ[i_fixed, :, :].T # (Pitch, E)
                    lbl = f"E-Pitch Map (L={L_edges[i_fixed]:.2f}), D={day_str}"
                    plot_data_list.append({
                        'ax_index': ax_index, 'plot_type': 'pcolor',
                        'x': E_edges, 'y': P_edges, 'z': Z,
                        'label': lbl, 'xlabel': 'E', 'ylabel': 'Pitch', 'zlabel': 'Flux',
                        'xscale': 'log', 'yscale': 'linear', 'zscale': 'log'
                    })
            
            elif mode == 'e_l': # X=E, Y=L, Fix=Pitch
                for i_fixed in np.unique(P_idx):
                    Z = JJ[:, :, i_fixed] # (L, E) - already Y, X order? No.
                    # X=E, Y=L. Z shape is (L, E). So Z[y, x] is correct.
                    lbl = f"E-L Map (P={P_edges[i_fixed]:.0f}), D={day_str}"
                    plot_data_list.append({
                        'ax_index': ax_index, 'plot_type': 'pcolor',
                        'x': E_edges, 'y': L_edges, 'z': Z,
                        'label': lbl, 'xlabel': 'E', 'ylabel': 'L', 'zlabel': 'Flux',
                        'xscale': 'log', 'yscale': 'linear', 'zscale': 'log'
                    })
    
    return plot_data_list

def _get_temporal_data(app_state: state.ApplicationState, ax_index: int):
    """
    Порт DrawTemporal.m
    Строит зависимость потока от Времени (Дней).
    Поддерживает множественные линии (если выбрано несколько L, P или E).
    """
    # 1. Подготовка индексов
    L_edges = config.BIN_INFO['Lbin'][app_state.lb - 1]
    pitch_edges = config.BIN_INFO['pitchbin'][app_state.pitchb - 1]
    
    if app_state.ror_e == 1: # E
        E_edges = config.BIN_INFO['Ebin'][app_state.eb - 1]
        E_values = app_state.e
        val_unit = "GeV"
        val_name = "E"
    else: # R
        E_edges = config.BIN_INFO['Rig'][app_state.eb - 1]
        E_values = app_state.rig
        val_unit = "GV"
        val_name = "R"
        
    # Находим индексы для всех выбранных параметров
    L_indices = np.unique(_find_bin_indices(L_edges, app_state.l))
    P_indices = np.unique(_find_bin_indices(pitch_edges, app_state.pitch))
    E_indices = np.unique(_find_bin_indices(E_edges, E_values))
    
    # Словарь для сбора данных: key=(l_idx, p_idx, e_idx) -> value={'x':[], 'y':[], ...}
    traces = {}
    for l in L_indices:
        for p in P_indices:
            for e in E_indices:
                traces[(l,p,e)] = {'x': [], 'y': [], 'y_err': [], 'n': []}

    # 2. Получаем список файлов
    file_paths = file_manager.get_input_filenames(app_state, 'flux')
    if not file_paths: return []
    
    base_date = datetime(2005, 12, 31)

    # 3. Цикл по файлам (Дням)
    for infile in file_paths:
        data = _load_mat_file(infile)
        if data is None: continue
        
        # Определяем дату/день
        try:
            day_num = int(os.path.basename(infile).split('_')[1].split('.')[0])
            # Для оси X используем дату (datetime)
            current_date = base_date + timedelta(days=day_num)
        except:
            continue

        if app_state.fullday:
            try:
                JJ = data['Jday']   # Shape: (L, E, P) или (L, R, P)
                dJJ = data['dJday']
                NN = data['numevday']
            except KeyError: continue
            
            # Извлекаем данные для всех нужных комбинаций
            for l_idx in L_indices:
                for e_idx in E_indices:
                    for p_idx in P_indices:
                        # Проверка размеров массива (на случай смены биннинга)
                        if l_idx >= JJ.shape[0] or e_idx >= JJ.shape[1] or p_idx >= JJ.shape[2]:
                            continue

                        flux = JJ[l_idx, e_idx, p_idx]
                        err = dJJ[l_idx, e_idx, p_idx]
                        nev = NN[l_idx, e_idx, p_idx]
                        
                        # Фильтр Nmin применяется ПОТОМ или ЗДЕСЬ? 
                        # Обычно для временного ряда мы сохраняем точку, даже если она 0,
                        # или пропускаем. Сделаем пропуск, если N < min.
                        if nev > app_state.n_min:
                            key = (l_idx, p_idx, e_idx)
                            traces[key]['x'].append(current_date)
                            traces[key]['y'].append(flux)
                            traces[key]['y_err'].append(err)
    
    # 4. Формируем список данных для отрисовки
    plot_data_list = []
    
    for key, trace_data in traces.items():
        if not trace_data['x']: continue # Пустой трек
        
        l_idx, p_idx, e_idx = key
        
        # Центры бинов для лейбла
        l_c = (L_edges[l_idx] + L_edges[l_idx+1])/2
        p_c = (pitch_edges[p_idx] + pitch_edges[p_idx+1])/2
        e_c = (E_edges[e_idx] + E_edges[e_idx+1])/2
        
        label = (f"L={l_c:.2f}, P={p_c:.0f}, {val_name}={e_c:.3f} {val_unit}")
        
        # Сортируем по дате (на всякий случай)
        # (zip -> sort -> unzip)
        combined = sorted(zip(trace_data['x'], trace_data['y'], trace_data['y_err']))
        x_sorted, y_sorted, err_sorted = zip(*combined)
        
        plot_data_list.append({
            "ax_index": ax_index,
            "plot_type": "errorbar",
            "x": x_sorted,
            "y": y_sorted,
            "y_err": err_sorted, # x_err для времени обычно не рисуют
            "label": label,
            "xlabel": "Date",
            "ylabel": "J",
            "xscale": "linear", # Время линейно
            "yscale": "log",
            # "marker": 'o' # Можно добавить маркеры
        })

    return plot_data_list

# --- ОБНОВЛЕННЫЙ ДИСПЕТЧЕР ---
def get_plot_data(app_state: state.ApplicationState, ax_index: int = 0):
    gen = app_state.gen 
    pk = app_state.plot_kind 

    if gen == 1: 
        if pk in [1, 2]: return _get_spectra_data(app_state, ax_index)
        elif pk == 3: return _get_pitch_data(app_state, ax_index)
        elif pk == 4: return _get_radial_data(app_state, ax_index)
        
        # --- НОВОЕ ---
        elif pk == 5: return _get_temporal_data(app_state, ax_index) # Temporal variations
        # -------------
        
        elif pk == 8: return _get_l_pitch_map(app_state, ax_index)
        elif pk == 9: return _get_e_pitch_map(app_state, ax_index)
        elif pk == 10: return _get_e_l_map(app_state, ax_index)
            
    return []
