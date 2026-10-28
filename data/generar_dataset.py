import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import os

# Configuración
NUM_ROWS = 2000
CATEGORIAS = ['Lacteos', 'Limpieza', 'Carnes', 'Bebidas', 'Verduras', 'Snacks', 'Panaderia']
MARCAS = ['Marca_A', 'Marca_B', 'Generico', 'Premium_X', 'Eco_Friendly', 'Local_Y']
PRODUCTOS = {
    'Lacteos': ['Leche', 'Queso', 'Yogur', 'Manteca'],
    'Limpieza': ['Detergente', 'Lavandina', 'Esponja', 'Desodorante_Piso'],
    'Carnes': ['Pollo', 'Carne_Picada', 'Chorizo', 'Bife'],
    'Bebidas': ['Agua', 'Gaseosa', 'Cerveza', 'Jugo'],
    'Verduras': ['Papa', 'Cebolla', 'Tomate', 'Lechuga'],
    'Snacks': ['Papas_Fritas', 'Mani', 'Nachos', 'Galletitas'],
    'Panaderia': ['Pan_Flauta', 'Medialunas', 'Facturas', 'Pan_Molde']
}
TIPOS_MOVIMIENTO = ['Compra', 'Consumo', 'Desperdicio']

def generate_date(start_date, end_date):
    time_between_dates = end_date - start_date
    days_between_dates = time_between_dates.days
    random_number_of_days = random.randrange(days_between_dates)
    return start_date + timedelta(days=random_number_of_days)

def main():
    print("Generando dataset sintético 'sucio'...")
    
    data = []
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2023, 12, 31)
    
    for _ in range(NUM_ROWS):
        categoria = random.choice(CATEGORIAS)
        producto = random.choice(PRODUCTOS[categoria])
        marca = random.choice(MARCAS)
        tipo = random.choice(TIPOS_MOVIMIENTO)
        
        # Precios base simulados
        precio_base = random.uniform(500, 5000)
        cantidad = random.randint(1, 10)
        fecha = generate_date(start_date, end_date).strftime('%Y-%m-%d')
        
        # Introducir "ruido" o errores (10% de probabilidad)
        # Nulos
        if random.random() < 0.05:
            categoria = np.nan
        if random.random() < 0.05:
            precio_base = np.nan
        if random.random() < 0.02:
            fecha = None
            
        # Outliers en precio o cantidad
        if random.random() < 0.03:
            precio_base = precio_base * 100 # Outlier gigantesco
        if random.random() < 0.03:
            cantidad = -5 # Cantidad negativa
            
        # Errores tipográficos (en lugar de 'Compra', 'compra ')
        if random.random() < 0.05 and tipo == 'Compra':
            tipo = 'compra '
            
        data.append([fecha, producto, categoria, marca, tipo, cantidad, precio_base])
        
    df = pd.DataFrame(data, columns=['fecha', 'producto', 'categoria', 'marca', 'tipo_movimiento', 'cantidad', 'precio'])
    
    # Duplicar algunas filas
    if NUM_ROWS > 50:
        duplicados = df.sample(n=50)
        df = pd.concat([df, duplicados], ignore_index=True)
        
    # Mezclar el dataframe para que los duplicados no estén al final
    df = df.sample(frac=1).reset_index(drop=True)
    
    # Guardar a CSV
    os.makedirs('data', exist_ok=True)
    output_path = 'data/inventario_movimientos_sucio.csv'
    df.to_csv(output_path, index=False)
    
    print(f"Dataset generado exitosamente con {len(df)} filas.")
    print(f"Ruta: {output_path}")

if __name__ == '__main__':
    main()
