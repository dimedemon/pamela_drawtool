"""
Модуль Обработки (Processing Module)
Прямой порт логики DrawSpectra.m.
Реализует загрузку Jday/dJday и правильную индексацию (L, E, P).
"""
import os
import numpy as np
import warnings
from scipy.io import loadmat
from . import config
from . import state
from . import file_manager

def _load_mat_file(file_path):
    """Загружает .mat файл как словарь."""
    if not os.path.exists(file_path): return None
    try:
        # squeeze_me убирает лишние размерности (1, 6) -> (6,)
        return loadmat(file_path, squeeze_me=True, struct_as_record=False)
    except: return None

def _find_bin_indices(edges, values):
    """Аналог поиска индекса в MATLAB: [~,Lnum] = min(abs(L-Ledges))."""
    if values is None or (isinstance(values, (list, np.ndarray)) and len(values) == 0):
        return np.array([0]) # Дефолтный бин
    if not isinstance(values, (list, np.ndarray)):
        values = [values]
    
    # Логика поиска как в DrawSpectra.m: найти ближайшую границу слева
    indices = np.searchsorted(edges, values, side='right') - 1
    indices[indices < 0] = 0
    indices[indices >= len(edges) - 1] = len(edges) - 2
    return np.unique(indices)

def _get_spectra_data(app_state, ax_index):
    """Реализация логики построения спектров из DrawSpectra.m."""
    print(f"\n[PROCESSING] -> Запуск обработки спектра...")

    # 1. Получаем параметры биннинга из конфига
    try:
        idx_L, idx_P, idx_E = app_state.lb - 1, app_state.pitchb - 1, app_state.eb - 1
        
        # Границы для поиска индексов
        L_edges = config.BIN_INFO['Lbin'][idx_L]
        P_edges = config.BIN_INFO['pitchbin'][idx_P]
        
        # Центры и ширины для графика (рассчитаны в config.py)
        if app_state.ror_e == 1: # Energy
            x_centers = config.BIN_INFO['Ecenters'][idx_E]
            x_err_half = config.BIN_INFO['dE'][idx_E] / 2.0
            x_label = "Kinetic Energy (GeV)"
        else: # Rigidity
            x_centers = config.BIN_INFO['Rigcenters'][idx_E]
            x_err_half = config.BIN_INFO['dR'][idx_E] / 2.0
            x_label = "Rigidity (GV)"
            
        print(f"[PROCESSING] Биннинг: L_bins={len(L_edges)-1}, E_bins={len(x_centers)}, P_bins={len(P_edges)-1}")
    except Exception as e:
        print(f"[ERROR] Ошибка параметров биннинга: {e}")
        return []

    # 2. Определяем индексы L и Pitch на основе выбора пользователя
    l_indices = _find_bin_indices(L_edges, app_state.l)
    p_indices = _find_bin_indices(P_edges, app_state.pitch)
    print(f"[PROCESSING] Индексы из интерфейса: L={l_indices}, Pitch={p_indices}")

    # 3. Ищем файлы данных
    files = file_manager.get_input_filenames(app_state, 'flux')
    if not files:
        print("[PROCESSING] Файлы не найдены Менеджером Файлов.")
        return []

    accumulated_y = []
    accumulated_y_err = []
    
    # Коэффициент перевода единиц из DrawSpectra.m (funits = 1e7)
    FUNITS = 1e7

    for fpath in files:
        mat = _load_mat_file(fpath)
        if mat is None: continue
        
        # Доступ к переменным как к ключам словаря (ВАЖНО!)
        # MATLAB: Jday(L, Energy, Pitch)
        j_data = mat.get('Jday') or mat.get('J')
        dj_data = mat.get('dJday') or mat.get('dJ')
        
        if j_data is None:
            print(f"    [WARN] В файле {os.path.basename(fpath)} не найдены переменные Jday или J.")
            continue

        try:
            # Вырезаем срез данных: (L_idx, все энергии, Pitch_idx)
            # В файле (3, 6, 16): 0-L, 1-E, 2-P
            # np.mean используется, если выбрано несколько L или Pitch
            subset_j = j_data[l_indices, :, :]
            subset_j = subset_j[:, :, p_indices]
            
            subset_dj = dj_data[l_indices, :, :] if dj_data is not None else np.zeros_like(subset_j)
            subset_dj = subset_dj[:, :, p_indices]

            # Усредняем по L и Pitch (оси 0 и 2 в срезе)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                y_day = np.nanmean(subset_j, axis=(0, 2))
                # Ошибки усредняем квадратично: sqrt(sum(err^2))/N
                y_err_day = np.sqrt(np.nansum(subset_dj**2, axis=(0, 2))) / np.sum(~np.isnan(subset_j), axis=(0, 2))

            accumulated_y.append(y_day)
            accumulated_y_err.append(y_err_day)
            print(f"    [+] Данные извлечены из {os.path.basename(fpath)}")
            
        except Exception as e:
            print(f"    [ERROR] Ошибка индексации в файле {os.path.basename(fpath)}: {e}")
            continue

    if not accumulated_y:
        print("[PROCESSING] Данные не были накоплены.")
        return []

    # 4. Финальное усреднение (если дней несколько)
    final_y = np.nanmean(accumulated_y, axis=0) * FUNITS
    if len(accumulated_y) > 1:
        # Для нескольких дней берем стандартное отклонение как ошибку
        final_y_err = (np.nanstd(accumulated_y, axis=0) / np.sqrt(len(accumulated_y))) * FUNITS
    else:
        final_y_err = accumulated_y_err[0] * FUNITS

    # 5. Маскируем пустые значения для логарифмической шкалы
    mask = ~np.isnan(final_y) & (final_y > 0)
    
    if not np.any(mask):
        print("[PROCESSING] Все значения в спектре <= 0 или NaN.")
        return []

    print(f"[PROCESSING] Успех! Подготовлено {np.sum(mask)} точек для графика.")

    # Формируем структуру для matplotlib_widget.py
    return [{
        "ax_index": ax_index,
        "plot_type": "errorbar",
        "x": x_centers[mask],
        "y": final_y[mask],
        "y_err": final_y_err[mask],
        "x_err": x_err_half[mask],
        "xlabel": x_label,
        "ylabel": "Flux (GeV m^2 sr s)^-1",
        "xscale": "log",
        "yscale": "log",
        "label": f"PAMELA Spectrum (N={len(accumulated_y)})"
    }]

def get_plot_data(app_state, ax_index=0):
    """Точка входа из главного окна."""
    # plot_kind 0 = Energy Spectra, 1 = Rigidity Spectra
    pk = app_state.plot_kind
    if pk == 0 or pk == 1:
        return _get_spectra_data(app_state, ax_index)
    return []
