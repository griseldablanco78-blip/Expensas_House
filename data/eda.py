import pandas as pd
import numpy as np
import os

def main():
    print("Iniciando limpieza de datos...")
    
    input_path = 'data/inventario_movimientos_sucio.csv'
    if not os.path.exists(input_path):
        print(f"Error: No se encuentra el archivo {input_path}")
        return
        
    df = pd.read_csv(input_path)
    print(f"Dataset original: {df.shape[0]} filas, {df.shape[1]} columnas")
    
    # 1. Eliminar duplicados
    df = df.drop_duplicates()
    print(f"Después de eliminar duplicados: {df.shape[0]} filas")
    
    # 2. Tratamiento de nulos
    # Para categorías nulas, podemos imputar basado en el producto (si es posible) o asignar 'Desconocido'
    df['categoria'] = df['categoria'].fillna('Desconocido')
    
    # Para precios nulos, imputamos con la mediana del precio de ese producto
    df['precio'] = df.groupby('producto')['precio'].transform(lambda x: x.fillna(x.median()))
    # Si aún quedan nulos (ej. un producto que solo tenía un registro y era nulo), rellenamos con la mediana global
    df['precio'] = df['precio'].fillna(df['precio'].median())
    
    # Para fechas nulas, las eliminamos ya que una serie de tiempo sin fecha no sirve
    df = df.dropna(subset=['fecha'])
    print(f"Después de eliminar fechas nulas: {df.shape[0]} filas")
    
    # 3. Corrección de errores tipográficos y estandarización
    df['tipo_movimiento'] = df['tipo_movimiento'].str.strip().str.capitalize()
    
    # 4. Tratamiento de Outliers
    # Cantidades negativas (deberían ser positivas o tratadas según el tipo de movimiento, asumiremos que fue error de tipeo)
    df['cantidad'] = df['cantidad'].abs()
    
    # Outliers en precio (precios multiplicados por 100 por error)
    # Usaremos el rango intercuartílico (IQR) por producto para detectar precios extremadamente altos
    def cap_outliers(series):
        Q1 = series.quantile(0.25)
        Q3 = series.quantile(0.75)
        IQR = Q3 - Q1
        upper_bound = Q3 + 1.5 * IQR
        lower_bound = Q1 - 1.5 * IQR
        # Si el IQR es 0 (todos los precios son iguales), no hacemos nada
        if IQR == 0:
            return series
        # Limitamos los valores
        return np.where(series > upper_bound, series.median(), series)

    df['precio'] = df.groupby('producto')['precio'].transform(cap_outliers)
    
    # 5. Estandarizar tipos de datos
    df['fecha'] = pd.to_datetime(df['fecha'])
    df['cantidad'] = df['cantidad'].astype(int)
    
    print("Limpieza finalizada.")
    print(df.info())
    
    # Guardar dataset limpio
    output_path = 'data/inventario_movimientos_limpio.csv'
    df.to_csv(output_path, index=False)
    print(f"Dataset limpio guardado en: {output_path}")

if __name__ == '__main__':
    main()
