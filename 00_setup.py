from pathlib import Path


def create_structure():
    # Definimos las capas
    layers = ['bronze', 'silver', 'gold']
    
    # Subcarpetas para organizar mejor (opcional pero recomendado)
    subfolders = ['socrata_api', 'policia_scraping', 'dane_geo']

    for layer in layers:
        for sub in subfolders:
            path = Path('data') / layer / sub
            path.mkdir(parents=True, exist_ok=True)
            print(f"Creado: {path}")
            
    # Crear carpeta para logs o scripts
    Path('src').mkdir(exist_ok=True)

if __name__ == "__main__":
    create_structure()