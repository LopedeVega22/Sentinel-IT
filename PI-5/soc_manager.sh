#!/bin/bash
# ==============================================================================
# SOC Manager - NODO COORDINADOR IA (Raspberry Pi 5)
# ==============================================================================
# Script interactivo y unificado para gestionar el SOC.

# Nombres canónicos de certificados:
CERT_NAME="Pi5-dani.cert.pem"
KEY_NAME="Pi5-dani.private.key"
CA_NAME="root-CA.crt"
REPO_URL="https://github.com/LopedeVega22/Sentinel-IT.git"
CLONE_DIR=".soc_engine_src"

# Colores para estética
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

function show_header() {
    clear
    echo -e "${BLUE}======================================${NC}"
    echo -e "${BLUE}  🛡️ Sentinel-IT SOC Manager - Pi5${NC}"
    echo -e "${BLUE}======================================${NC}"
    echo ""
}

function check_root() {
    if [ "$EUID" -ne 0 ]; then
        show_header
        echo -e "${RED}[ERROR] Este script requiere permisos de administrador para ejecutarse correctamente.${NC}"
        echo -e "${YELLOW}Por favor, inicia la ejecución con sudo: sudo $0${NC}"
        echo ""
        exit 1
    fi
}

function verify_prerequisites() {
    local needs_restart=false
    
    if ! command -v git &> /dev/null; then
        echo -e "${YELLOW}[INFO] Git no encontrado. Instalando...${NC}"
        sudo apt-get update -qq && sudo apt-get install -y -qq git
    fi
    
    if ! command -v docker &> /dev/null; then
        echo -e "${YELLOW}[INFO] Docker no encontrado. Instalando...${NC}"
        sudo apt-get update -qq && sudo apt-get install -y -qq ca-certificates curl
        curl -fsSL https://get.docker.com | sudo sh
        sudo usermod -aG docker "$USER"
        needs_restart=true
    fi
    
    if ! docker compose version &> /dev/null; then
        echo -e "${YELLOW}[INFO] docker-compose-plugin no encontrado. Instalando...${NC}"
        sudo apt-get update -qq && sudo apt-get install -y -qq docker-compose-plugin
    fi

    if [ "$needs_restart" = true ]; then
        echo -e "${RED}[WARNING] Docker se ha instalado por primera vez. Reinicia sesión o usa 'newgrp docker' y vuelve a ejecutar.${NC}"
        exit 0
    fi
}

function prepare_environment() {
    echo -e "${GREEN}[*] Opción 1: Preparar Entorno y Credenciales${NC}"
    if [ ! -d "./certificados" ]; then
        mkdir -p ./certificados
        chmod 700 ./certificados
        echo -e "${GREEN}[SUCCESS] Carpeta 'certificados/' creada. Mueve ahí los ficheros AWS (.pem, .key, root-CA.crt).${NC}"
    else
        echo -e "${BLUE}[INFO] Inspeccionando carpeta certificados/...${NC}"
        for f in ./certificados/*; do
            [ -f "$f" ] || continue
            local nombre=$(basename "$f")
            local nombre_lower=$(echo "$nombre" | tr '[:upper:]' '[:lower:]')
            
            # (Simplificación de la lógica de renormalización que existía)
            if [[ "$nombre_lower" == *"private"* ]] && [ ! -f "./certificados/$KEY_NAME" ]; then
                mv "$f" "./certificados/$KEY_NAME"
                echo "   -> Renombrado a $KEY_NAME"
            elif [[ "$nombre_lower" == *"root"* ]] && [ ! -f "./certificados/$CA_NAME" ]; then
                mv "$f" "./certificados/$CA_NAME"
                echo "   -> Renombrado a $CA_NAME"
            elif [[ "$nombre_lower" =~ \.pem$|\.crt$ ]] && [[ ! "$nombre_lower" == *"root"* ]] && [[ ! "$nombre_lower" == *"public"* ]] && [ ! -f "./certificados/$CERT_NAME" ]; then
                mv "$f" "./certificados/$CERT_NAME"
                echo "   -> Renombrado a $CERT_NAME"
            fi
        done
        
        # Validar existencia
        local ok=true
        for expected in "./certificados/$CERT_NAME" "./certificados/$KEY_NAME" "./certificados/$CA_NAME"; do
            if [ ! -f "$expected" ]; then
                echo -e "${RED}[WARNING] Falta: $(basename "$expected")${NC}"
                ok=false
            fi
        done
        if [ "$ok" = true ]; then
            echo -e "${GREEN}[SUCCESS] Todos los certificados están listos.${NC}"
        fi
    fi

    local configure_env=true
    if [ -f "./.env" ]; then
        echo -e "${BLUE}[INFO] El archivo .env ya está configurado.${NC}"
        echo -ne "\n"
        read -rp "   ¿Deseas volver a configurar el motor de IA y las credenciales? [s/N]: " reconf
        if [[ ! "$reconf" =~ ^[sS]$ ]]; then
            configure_env=false
        fi
    fi

    if [ "$configure_env" = true ]; then
        echo ""
        echo -e "${YELLOW}   ¿Qué tipo de motor IA deseas usar?${NC}"
        echo "   1) Local (Ollama) [Recomendado - Zero Trust]"
        echo "   2) Google API (Gemini Cloud)"
        read -rp "   Opción (1/2) [1]: " ai_opcion
        ai_opcion=${ai_opcion:-1}

        GEMINI_KEY=""

        if [ "$ai_opcion" == "1" ]; then
            AI_MODE="local"
            echo ""
            echo -e "${YELLOW}   ¿Qué modelo local quieres instalar/usar?${NC}"
            echo "   1) gemma:2b (Equilibrado para Raspberry Pi 5)"
            echo "   2) llama3.2:1b (Más rápido)"
            echo "   3) qwen2.5:1.5b (Destacado para Edge)"
            echo "   4) gemma4:e2b (Por defecto)"
            read -rp "   Selecciona (1-4) o escribe el nombre exacto [4]: " model_choice
            
            case $model_choice in
                1) AI_MODEL="ollama/gemma:2b" ;;
                2) AI_MODEL="ollama/llama3.2:1b" ;;
                3) AI_MODEL="ollama/qwen2.5:1.5b" ;;
                4|"") AI_MODEL="ollama/gemma4:e2b" ;;
                *) AI_MODEL="ollama/${model_choice}" ;;
            esac
        elif [ "$ai_opcion" == "2" ]; then
            AI_MODE="api"
            echo ""
            echo -e "${YELLOW}   ¿Qué modelo de Gemini vas a utilizar?${NC}"
            echo "   1) gemini-flash-latest (Por defecto, rápido y equilibrado)"
            echo "   2) gemini-pro-latest (Avanzado)"
            read -rp "   Selecciona (1-2) o escribe su nombre [1]: " model_choice

            case $model_choice in
                1|"") AI_MODEL="gemini-flash-latest" ;;
                2) AI_MODEL="gemini-pro-latest" ;;
                *) AI_MODEL="${model_choice}" ;;
            esac

            echo ""
            read -rp "   Introduce tu GEMINI_API_KEY: " GEMINI_KEY
        fi

        echo ""
        read -rp "   Usuario para el Dashboard [admin]: " dash_user
        dash_user=${dash_user:-admin}
        read -rsp "   Contraseña para el Dashboard: " dash_pass
        echo ""
        cat > ./.env << EOF
AI_MODE=${AI_MODE}
AI_MODEL=${AI_MODEL}
GEMINI_API_KEY=${GEMINI_KEY}
DASHBOARD_USER=${dash_user}
DASHBOARD_PASSWORD=${dash_pass}
EOF
        # Limpiar caracteres \r (saltos de línea de Windows)
        sed -i 's/\r$//' ./.env
        chmod 600 ./.env
        echo -e "${GREEN}[SUCCESS] Archivo '.env' generado (Modo: ${AI_MODE}).${NC}"
    fi

    read -n 1 -s -r -p "Presiona cualquier tecla para volver al menú..."
}

function start_soc() {
    echo -e "${GREEN}[*] Opción 2: Arrancar SOC${NC}"
    verify_prerequisites
    
    if [ ! -d "./certificados" ] || [ ! -f "./.env" ]; then
        echo -e "${RED}[ERROR] Faltan credenciales. Ejecuta la Opción 1 primero.${NC}"
        read -n 1 -s -r -p "Presiona cualquier tecla para volver al menú..."
        return
    fi

    if [ -f "./docker-compose.yml" ]; then
        echo -e "${BLUE}[INFO] Modo de directorio local detectado.${NC}"
        
        # Sincronización automática de código en despliegue continuo (GitOps) si hay un repo activo
        if [ -d ".git" ]; then
            echo -e "${BLUE}[INFO] Repositorio Git local detectado. Sincronizando últimos cambios de GitHub...${NC}"
            # Se aplica git pull, mostrando aviso si hay conflicto con cambios por SCP locales
            git pull || echo -e "${YELLOW}[WARN] Hubo un error haciendo 'git pull'. Si has modificado archivos locales directamente (por ejemplo, con SCP), resuelve los conflictos para que Git aplique la versión de la nube.${NC}"
        fi

        echo -e "${BLUE}[INFO] Reconstruyendo y levantando contenedor Docker...${NC}"
        docker compose up -d --build
    else
        echo -e "${BLUE}[INFO] Sincronizando código GitOps externo...${NC}"
        rm -rf "$CLONE_DIR"
        git clone -q "$REPO_URL" "$CLONE_DIR"
        
        # Inyectando vars a GitOps path
        cp -r ./certificados "$CLONE_DIR/PI-5/certificados"
        cp ./.env "$CLONE_DIR/PI-5/.env"
        
        cd "$CLONE_DIR/PI-5" || return
        docker compose up -d --build
        cd - > /dev/null
    fi

    if [ -f "./.env" ]; then
        # Aseguramos que no haya rastro de formato de Windows antes de cargarlo
        sed -i 's/\r$//' ./.env
        source ./.env
        if [ "$AI_MODE" == "local" ]; then
            local_model_name=${AI_MODEL#ollama/}
            echo -e "${YELLOW}=======================================================${NC}"
            echo -e "${BLUE}[INFO] Modo local: Verificando/Descargando modelo '${local_model_name}' en Ollama...${NC}"
            echo -e "${YELLOW}Esto puede tardar unos minutos si es la primera vez.${NC}"
            echo -e "${YELLOW}=======================================================${NC}"
            docker exec local-ai-engine ollama pull "$local_model_name"
        fi
    fi

    echo -e "${GREEN}=======================================================${NC}"
    echo -e "${GREEN}[SUCCESS] COORDINADOR IA OPERATIVO!${NC}"
    echo -e "» Dashboard: http://localhost:5000"
    echo -e "${GREEN}=======================================================${NC}"
    read -n 1 -s -r -p "Presiona cualquier tecla para volver al menú..."
}

function stop_soc() {
    echo -e "${GREEN}[*] Opción 3: Detener SOC${NC}"
    if [ -f "./docker-compose.yml" ]; then
        docker compose down
    elif [ -d "$CLONE_DIR/PI-5" ]; then
        cd "$CLONE_DIR/PI-5" && docker compose down && cd - > /dev/null
    fi
    echo -e "${GREEN}[SUCCESS] Servicios detenidos.${NC}"
    read -n 1 -s -r -p "Presiona cualquier tecla para volver al menú..."
}

function view_logs() {
    echo -e "${GREEN}[*] Opción 4: Ver Logs de Docker Compose${NC}"
    echo "Pulsa Ctrl+C para salir de los logs de vuelta al sistema (El servicio seguirá corriendo)."
    sleep 2
    if [ -f "./docker-compose.yml" ]; then
        docker compose logs -f
    elif [ -d "$CLONE_DIR/PI-5" ]; then
        cd "$CLONE_DIR/PI-5" && docker compose logs -f && cd - > /dev/null
    else
        echo -e "${RED}[ERROR] No se encuentra el docker-compose.${NC}"
        read -n 1 -s -r -p "Presiona cualquier tecla para volver al menú..."
    fi
}

function uninstall_soc() {
    echo -e "${GREEN}[*] Opción 5: Desinstalar SOC${NC}"
    echo -e "${YELLOW}ADVERTENCIA: Estás a punto de desinstalar el sistema.${NC}"
    echo "1) Desinstalación completa (Borrará contenedores, imágenes, volúmenes, '.env' y certificados)"
    echo "2) Desinstalación parcial (Borrará contenedores e imágenes, mantendrá logs, '.env' y certificados)"
    echo "3) Cancelar"
    read -rp "Selecciona una opción (1-3): " uninst_opt

    case $uninst_opt in
        1)
            echo -e "${RED}[!] Iniciando desinstalación completa...${NC}"
            if [ -f "./docker-compose.yml" ]; then
                docker compose down -v --rmi all
            elif [ -d "$CLONE_DIR/PI-5" ]; then
                cd "$CLONE_DIR/PI-5" && docker compose down -v --rmi all && cd - > /dev/null
            fi
            echo -e "${BLUE}[INFO] Eliminando credenciales y código...${NC}"
            rm -rf ./certificados
            rm -f ./.env
            rm -rf "$CLONE_DIR"
            echo -e "${GREEN}[SUCCESS] Desinstalación completa finalizada.${NC}"
            read -n 1 -s -r -p "Presiona cualquier tecla para volver al menú..."
            ;;
        2)
            echo -e "${YELLOW}[!] Iniciando desinstalación parcial...${NC}"
            if [ -f "./docker-compose.yml" ]; then
                docker compose down --rmi all
            elif [ -d "$CLONE_DIR/PI-5" ]; then
                cd "$CLONE_DIR/PI-5" && docker compose down --rmi all && cd - > /dev/null
            fi
            echo -e "${BLUE}[INFO] Eliminando directorio de código fuente clonado...${NC}"
            rm -rf "$CLONE_DIR"
            echo -e "${GREEN}[SUCCESS] Desinstalación parcial finalizada.${NC}"
            read -n 1 -s -r -p "Presiona cualquier tecla para volver al menú..."
            ;;
        3|*)
            echo -e "${BLUE}Operación cancelada.${NC}"
            sleep 1
            ;;
    esac
}

check_root

while true; do
    show_header
    echo "1) Preparar Entorno y Credenciales"
    echo "2) Arrancar SOC (Clonar/Actualizar Docker)"
    echo "3) Detener SOC"
    echo "4) Ver Logs"
    echo "5) Desinstalar SOC"
    echo "6) Salir"
    echo -e "${BLUE}--------------------------------------${NC}"
    read -rp "Selecciona una opción: " opt
    
    case $opt in
        1) prepare_environment ;;
        2) start_soc ;;
        3) stop_soc ;;
        4) view_logs ;;
        5) uninstall_soc ;;
        6) echo -e "${BLUE}Saliendo...${NC}"; exit 0 ;;
        *) echo -e "${RED}Opción inválida.${NC}"; sleep 1 ;;
    esac
done
