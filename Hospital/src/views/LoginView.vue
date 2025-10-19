<template>
  <div class="login-container">
    <form class="login-form" @submit.prevent="handleLogin">
      <h2>Iniciar Sesión</h2>

      <div class="form-group">
        <label for="email">Correo Electrónico:</label>
        <input 
          type="email" 
          id="email" 
          v-model="email" 
          required 
        />
      </div>

      <div class="form-group">
        <label for="password">Contraseña:</label>
        <input 
          type="password" 
          id="password" 
          v-model="password" 
          required 
        />
      </div>

      <button type="submit">Ingresar</button>
    </form>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';

// 'ref' se usa para crear variables reactivas que guardarán los datos del formulario
const email = ref('');
const password = ref('');
const router = useRouter(); // Para redirigir al usuario después

const handleLogin = () => {
  // --- Validar datos ---
  // Por ahora, solo simulamos un login exitoso.
  console.log('Datos enviados:', email.value, password.value);

  if (email.value === "admin@test.com" && password.value === "123456") {
    alert('¡Login Exitoso! (Simulación)');
    // En un futuro, aquí recibirías un token de tu API.
    
    // Redirigir al usuario a una página principal (ej. un 'dashboard')
    // router.push('/dashboard'); 
  } else {
    alert('Credenciales incorrectas (Simulación)');
  }
};
</script>

<style scoped>
/* Estilos básicos para centrar y dar forma al formulario */
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 80vh; /* Ocupa casi toda la altura de la vista */
}

.login-form {
  padding: 2rem;
  border: 1px solid #ccc;
  border-radius: 8px;
  background-color: black;
  width: 300px;
}

.form-group {
  margin-bottom: 1rem;
}

label {
  display: block;
  margin-bottom: 0.5rem;
}

input {
  width: 100%;
  padding: 0.5rem;
  box-sizing: border-box; /* Asegura que el padding no afecte el ancho total */
  border: 1px solid #ddd;
  border-radius: 4px;
}

button {
  width: 100%;
  padding: 0.75rem;
  background-color: #42b883; /* Color verde de Vue */
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
}

button:hover {
  background-color: #33a06f;
}
</style>