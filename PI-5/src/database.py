import sqlite3
import os
import yaml

# Rutas base y configuracion
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
CONFIG_PATH = os.path.join(BASE_DIR, 'config.yml')

# Carga de la ruta de la base de datos desde el archivo de configuracion
try:
    with open(CONFIG_PATH, "r") as f:
        config = yaml.safe_load(f)
    DB_PATH = os.path.join(BASE_DIR, config['database']['db_path'])
except Exception as e:
    print(f"[ERROR] Error al cargar configuracion, usando ruta por defecto: {e}")
    DB_PATH = os.path.join(BASE_DIR, "soc_data.db")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Esquema de la tabla 'logs' para almacenar incidentes y decisiones del agente IA
cursor.execute('''
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dispositivo TEXT,
        servicio TEXT,
        log_original TEXT,
        ip_origen TEXT,
        nivel_gravedad TEXT,
        veredicto_ia TEXT,
        accion_tomada TEXT,
        estado_mitigacion TEXT,
        status TEXT DEFAULT 'LOGGED',
        pending_command TEXT,
        rationale TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
''')

# Migración para bases de datos existentes: intentar añadir las nuevas columnas
try:
    cursor.execute('ALTER TABLE logs ADD COLUMN estado_mitigacion TEXT')
except sqlite3.OperationalError:
    pass

try:
    cursor.execute("ALTER TABLE logs ADD COLUMN status TEXT DEFAULT 'LOGGED'")
    cursor.execute("ALTER TABLE logs ADD COLUMN pending_command TEXT")
    cursor.execute("ALTER TABLE logs ADD COLUMN rationale TEXT")
except sqlite3.OperationalError:
    pass

# Tabla de auditoria append-only para el Policy Engine.
# Cierra el hueco "sin trazabilidad ordenada" del doc futuras_mejoras.md
# (mapeo con NIST SP 800-53 AU-2 e ISO 27001 A.12.4).
cursor.execute('''
    CREATE TABLE IF NOT EXISTS audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts DATETIME DEFAULT CURRENT_TIMESTAMP,
        event_type TEXT,
        device TEXT,
        command TEXT,
        classification TEXT,
        decision_reason TEXT,
        related_log_id INTEGER,
        FOREIGN KEY (related_log_id) REFERENCES logs(id)
    )
''')

# Triggers anti-modificacion: la integridad del log de auditoria depende de
# que nadie pueda editarlo a posteriori desde la aplicacion.
cursor.execute('''
    CREATE TRIGGER IF NOT EXISTS audit_log_no_update
    BEFORE UPDATE ON audit_log
    BEGIN
        SELECT RAISE(ABORT, 'audit_log is append-only');
    END
''')
cursor.execute('''
    CREATE TRIGGER IF NOT EXISTS audit_log_no_delete
    BEFORE DELETE ON audit_log
    BEGIN
        SELECT RAISE(ABORT, 'audit_log is append-only');
    END
''')

conn.commit()
conn.close()

print(f"[INFO] Base de datos preparada en: {DB_PATH}")

