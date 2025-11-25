from pathlib import Path


def create_structure() -> None:
    # Definimos las capas
    layers = ['bronze', 'silver', 'gold']
    
    # Subcarpetas para organizar mejor (opcional pero recomendado)
    subfolders = ['socrata_api', 'policia_scraping', 'dane_geo']

    for layer in layers:
        for sub in subfolders:
            path = Path('data') / layer / sub
            path.mkdir(parents=True, exist_ok=True)
            print(f"Creado: {path}")


if __name__ == "__main__":
    create_structure()