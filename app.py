from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
import numpy as np

import os
from werkzeug.utils import secure_filename


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

current_df = None
original_df = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    global current_df, original_df
    
    if 'file' not in request.files:
        return jsonify({'error': 'No se seleccionó archivo'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No se seleccionó archivo'}), 400
    
    if file and file.filename.lower().endswith('.csv'):
        try:
            df = pd.read_csv(file)
            current_df = df.copy()
            original_df = df.copy()
            
            return jsonify({
                'success': True,
                'message': f'Archivo cargado exitosamente',
                'shape': df.shape,
                'columns': df.columns.tolist()
            })
        except Exception as e:
            return jsonify({'error': f'Error al procesar archivo: {str(e)}'}), 400
    
    return jsonify({'error': 'Formato de archivo no válido'}), 400

@app.route('/generate-demo-data', methods=['POST'])
def generate_demo_data():
    global current_df, original_df
    
    try:
        np.random.seed(42) 
        
        nombres = ['Juan Pérez', 'María García', 'Carlos López', 'Ana Martínez', 
                  'Pedro Rodríguez', 'Laura Hernández', 'Miguel Torres', 'Carmen Jiménez', 
                  'José Ruiz', 'Isabel Moreno']
        
        carreras = ['Ingeniería en Sistemas', 'Administración', 'Contaduría', 
                   'Psicología', 'Derecho', 'Medicina', 'Arquitectura']
        
        data = {
            'nombre': [f"{np.random.choice(nombres)} {i+1}" for i in range(100)],
            'matricula': [f"MAT{str(i+1).zfill(4)}" for i in range(100)],
            'carrera': np.random.choice(carreras, 100),
            'cal_asignatura1': np.round(np.random.uniform(60, 100, 100), 1),
            'cal_asignatura2': np.round(np.random.uniform(60, 100, 100), 1),
            'cal_asignatura3': np.round(np.random.uniform(60, 100, 100), 1)
        }
        
        df = pd.DataFrame(data)
        current_df = df.copy()
        original_df = df.copy()
        
        return jsonify({
            'success': True,
            'message': 'Datos de prueba generados exitosamente',
            'shape': df.shape,
            'columns': df.columns.tolist()
        })
        
    except Exception as e:
        return jsonify({'error': f'Error al generar datos: {str(e)}'}), 400

@app.route('/head', methods=['POST'])
def get_head():
    global current_df
    
    if current_df is None:
        return jsonify({'error': 'No hay datos cargados'}), 400
    
    try:
        n = request.json.get('n', 5)
        result = current_df.head(n)
        
        return jsonify({
            'success': True,
            'data': result.to_dict('records'),
            'columns': result.columns.tolist(),
            'code': f'df.head({n})'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/tail', methods=['POST'])
def get_tail():
    global current_df
    
    if current_df is None:
        return jsonify({'error': 'No hay datos cargados'}), 400
    
    try:
        n = request.json.get('n', 5)
        result = current_df.tail(n)
        
        return jsonify({
            'success': True,
            'data': result.to_dict('records'),
            'columns': result.columns.tolist(),
            'code': f'df.tail({n})'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/info', methods=['GET'])
def get_info():
    global current_df
    
    if current_df is None:
        return jsonify({'error': 'No hay datos cargados'}), 400
    
    try:
        info_data = {
            'shape': current_df.shape,
            'columns_info': []
        }
        
        for col in current_df.columns:
            dtype = str(current_df[col].dtype)
            non_null = current_df[col].count()
            info_data['columns_info'].append({
                'column': col,
                'non_null_count': int(non_null),
                'dtype': dtype
            })
        
        return jsonify({
            'success': True,
            'info': info_data,
            'code': 'df.info()'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/describe', methods=['GET'])
def get_describe():
    global current_df
    
    if current_df is None:
        return jsonify({'error': 'No hay datos cargados'}), 400
    
    try:
        numeric_df = current_df.select_dtypes(include=[np.number])
        
        if numeric_df.empty:
            return jsonify({
                'success': False,
                'message': 'No se encontraron columnas numéricas'
            })
        
        describe_result = numeric_df.describe()
        
        return jsonify({
            'success': True,
            'data': describe_result.to_dict(),
            'code': 'df.describe()'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/shape', methods=['GET'])
def get_shape():
    global current_df
    
    if current_df is None:
        return jsonify({'error': 'No hay datos cargados'}), 400
    
    return jsonify({
        'success': True,
        'shape': current_df.shape,
        'code': 'df.shape'
    })

@app.route('/columns', methods=['GET'])
def get_columns():
    global current_df
    
    if current_df is None:
        return jsonify({'error': 'No hay datos cargados'}), 400
    
    return jsonify({
        'success': True,
        'columns': current_df.columns.tolist(),
        'code': 'df.columns'
    })

@app.route('/select-column', methods=['POST'])
def select_column():
    global current_df
    
    if current_df is None:
        return jsonify({'error': 'No hay datos cargados'}), 400
    
    try:
        column = request.json.get('column')
        if column not in current_df.columns:
            return jsonify({'error': f'Columna {column} no existe'}), 400
        
        result = current_df[column].to_frame()
        
        return jsonify({
            'success': True,
            'data': result.head(20).to_dict('records'),
            'total_rows': len(result),
            'code': f"df['{column}']"
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/select-columns', methods=['POST'])
def select_columns():
    global current_df
    
    if current_df is None:
        return jsonify({'error': 'No hay datos cargados'}), 400
    
    try:
        columns = request.json.get('columns', [])
        if not columns:
            return jsonify({'error': 'No se especificaron columnas'}), 400
        
        missing_cols = [col for col in columns if col not in current_df.columns]
        if missing_cols:
            return jsonify({'error': f'Columnas no encontradas: {missing_cols}'}), 400
        
        result = current_df[columns]
        
        return jsonify({
            'success': True,
            'data': result.head(20).to_dict('records'),
            'columns': columns,
            'total_rows': len(result),
            'code': f"df[{columns}]"
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/filter', methods=['POST'])
def filter_data():
    global current_df
    
    if current_df is None:
        return jsonify({'error': 'No hay datos cargados'}), 400
    
    try:
        column = request.json.get('column')
        operator = request.json.get('operator')
        value = request.json.get('value')
        
        if column not in current_df.columns:
            return jsonify({'error': f'Columna {column} no existe'}), 400
        
        try:
            if isinstance(value, str) and value.replace('.', '').replace('-', '').isdigit():
                value = float(value)
        except:
            pass
        
        if operator == '>':
            filtered_df = current_df[current_df[column] > value]
        elif operator == '<':
            filtered_df = current_df[current_df[column] < value]
        elif operator == '==':
            filtered_df = current_df[current_df[column] == value]
        elif operator == '>=':
            filtered_df = current_df[current_df[column] >= value]
        elif operator == '<=':
            filtered_df = current_df[current_df[column] <= value]
        elif operator == '!=':
            filtered_df = current_df[current_df[column] != value]
        else:
            return jsonify({'error': 'Operador no válido'}), 400
        
        value_str = f"'{value}'" if isinstance(value, str) else str(value)
        code = f"df[df['{column}'] {operator} {value_str}]"
        
        return jsonify({
            'success': True,
            'data': filtered_df.head(50).to_dict('records'),
            'columns': filtered_df.columns.tolist(),
            'total_rows': len(filtered_df),
            'original_rows': len(current_df),
            'percentage': round((len(filtered_df) / len(current_df)) * 100, 2),
            'code': code
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/reset-data', methods=['POST'])
def reset_data():
    global current_df, original_df
    
    if original_df is None:
        return jsonify({'error': 'No hay datos originales para restaurar'}), 400
    
    current_df = original_df.copy()
    
    return jsonify({
        'success': True,
        'message': 'Datos restaurados al estado original'
    })

@app.route('/numpy-stats', methods=['POST'])
def numpy_stats():
    global current_df
    
    if current_df is None:
        return jsonify({'error': 'No hay datos cargados'}), 400
    
    try:
        column = request.json.get('column')
        if column not in current_df.columns:
            return jsonify({'error': f'Columna {column} no existe'}), 400
        
        if not pd.api.types.is_numeric_dtype(current_df[column]):
            return jsonify({'error': f'La columna {column} no es numérica'}), 400
        
        data = current_df[column].dropna().values
        
        stats = {
            'mean': float(np.mean(data)),
            'median': float(np.median(data)),
            'std': float(np.std(data)),
            'var': float(np.var(data)),
            'min': float(np.min(data)),
            'max': float(np.max(data)),
            'sum': float(np.sum(data)),
            'count': int(len(data))
        }
        
        return jsonify({
            'success': True,
            'stats': stats,
            'column': column,
            'code': f"np.mean(df['{column}']), np.std(df['{column}']), etc."
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)