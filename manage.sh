#!/bin/bash

# CTF Rclone MVP Management Script
# Usage: ./manage.sh [start|stop|restart|status|logs] [service]

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"
LOG_DIR="$SCRIPT_DIR/logs"

# PID file locations
PID_DIR="$SCRIPT_DIR/.pids"
mkdir -p "$PID_DIR"
mkdir -p "$LOG_DIR"

# Service definitions
get_service_port() {
    case "$1" in
        backend) echo 8000 ;;
        frontend) echo 3000 ;;
        *) echo "" ;;
    esac
}

# Check if virtual environment exists
check_venv() {
    if [ ! -d "$BACKEND_DIR/venv" ]; then
        echo -e "${YELLOW}Creating Python virtual environment...${NC}"
        cd "$BACKEND_DIR"
        python3 -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt
        cd "$SCRIPT_DIR"
    fi
}

# Check if a service is running by checking the PID file
is_running_pid() {
    local service=$1
    local pid_file="$PID_DIR/$service.pid"
    if [ -f "$pid_file" ]; then
        local pid
        pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0 # Running
        fi
    fi
    return 1 # Not running
}

# Check if a port is in use
is_port_in_use() {
    local port=$1
    if [ -z "$port" ]; then
        return 1 # No port to check
    fi
    # lsof returns 0 if process found, 1 if not
    if lsof -i :"$port" > /dev/null 2>&1; then
        return 0 # Port is in use
    fi
    return 1 # Port is free
}

# Start services
start_service() {
    local service=$1
    local start_command=$2
    local log_file="$LOG_DIR/$service.log"
    local pid_file="$PID_DIR/$service.pid"
    local port

    port=$(get_service_port "$service")

    if is_running_pid "$service"; then
        echo -e "${YELLOW}$service is already running.${NC}"
        return 0
    fi

    if is_port_in_use "$port"; then
        echo -e "${RED}Port $port for $service is already in use by another process.${NC}"
        return 1
    fi

    echo -e "${YELLOW}Starting $service...${NC}"
    
    # Execute the start command in the background
    eval "$start_command" > "$log_file" 2>&1 &
    local pid=$!
    echo "$pid" > "$pid_file"

    sleep 3 # Wait a moment for the service to potentially fail

    if ! ps -p "$pid" > /dev/null 2>&1; then
        echo -e "${RED}$service failed to start. Check logs: ./manage.sh logs $service${NC}"
        rm -f "$pid_file"
        return 1
    fi

    echo -e "${GREEN}$service started successfully (PID: $pid).${NC}"
    return 0
}

start_docker() {
    echo -e "${YELLOW}Starting Docker containers...${NC}"
    cd "$SCRIPT_DIR"
    docker-compose up -d
    echo -e "${GREEN}Docker containers started${NC}"
}

start_all_services() {
    start_docker
    sleep 5 # Wait for containers to initialize
    
    check_venv
    
    start_service "backend" "cd '$BACKEND_DIR' && source venv/bin/activate && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
    start_service "frontend" "cd '$FRONTEND_DIR' && npm start"
    start_service "worker" "cd '$BACKEND_DIR' && source venv/bin/activate && python worker.py"
    start_service "event-monitor" "cd '$BACKEND_DIR' && source venv/bin/activate && python event_monitor_service.py"
    # start_service "scheduler" "cd '$BACKEND_DIR' && source venv/bin/activate && python scheduler_service.py"
}

# Stop services
stop_service() {
    local service=$1
    local pid_file="$PID_DIR/$service.pid"
    local port
    
    port=$(get_service_port "$service")
    echo -e "${YELLOW}Stopping $service...${NC}"

    # Kill by PID file
    if [ -f "$pid_file" ]; then
        local pid
        pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            kill "$pid" 2>/dev/null || true
            sleep 1
            # Force kill if still running
            if ps -p "$pid" > /dev/null 2>&1; then
                kill -9 "$pid" 2>/dev/null || true
            fi
        else
            echo -e "${YELLOW}Stale PID file found for $service.${NC}"
        fi
        rm -f "$pid_file"
    fi

    # Kill any process using the port
    if [ -n "$port" ]; then
        local pids_on_port
        pids_on_port=$(lsof -t -i:"$port" 2>/dev/null)
        if [ -n "$pids_on_port" ]; then
            echo -e "${YELLOW}Force stopping process(es) on port $port...${NC}"
            # Convert newlines to spaces and kill all PIDs
            echo "$pids_on_port" | xargs kill -9 2>/dev/null || true
        fi
    fi
    
    echo -e "${GREEN}$service stopped.${NC}"
}

stop_docker() {
    echo -e "${YELLOW}Stopping Docker containers...${NC}"
    cd "$SCRIPT_DIR"
    docker-compose down
    echo -e "${GREEN}Docker containers stopped${NC}"
}

stop_all_services() {
    stop_service "scheduler"
    stop_service "event-monitor"
    stop_service "worker"
    stop_service "frontend"
    stop_service "backend"
    stop_docker
}

# Check service status
check_status() {
    local service=$1
    local pid_file="$PID_DIR/$service.pid"
    local port
    port=$(get_service_port "$service")

    if is_running_pid "$service"; then
        echo -e "${GREEN}✓ $service is running (PID: $(cat "$pid_file"))${NC}"
    elif is_port_in_use "$port"; then
        echo -e "${YELLOW}⚠ $service is not running via manage.sh, but port $port is in use.${NC}"
    else
        echo -e "${RED}✗ $service is not running${NC}"
    fi
}

check_docker_status() {
    if docker-compose ps | grep -q "Up"; then
        echo -e "${GREEN}✓ Docker containers are running${NC}"
        docker-compose ps
    else
        echo -e "${RED}✗ Docker containers are not running${NC}"
    fi
}

# View logs
view_logs() {
    local service=$1
    local log_file="$LOG_DIR/$service.log"
    
    if [ -f "$log_file" ]; then
        echo -e "${YELLOW}Showing last 50 lines of $service logs:${NC}"
        tail -n 50 "$log_file"
    else
        echo -e "${RED}No log file found for $service${NC}"
    fi
}

# Main command handling
case "$1" in
    start)
        if [ -z "$2" ]; then
            start_all_services
        else
            case "$2" in
                docker) start_docker ;;
                backend) check_venv; start_service "backend" "cd '$BACKEND_DIR' && source venv/bin/activate && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000" ;;
                frontend) start_service "frontend" "cd '$FRONTEND_DIR' && npm start" ;;
                worker) check_venv; start_service "worker" "cd '$BACKEND_DIR' && source venv/bin/activate && python worker.py" ;;
                event-monitor) check_venv; start_service "event-monitor" "cd '$BACKEND_DIR' && source venv/bin/activate && python event_monitor_service.py" ;;
                scheduler) check_venv; start_service "scheduler" "cd '$BACKEND_DIR' && source venv/bin/activate && python scheduler_service.py" ;;
                *) echo -e "${RED}Unknown service: $2${NC}"; exit 1 ;;
            esac
        fi
        ;;
    
    stop)
        if [ -z "$2" ]; then
            stop_all_services
        else
            case "$2" in
                docker) stop_docker ;;
                backend|frontend|worker|event-monitor|scheduler) stop_service "$2" ;;
                *) echo -e "${RED}Unknown service: $2${NC}"; exit 1 ;;
            esac
        fi
        ;;
    
    restart)
        if [ -z "$2" ]; then
            stop_all_services
            echo -e "${YELLOW}Restarting all services...${NC}"
            sleep 2
            start_all_services
        else
            stop_service "$2"
            echo -e "${YELLOW}Restarting $2...${NC}"
            sleep 2
            $0 start "$2"
        fi
        ;;
    
    status)
        echo -e "${YELLOW}=== CTF Rclone MVP Status ===${NC}"
        check_docker_status
        check_status "backend"
        check_status "frontend"
        check_status "worker"
        check_status "event-monitor"
        check_status "scheduler"
        ;;
    
    logs)
        if [ -z "$2" ]; then
            echo -e "${RED}Please specify a service to view logs${NC}"
            echo "Available services: backend, frontend, worker, event-monitor, scheduler"
        else
            view_logs "$2"
        fi
        ;;
    
    *)
        echo "CTF Rclone MVP Management Script"
        echo "Usage: $0 [start|stop|restart|status|logs] [service]"
        echo ""
        echo "Commands:"
        echo "  start [service]    - Start all services or a specific service"
        echo "  stop [service]     - Stop all services or a specific service"
        echo "  restart [service]  - Restart all services or a specific service"
        echo "  status            - Show status of all services"
        echo "  logs <service>    - View logs for a specific service"
        echo ""
        echo "Services:"
        echo "  docker       - Docker containers (PostgreSQL, Redis, Rclone)"
        echo "  backend      - FastAPI backend API"
        echo "  frontend     - React web interface"
        echo "  worker       - Job processor"
        echo "  event-monitor - File system event monitor"
        echo "  scheduler    - Cron job scheduler"
        echo ""
        echo "Examples:"
        echo "  $0 start           # Start all services"
        echo "  $0 stop backend    # Stop only the backend"
        echo "  $0 restart worker  # Restart the worker"
        echo "  $0 status          # Check all services"
        echo "  $0 logs worker     # View worker logs"
        ;;
esac