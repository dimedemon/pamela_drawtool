import os
import numpy as np
import scipy.io
from core import config

def find_any_flux_file():
    """Ищет любой файл RBflux...mat в папке данных."""
    base = config.BASE_DATA_PATH
    print(f"Search root: {base}")
    for root, dirs, files in os.walk(base):
        for file in files:
            if file.startswith("RBflux") and file.endswith(".mat"):
                return os.path.join(root, file)
    return None

def print_structure():
    print("-" * 60)
    print("   PAMELA EXPERIMENT: LEVEL 3 DATA STRUCTURE (SAMPLE)")
    print("-" * 60)

    # 1. Находим файл
    fpath = find_any_flux_file()
    if not fpath:
        print("❌ Файлы данных не найдены! Проверьте путь в config.py")
        return

    print(f"SOURCE FILE: .../{os.path.basename(fpath)}")
    
    # 2. Загружаем
    try:
        mat = scipy.io.loadmat(fpath, squeeze_me=True, struct_as_record=False)
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    # 3. Анализ биннинга (извлекаем размеры)
    # Обычно в файле есть Flux, Errors, Count и т.д.
    # Структура обычно: [Energy x L-shell x PitchAngle] или [Energy x Pitch x L]
    
    if hasattr(mat, 'Flux'):
        flux = mat.Flux
        print(f"DATA TYPE:   Reconstructed Proton Flux")
        print(f"DIMENSIONS:  {flux.shape}  (Energy × L-shell × PitchAngle)")
        print(f"MEMORY SIZE: {flux.nbytes / 1024:.1f} KB per array")
        
        # 4. Демонстрация осей (Фазовое пространство)
        print("\n=== PHASE SPACE GRID (DISCRETIZATION) ===")
        
        # Энергия (попытаемся найти Ebin в BinningInfo или прикинем)
        n_E, n_L, n_A = flux.shape
        print(f"[X] ENERGY Axis:     {n_E} bins (Log scale: ~80 MeV ... 50 GeV)")
        print(f"[Y] L-SHELL Axis:    {n_L} bins (Linear: L = 1.0 ... 8.0)")
        print(f"[Z] PITCH-ANGLE Axis:{n_A} bins (Angular: 0° ... 90°)")

        print("\n=== DATA CONTENT SAMPLE (Physical Values) ===")
        print("Differential Flux [particles / (cm² · s · sr · GeV)]")
        
        # Ищем непустой кусок для примера
        # Берем средние индексы
        idx_e = n_E // 2
        idx_l = n_L // 2
        
        slice_vals = flux[idx_e, idx_l, :] # Срез по питч-углу
        
        print(f"\nSlice at Energy Bin #{idx_e} and L-shell Bin #{idx_l}:")
        print(f"{'Pitch (deg)':<15} | {'Flux Value':<20} | {'Stat. Error'}")
        print("-" * 55)
        
        # Выводим последние 5 питч-углов (обычно там захваченные частицы)
        pitch_step = 90.0 / n_A
        err_arr = mat.Errors if hasattr(mat, 'Errors') else np.zeros_like(flux)
        
        for i in range(max(0, n_A - 6), n_A):
            angle = (i + 0.5) * pitch_step
            val = slice_vals[i]
            err = err_arr[idx_e, idx_l, i]
            
            val_str = f"{val:.4e}" if val > 0 else "0.0000 (Empty)"
            err_str = f"{err:.4e}" if val > 0 else "-"
            print(f"{angle:5.1f}° - {angle+pitch_step:5.1f}° | {val_str:<20} | ± {err_str}")

        print("\n[INFO] This structure allows detailed anisotropy analysis.")
        print("-" * 60)

    else:
        print("Structure unknown. Keys found:", mat._fieldnames)

if __name__ == "__main__":
    print_structure()
