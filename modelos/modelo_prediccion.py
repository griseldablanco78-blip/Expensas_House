import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score
import os

def prepare_data(df):
    """
    Prepara los datos para el modelo.
    Objetivo: Predecir si un producto necesitará reposición (Stock Crítico)
    """
    # Calculamos el stock actual por producto
    df['cambio_stock'] = df.apply(lambda row: row['cantidad'] if row['tipo_movimiento'] == 'Compra' else -row['cantidad'], axis=1)
    
    stock = df.groupby(['producto', 'categoria']).agg(
        stock_actual=('cambio_stock', 'sum'),
        frecuencia_consumo=('tipo_movimiento', lambda x: (x == 'Consumo').sum()),
        gasto_total=('precio', 'sum')
    ).reset_index()
    
    # Variable objetivo: 1 si stock_actual <= 2 (necesita reposición), 0 en caso contrario
    stock['necesita_reposicion'] = (stock['stock_actual'] <= 2).astype(int)
    
    # Variables predictoras (Features)
    # Convertimos la categoría a variables dummy
    X = pd.get_dummies(stock[['categoria', 'frecuencia_consumo', 'gasto_total']], drop_first=True)
    y = stock['necesita_reposicion']
    
    return X, y

def main():
    print("Entrenando Modelo Predictivo de Reposición (Random Forest)...")
    
    path = "data/inventario_movimientos_limpio.csv"
    if not os.path.exists(path):
        print("Dataset limpio no encontrado.")
        return
        
    df = pd.read_csv(path)
    X, y = prepare_data(df)
    
    if len(y) < 10:
        print("Pocos datos para entrenar el modelo.")
        return
        
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Inicializar y entrenar el modelo (Se justifica Random Forest por su robustez frente a outliers y datos no lineales)
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    # Predicciones
    y_pred = model.predict(X_test)
    
    print("\nResultados del Modelo:")
    print(f"Exactitud (Accuracy): {accuracy_score(y_test, y_pred):.2f}")
    print("\nReporte de Clasificación:")
    print(classification_report(y_test, y_pred))
    
    print("\nModelo entrenado con éxito. (Nota: en un entorno de producción, guardaríamos el modelo con pickle/joblib).")

if __name__ == '__main__':
    # Crear carpeta si no existe
    os.makedirs('modelos', exist_ok=True)
    main()
