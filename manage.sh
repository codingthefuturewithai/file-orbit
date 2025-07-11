#!/bin/bash

# CTF Rclone MVP Management Script
# Usage: ./manage.sh [start|stop|restart|status|logs] [all|service]

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

    # For frontend, find an available port starting from 3000
    if [ "$service" = "frontend" ]; then
        local test_port=3000
        while is_port_in_use "$test_port"; do
            test_port=$((test_port + 1))
        done
        if [ "$test_port" != "3000" ]; then
            echo -e "${YELLOW}Port 3000 is in use. Starting frontend on port $test_port${NC}"
        fi
        # Replace PORT in the start command
        start_command=$(echo "$start_command" | sed "s|npm start|PORT=$test_port npm start|")
    elif is_port_in_use "$port"; then
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
    start_service "frontend" "cd '$FRONTEND_DIR' && BROWSER=none npm start"
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

    # Only warn about port usage if we didn't have a PID file
    # This means another process is using the port, not our managed process
    if [ ! -f "$pid_file" ] && [ -n "$port" ]; then
        local pids_on_port
        pids_on_port=$(lsof -t -i:"$port" 2>/dev/null)
        if [ -n "$pids_on_port" ]; then
            echo -e "${YELLOW}Note: Port $port is still in use by another process (not managed by this script).${NC}"
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
    elif [ "$service" = "frontend" ] && is_port_in_use "$port"; then
        # For frontend, port in use might mean React started on a different port
        echo -e "${YELLOW}⚠ $service process not tracked by manage.sh, but something is using port $port${NC}"
        echo -e "${YELLOW}  (React may have started on a different port - check logs)${NC}"
    elif is_port_in_use "$port"; then
        echo -e "${YELLOW}⚠ $service is not running via manage.sh, but port $port is in use by another process${NC}"
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
CMD=$1
SERVICE=$2

# Function to display usage information
usage() {
    echo "Usage: $0 [start|stop|restart|status|logs] [all|service]"
    echo "Services: backend, frontend, worker, event-monitor, scheduler, docker"
    exit 1
}

# Require a command
if [ -z "$CMD" ]; then
    usage
fi

# Commands that require a service argument
case "$CMD" in
    start|stop|restart|status|logs)
        if [ -z "$SERVICE" ]; then
            echo -e "${RED}Error: Missing argument. Please specify 'all' or a service name.${NC}"
            usage
        fi
        ;;
esac

case "$CMD" in
    start)
        case "$SERVICE" in
            all) start_all_services ;;
            docker) start_docker ;;
            backend) check_venv; start_service "backend" "cd '$BACKEND_DIR' && source venv/bin/activate && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000" ;;
            frontend) start_service "frontend" "cd '$FRONTEND_DIR' && BROWSER=none npm start" ;;
            worker) check_venv; start_service "worker" "cd '$BACKEND_DIR' && source venv/bin/activate && python worker.py" ;;
            event-monitor) check_venv; start_service "event-monitor" "cd '$BACKEND_DIR' && source venv/bin/activate && python event_monitor_service.py" ;;
            scheduler) check_venv; start_service "scheduler" "cd '$BACKEND_DIR' && source venv/bin/activate && python scheduler_service.py" ;;
            *) echo -e "${RED}Unknown service: $SERVICE${NC}"; usage ;;
        esac
        ;;
    stop)
        case "$SERVICE" in
            all) stop_all_services ;;
            docker) stop_docker ;;
            backend) stop_service "backend" ;;
            frontend) stop_service "frontend" ;;
            worker) stop_service "worker" ;;
            event-monitor) stop_service "event-monitor" ;;
            scheduler) stop_service "scheduler" ;;
            *) echo -e "${RED}Unknown service: $SERVICE${NC}"; usage ;;
        esac
        ;;
    restart)
        case "$SERVICE" in
            all)
                stop_all_services
                echo "---"
                start_all_services
                ;;
            *)
                stop_service "$SERVICE"
                sleep 1
                start_service "$SERVICE" # Simplified for individual services
                ;;
        esac
        ;;
    status)
        echo "=== CTF Rclone MVP Status ==="
        if [ "$SERVICE" = "all" ]; then
            check_docker_status
            check_status "backend"
            check_status "frontend"
            check_status "worker"
            check_status "event-monitor"
            check_status "scheduler"
        else
            if [ "$SERVICE" = "docker" ]; then
                check_docker_status
            else
                check_status "$SERVICE"
            fi
        fi
        ;;
    logs)
        if [ "$SERVICE" = "all" ]; then
            echo -e "${RED}Cannot view logs for 'all' services at once. Please specify a single service.${NC}"
            usage
        else
            view_logs "$SERVICE"
        fi
        ;;
    *)
        echo -e "${RED}Unknown command: $CMD${NC}"
        usage
        ;;
esac