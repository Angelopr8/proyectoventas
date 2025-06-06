from config.conexion import conexion
from flask import Flask, render_template, request, redirect, session, flash
from datetime import datetime, date

app = Flask(__name__)
app.secret_key = 'miclave'

def mostrarTodo():
    cursor = conexion.cursor()
    cursor.execute('SELECT * FROM tbcliente')
    clientes = cursor.fetchall()
    cursor.close()
    return clientes

def obtener_productos():
    """Obtener todos los productos disponibles"""
    cursor = conexion.cursor()
    cursor.execute('SELECT * FROM tbproducto')
    productos = cursor.fetchall()
    cursor.close()
    return productos

def obtener_compras_cliente(cliente_id):
    """Obtener el historial de compras de un cliente"""
    cursor = conexion.cursor()
    sql = '''
    SELECT v.id, v.fecha_venta, p.nombre, v.cantidad, v.precio_unitario, v.total, v.observaciones
    FROM tbventa v
    JOIN tbproducto p ON v.producto_id = p.id
    WHERE v.cliente_id = %s
    ORDER BY v.fecha_venta DESC
    '''
    cursor.execute(sql, (cliente_id,))
    compras = cursor.fetchall()
    cursor.close()
    return compras

def calcular_total_compras(cliente_id):
    """Calcular el total de compras de un cliente"""
    cursor = conexion.cursor()
    sql = 'SELECT SUM(total) FROM tbventa WHERE cliente_id = %s'
    cursor.execute(sql, (cliente_id,))
    resultado = cursor.fetchone()
    cursor.close()
    return resultado[0] if resultado[0] else 0

@app.route('/')
def index():
    if 'usuario' in session:
        datos = mostrarTodo()
        return render_template('registrar.html', clientes=datos)
    return render_template("login.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    mensaje = ''
    if request.method == 'POST':
        user = request.form['txtuser']
        clave = request.form['txtclave']

        cursor = conexion.cursor()
        sql = 'SELECT id_usuario, user, clave, rol FROM tbusuario WHERE user=%s AND clave=%s'
        cursor.execute(sql, (user, clave))
        usuario = cursor.fetchone()
        cursor.close()

        if usuario:
            session['usuario'] = usuario[1]
            session['clave'] = usuario[2]
            return redirect('/')
        else:
            mensaje = "Usuario o contraseña incorrecto"
    return render_template('login.html', mensaje=mensaje)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/insertar', methods=['POST'])
def insertar():
    if 'usuario' not in session:
        return redirect('/login')
    
    nombre = request.form['txtnombre']
    nit = request.form['txtnit']
    cursor = conexion.cursor()
    sql = "INSERT INTO tbcliente (nombre, nit) VALUES (%s, %s)"
    cursor.execute(sql, (nombre, nit))
    conexion.commit()
    cursor.close()
    clientes = mostrarTodo()
    mensaje = "Registro insertado exitosamente"
    return render_template('registrar.html', mensaje=mensaje, clientes=clientes)

@app.route('/buscar', methods=['GET'])
def buscar():
    if 'usuario' not in session:
        return redirect('/login')
    
    buscar = request.args.get('txtbuscar')
    cursor = conexion.cursor()
    sql = "SELECT * FROM tbcliente WHERE nombre LIKE %s"
    cursor.execute(sql, (buscar + '%',))
    datos = cursor.fetchall()
    cursor.close()
    return render_template('registrar.html', mensaje="Resultados de búsqueda", clientes=datos)

@app.route('/actualizar/<int:id>')
def mostrar_actualizar(id):
    if 'usuario' not in session:
        return redirect('/login')
    
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM tbcliente WHERE id = %s", (id,))
    cliente = cursor.fetchone()
    cursor.close()
    clientes = mostrarTodo()
    return render_template('registrar.html', cliente=cliente, clientes=clientes, mensaje="Actualizar cliente")

@app.route('/actualizar', methods=['POST'])
def actualizar():
    if 'usuario' not in session:
        return redirect('/login')
    
    id_cliente = request.form['txtid']
    nombre = request.form['txtnombre']
    nit = request.form['txtnit']
    
    cursor = conexion.cursor()
    sql = "UPDATE tbcliente SET nombre = %s, nit = %s WHERE id = %s"
    cursor.execute(sql, (nombre, nit, id_cliente))
    conexion.commit()
    cursor.close()
    
    clientes = mostrarTodo()
    mensaje = "Registro actualizado exitosamente"
    return render_template('registrar.html', mensaje=mensaje, clientes=clientes)

@app.route('/eliminar/<int:id>')
def eliminar(id):
    if 'usuario' not in session:
        return redirect('/login')
    
    cursor = conexion.cursor()
    sql = "DELETE FROM tbcliente WHERE id = %s"
    cursor.execute(sql, (id,))
    conexion.commit()
    cursor.close()
    
    clientes = mostrarTodo()
    mensaje = "Registro eliminado exitosamente"
    return render_template('registrar.html', mensaje=mensaje, clientes=clientes)

# NUEVAS RUTAS PARA EL SISTEMA DE VENTAS

@app.route('/comprar/<int:cliente_id>')
def comprar(cliente_id):
    """Mostrar el formulario de compra para un cliente específico"""
    if 'usuario' not in session:
        return redirect('/login')
    
    # Obtener información del cliente
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM tbcliente WHERE id = %s", (cliente_id,))
    cliente = cursor.fetchone()
    cursor.close()
    
    if not cliente:
        flash('Cliente no encontrado', 'error')
        return redirect('/')
    
    # Obtener productos disponibles
    productos = obtener_productos()
    
    # Obtener historial de compras
    compras = obtener_compras_cliente(cliente_id)
    
    # Calcular total de compras
    total_compras = calcular_total_compras(cliente_id)
    
    # Fecha actual
    fecha_actual = date.today().strftime('%Y-%m-%d')
    
    return render_template('comprar.html', 
                         cliente=cliente,
                         productos=productos,
                         compras=compras,
                         total_compras=total_compras,
                         fecha_actual=fecha_actual)

@app.route('/procesar_venta', methods=['POST'])
def procesar_venta():
    """Procesar una nueva venta"""
    if 'usuario' not in session:
        return redirect('/login')
    
    try:
        cliente_id = request.form['cliente_id']
        producto_id = request.form['producto_id']
        cantidad = int(request.form['cantidad'])
        precio_unitario = float(request.form['precio_unitario'])
        total = float(request.form['total'])
        fecha_venta = request.form['fecha_venta']
        observaciones = request.form.get('observaciones', '')
        
        # Validaciones
        if not all([cliente_id, producto_id, cantidad, precio_unitario]):
            flash('Todos los campos son obligatorios', 'error')
            return redirect(f'/comprar/{cliente_id}')
        
        if cantidad <= 0 or precio_unitario <= 0 or total <= 0:
            flash('Los valores deben ser mayores a cero', 'error')
            return redirect(f'/comprar/{cliente_id}')
        
        # Insertar la venta
        cursor = conexion.cursor()
        sql = '''
        INSERT INTO tbventa (cliente_id, producto_id, cantidad, precio_unitario, total, fecha_venta, observaciones)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        '''
        cursor.execute(sql, (cliente_id, producto_id, cantidad, precio_unitario, total, fecha_venta, observaciones))
        conexion.commit()
        cursor.close()
        
        flash('Venta procesada exitosamente', 'success')
        return redirect(f'/comprar/{cliente_id}')
        
    except Exception as e:
        flash(f'Error al procesar la venta: {str(e)}', 'error')
        return redirect(f'/comprar/{cliente_id}')

@app.route('/vercompras/<int:cliente_id>')
def ver_compras(cliente_id):
    """Ver todas las compras de un cliente"""
    if 'usuario' not in session:
        return redirect('/login')
    
    # Obtener información del cliente
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM tbcliente WHERE id = %s", (cliente_id,))
    cliente = cursor.fetchone()
    cursor.close()
    
    if not cliente:
        flash('Cliente no encontrado', 'error')
        return redirect('/')
    
    # Obtener todas las compras del cliente
    compras = obtener_compras_cliente(cliente_id)
    
    # Calcular total de compras
    total_compras = calcular_total_compras(cliente_id)
    
    return render_template('vercompras.html',
                         cliente=cliente,
                         compras=compras,
                         total_compras=total_compras)

@app.route('/productos')
def productos():
    """Gestionar productos"""
    if 'usuario' not in session:
        return redirect('/login')
    
    productos = obtener_productos()
    return render_template('productos.html', productos=productos)

@app.route('/insertar_producto', methods=['POST'])
def insertar_producto():
    """Insertar un nuevo producto"""
    if 'usuario' not in session:
        return redirect('/login')
    
    try:
        nombre = request.form['nombre']
        precio = float(request.form['precio'])
        
        cursor = conexion.cursor()
        sql = "INSERT INTO tbproducto (nombre, precio) VALUES (%s, %s)"
        cursor.execute(sql, (nombre, precio))
        conexion.commit()
        cursor.close()
        
        flash('Producto agregado exitosamente', 'success')
    except Exception as e:
        flash(f'Error al agregar producto: {str(e)}', 'error')
    
    return redirect('/productos')

# Filtro personalizado para formatear números
@app.template_filter('currency')
def currency_filter(value):
    """Formatear números como moneda"""
    if value is None:
        return "0.00"
    return f"{float(value):,.2f}"

if __name__ == '__main__':
    app.run(debug=True)