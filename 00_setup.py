import os

def create_structure():
    # Definimos las capas
    layers = ['bronze', 'silver', 'gold']
    
    # Subcarpetas para organizar mejor (opcional pero recomendado)
    subfolders = ['socrata_api', 'policia_scraping', 'dane_geo']

    for layer in layers:
        for sub in subfolders:
            path = os.path.join('data', layer, sub)
            os.makedirs(path, exist_ok=True)
            print(f"Creado: {path}")
            
    # Crear carpeta para logs o scripts
    os.makedirs('src', exist_ok=True)

if __name__ == "__main__":
    create_structure()