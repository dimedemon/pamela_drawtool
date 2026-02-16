"""
Модуль Обработки (Processing Module) - DEBUG VERSION
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
    try: return loadmat(file_path, squeeze_me=True, struct_as_record=False)
    except: return None

def _find_bin_indices(edges, values):
    if values is None or len(values) == 0: return np.array([], dtype=int)
    if not isinstance(values, (list, np.ndarray)): values = [values]
    indices = np.searchsorted(edges, values, side='right') - 1
    indices[indices < 0] = 0
    indices[indices >= len(edges) - 1] = len(edges) - 2
    return np.unique(indices)

# --- ЛОГИКА ПОСТРОЕНИЯ СПЕКТРОВ (PlotKind 1, 2) ---
def _generic_1d_plot(app_state, ax_index, mode='spectra'):
    print(f"\n[DEBUG PROCESSING] -> Зашли в функцию _generic_1d_plot")
    print(f"[DEBUG PROCESSING]    L={app_state.l}, Pitch={app_state.pitch}")
    print(f"[DEBUG PROCESSING]    Binning indices: lb={app_state.lb}, pitchb={app_state.pitchb}, eb={app_state.eb}")

    # 1. Инициализация бинов
    try:
        # Важно: индексы в state 1-based (как в Matlab), в питоне 0-based
        L_edges = config.BIN_INFO['Lbin'][app_state.lb - 1]
        P_edges = config.BIN_INFO['pitchbin'][app_state.pitchb - 1]
        
        if app_state.ror_e == 1: # Energy
            X_edges = config.BIN_INFO['Ebin'][app_state.eb - 1]
            x_label = "Kinetic Energy (GeV)"
        else: # Rigidity
            X_edges = config.BIN_INFO['Rig'][app_state.eb - 1]
            x_label = "Rigidity (GV)"
            
        X_centers = np.sqrt(X_edges[:-1] * X_edges[1:])
        print(f"[DEBUG PROCESSING]    Бины инициализированы успешно. X_len={len(X_centers)}")
    except Exception as e:
        print(f"[ERROR PROCESSING] Ошибка инициализации бинов: {e}")
        import traceback
        traceback.print_exc()
        return []

    # 2. Индексы
    target_l = app_state.l if (app_state.l and len(app_state.l) > 0) else [(L_edges[0] + L_edges[-1])/2]
    target_p = app_state.pitch if (app_state.pitch and len(app_state.pitch) > 0) else [45.0]

    L_indices = _find_bin_indices(L_edges, target_l)
    P_indices = _find_bin_indices(P_edges, target_p)
    print(f"[DEBUG PROCESSING]    Сконвертированные индексы -> L_idx: {L_indices}, P_idx: {P_indices}")

    # 3. Вызов файл-менеджера (Здесь должны пойти логи поиска файлов)
    print(f"[DEBUG PROCESSING]    Вызываю file_manager.get_input_filenames...")
    files = file_manager.get_input_filenames(app_state, 'flux')
    
    if not files:
        print("[DEBUG PROCESSING]    file_manager вернул пустой список файлов.")
        return []

    # 4. Чтение данных
    accumulated_spectra = []
    print(f"[DEBUG PROCESSING]    Начинаю чтение {len(files)} файлов...")

    for fpath in files:
        mat = _load_mat_file(fpath)
        if mat is None: 
            print(f"    [WARN] Не удалось прочитать {os.path.basename(fpath)}")
            continue

        data_3d = None
        if hasattr(mat, 'Flux'): data_3d = mat.Flux
        elif hasattr(mat, 'flux'): data_3d = mat.flux
        
        if data_3d is None:
            print(f"    [WARN] В файле {os.path.basename(fpath)} нет переменной Flux")
            continue
        
        # Обработка размерностей
        if data_3d.ndim != 3:
             # Бывает 2D, если питч-угол 1 бин или L 1 бин. Нужно обрабатывать аккуратно.
             print(f"    [WARN] Странная размерность данных: {data_3d.shape} в {os.path.basename(fpath)}")
             continue

        try:
            subset = data_3d[:, L_indices, :][:, :, P_indices]
            # Заменяем 0 на NaN
            subset[subset == 0] = np.nan
            # Усредняем
            daily_spectrum = np.nanmean(subset, axis=(1, 2))
            accumulated_spectra.append(daily_spectrum)
        except Exception as e:
            print(f"    [ERROR] Ошибка при срезе данных: {e}")
            continue

    if not accumulated_spectra:
        print("[DEBUG PROCESSING]    Данные не накоплены (accumulated_spectra пуст).")
        return []

    all_spectra = np.array(accumulated_spectra)
    final_flux = np.nanmean(all_spectra, axis=0)
    
    if len(accumulated_spectra) > 1:
        final_err = np.nanstd(all_spectra, axis=0) / np.sqrt(len(accumulated_spectra))
    else:
        final_err = np.zeros_like(final_flux)

    valid_mask = ~np.isnan(final_flux) & (final_flux > 0)
    
    if not np.any(valid_mask):
        print("[DEBUG PROCESSING]    Все данные NaN или 0 после усреднения.")
        return []

    print(f"[DEBUG PROCESSING] -> УСПЕХ! Возвращаем данные для графика.")
    
    return [{
        "ax_index": ax_index,
        "type": "spectra",
        "x_values": X_centers[valid_mask],
        "y_values": final_flux[valid_mask],
        "y_err": final_err[valid_mask],
        "x_label": x_label,
        "y_label": "Flux",
        "x_scale": "log", "y_scale": "log",
        "title": f"Spectrum (Days: {len(files)})",
        "label": "PAMELA Data"
    }]

# --- ГЛАВНЫЙ ДИСПЕТЧЕР (ENTRY POINT) ---
def get_plot_data(app_state: state.ApplicationState, ax_index: int = 0):
    pk = app_state.plot_kind
    
    # === ВОТ ЭТОТ ЛОГ НАМ НУЖЕН БОЛЬШЕ ВСЕГО ===
    print(f"\n[DEBUG PROCESSING] !!! ВХОД В get_plot_data !!!")
    print(f"[DEBUG PROCESSING] PlotKind = {pk} (Тип: {type(pk)})")
    # ===========================================

    # 1. СПЕКТРЫ (Energy=1, Rigidity=2 в меню MATLAB часто соответствуют 1 и 2)
    # ВАЖНО: Проверьте, какой индекс у "Energy Spectra" в вашем interface
    # Обычно в коде: 1 - Energy Spectra, 2 - Rigidity Spectra
    if pk == 1 or pk == 2: 
        return _generic_1d_plot(app_state, ax_index, 'spectra')
    
    # 12. ГИСТОГРАММА (Для теста)
    elif pk == 12: 
        print("[DEBUG PROCESSING] Выбран режим гистограммы (12)")
        return [] 
    
    else:
        print(f"[DEBUG PROCESSING] PlotKind {pk} не обработан (вернул []).")
        return []
