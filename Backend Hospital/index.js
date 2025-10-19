// --- 1. Importar librerías ---
const express = require('express');
const mysql = require('mysql2/promise'); // Usamos la versión con Promesas
const bcrypt = require('bcryptjs');
const cors = require('cors');

// --- 2. Configuración ---
const app = express();
app.use(express.json()); // Permite a Express entender JSON
app.use(cors()); // Permite peticiones desde otros "orígenes" (tu app de Vue)

const port = 3000; // El backend correrá en este puerto

// Configuración de la conexión a la BD
// ESTOS DATOS SON SECRETOS y solo viven en el backend
const dbConfig = {
  host: 'localhost', // O la IP de tu BD
  user: 'root',      // Tu usuario de Workbench/MySQL
  password: 'tu_password_de_mysql', // Tu contraseña de Workbench/MySQL
  database: 'mi_proyecto_db'
};

// --- 3. Crear el "Endpoint" de Login ---
// (Un endpoint es una URL de tu API)
app.post('/login', async (req, res) => {
  try {
    // 3.1. Obtener datos que envió Vue
    const { email, password } = req.body;

    if (!email || !password) {
      return res.status(400).json({ message: 'Email y contraseña son requeridos' });
    }

    // 3.2. Conectarse a la BD
    const connection = await mysql.createConnection(dbConfig);
    
    // 3.3. Buscar al usuario por email
    const [rows] = await connection.execute(
      'SELECT * FROM users WHERE email = ?',
      [email]
    );

    await connection.end();

    // 3.4. Validar si el usuario existe
    if (rows.length === 0) {
      return res.status(401).json({ message: 'Credenciales inválidas' }); // 401 = No autorizado
    }

    const user = rows[0];

    // 3.5. Comparar la contraseña (¡NUNCA al revés!)
    // Compara la contraseña enviada (password) con el hash guardado (user.password_hash)
    const isPasswordValid = await bcrypt.compare(password, user.password_hash);

    if (!isPasswordValid) {
      return res.status(401).json({ message: 'Credenciales inválidas' });
    }
    
    // 3.6. ¡Login Exitoso!
    // En un proyecto real, aquí generarías un Token (JWT)
    res.status(200).json({ 
      message: '¡Login Exitoso!',
      user: { id: user.id, email: user.email } 
    });

  } catch (error) {
    console.error('Error en el login:', error);
    res.status(500).json({ message: 'Error interno del servidor' });
  }
});

// --- 4. Iniciar el servidor ---
app.listen(port, () => {
  console.log(`Servidor Backend corriendo en http://localhost:${port}`);
});