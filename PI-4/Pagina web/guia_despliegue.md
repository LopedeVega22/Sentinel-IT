# Guía de Despliegue - SentinelIT

Esta guía explica los pasos necesarios para instalar y poner en marcha el panel web de SentinelIT y preparar la base de datos.

## 1. Requisitos Previos
* **Servidor Web:** Apache o Nginx
* **PHP:** Versión 7.4 o superior (con extensión PDO_MySQL habilitada)
* **Base de Datos:** MySQL o MariaDB

## 2. Configuración de la Base de Datos
1. Inicia sesión en tu gestor de base de datos (por ejemplo, phpMyAdmin o mediante la consola de MySQL/MariaDB).
2. Crea una nueva base de datos llamada `SentinelIT` (o el nombre que prefieras).
3. Importa el archivo `schema.sql` proporcionado en el código fuente.
   - *Por consola:* `mysql -u root -p SentinelIT < schema.sql`
4. Este script creará las tablas necesarias (`eventos`, `usuarios`, `ajustes`) e insertará algunos datos de prueba.

## 3. Configuración del Proyecto Web
1. Mueve a la carpeta pública de tu servidor web (por ejemplo, `htdocs` en XAMPP, `www` en AppServ o `/var/www/html` en Linux) todos los archivos del proyecto.
2. Abre el archivo `db.php` con un editor de texto o código.
3. Verifica y ajusta las credenciales de conexión según tu entorno local:
   ```php
   $host = 'localhost';
   $db   = 'SentinelIT'; // El nombre de tu base de datos
   $user = 'root';       // Tu usuario de MySQL/MariaDB
   $pass = '';           // Tu contraseña de MySQL/MariaDB
   ```

## 4. Acceso al Panel
1. Abre tu navegador y dirígete a `http://localhost/SentinelIT-web` (o la ruta donde hayas colocado el proyecto).
2. Accede a la sección de **Iniciar Sesión**.
3. Las credenciales de prueba por defecto (si no has modificado los hashes en la base de datos) son:
   - **Administrador:** admin@SentinelIT.com / admin123
   - **Clientes:** cliente1@SentinelIT.com o cliente2@SentinelIT.com / cliente123

## 5. Configuración de los Agentes (Sensores Raspberry Pi)
*(Opcional: solo si conectarás agentes reales al panel)*
Para que una Raspberry Pi envíe datos a este panel, asegúrate de que el script en Python o Bash alojado en tu Raspberry inserte directamente los registros (tipo de evento, servicio, IP detectada) en la tabla `eventos` de esta misma base de datos o envíe peticiones POST a un archivo PHP de recepción que deberás habilitar.

