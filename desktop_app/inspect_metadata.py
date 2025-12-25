import os
import scipy.io
import numpy as np

# Путь, который мы видели в логах
PATH = "/Volumes/T7 Touch/dirflux_newStructure/file_metadata.mat"

def inspect_element(key, val, indent=0):
    space = "    " * indent
    t = type(val)
    
    if isinstance(val, (np.ndarray, list)):
        # Если это массив, пишем размер
        shape = getattr(val, 'shape', len(val))
        print(f"{space}- {key} : Array {shape}")
        
        # Если внутри массива лежат объекты (структуры), заглянем в первый
        if hasattr(val, 'flat') and val.size > 0:
            first_elem = val.flat[0]
            if isinstance(first_elem, scipy.io.matlab.mio5_params.mat_struct):
                print(f"{space}  [Inside '{key}' array found structs. Inspecting first element:]")
                inspect_object(first_elem, indent + 1)
                
    elif isinstance(val, scipy.io.matlab.mio5_params.mat_struct):
        print(f"{space}- {key} : Struct/Object")
        inspect_object(val, indent + 1)
    else:
        print(f"{space}- {key} : {t} (Value: {str(val)[:50]}...)")

def inspect_object(obj, indent=0):
    # Перебираем атрибуты объекта
    if hasattr(obj, '_fieldnames'):
        for name in obj._fieldnames:
            val = getattr(obj, name)
            inspect_element(name, val, indent)
    elif hasattr(obj, '__dict__'):
        for name, val in obj.__dict__.items():
            if name.startswith('_'): continue
            inspect_element(name, val, indent)

print(f"=== INSPECTING: {PATH} ===")

if not os.path.exists(PATH):
    print("❌ Файл не найден!")
else:
    try:
        mat = scipy.io.loadmat(PATH, squeeze_me=True, struct_as_record=False)
        print("✅ Файл загружен. Структура:")
        # mat - это словарь на верхнем уровне
        for key, val in mat.items():
            if key.startswith('__'): continue
            inspect_element(key, val)
            
    except Exception as e:
        print(f"❌ Ошибка чтения: {e}")
