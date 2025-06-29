#!/bin/bash

# PBS Rclone MVP Management Script
# Usage: ./manage.sh [start|stop|restart|status|logs] [service]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"

# PID file locations
PID_DIR="$SCRIPT_DIR/.pids"
mkdir -p "$PID_DIR"

# Service definitions
# Note: We use a function instead of associative array for macOS compatibility
get_service_description() {
    case "$1" in
        docker) echo "Docker containers" ;;
        backend) echo "FastAPI backend" ;;
        frontend) echo "React frontend" ;;
        worker) echo "Job processor" ;;
        event-monitor) echo "Event monitor" ;;
        scheduler) echo "Scheduler service" ;;
        *) echo "Unknown service" ;;
    esac
}

# Check if virtual environment exists
check_venv() {
    if [ ! -d "$BACKEND_DIR/venv" ]; then
        echo -e "${RED}Error: Virtual environment not found at $BACKEND_DIR/venv${NC}"
        echo "Please create it with: cd $BACKEND_DIR && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
        exit 1
    fi
}

# Check if a service is running
check_if_running() {
    local service=$1
    local pid_file="$PID_DIR/$service.pid"
    
    if [ -f "$pid_file" ]; then
        PID=$(cat "$pid_file")
        if ps -p $PID > /dev/null 2>&1; then
            return 0  # Service is running
        fi
    fi
    return 1  # Service is not running
}

# Start services
start_docker() {
    echo -e "${YELLOW}Starting Docker containers...${NC}"
    cd "$SCRIPT_DIR"
    docker-compose up -d
    echo -e "${GREEN}Docker containers started${NC}"
}

start_backend() {
    # Check if already running
    if check_if_running "backend"; then
        echo -e "${YELLOW}Backend is already running${NC}"
        return 0
    fi
    
    check_venv
    echo -e "${YELLOW}Starting FastAPI backend...${NC}"
    cd "$BACKEND_DIR"
    source venv/bin/activate
    nohup python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > "$SCRIPT_DIR/logs/backend.log" 2>&1 &
    local pid=$!
    echo $pid > "$PID_DIR/backend.pid"
    
    # Wait a moment and verify the process started
    sleep 2
    if ps -p $pid > /dev/null 2>&1; then
        echo -e "${GREEN}Backend started on http://localhost:8000${NC}"
    else
        echo -e "${RED}Backend failed to start. Check logs with: $0 logs backend${NC}"
        rm -f "$PID_DIR/backend.pid"
        return 1
    fi
}

start_frontend() {
    # Check if already running
    if check_if_running "frontend"; then
        echo -e "${YELLOW}Frontend is already running${NC}"
        return 0
    fi
    
    echo -e "${YELLOW}Starting React frontend...${NC}"
    cd "$FRONTEND_DIR"
    nohup npm start > "$SCRIPT_DIR/logs/frontend.log" 2>&1 &
    local pid=$!
    echo $pid > "$PID_DIR/frontend.pid"
    
    # Wait a moment and verify the process started
    sleep 3
    if ps -p $pid > /dev/null 2>&1; then
        echo -e "${GREEN}Frontend started on http://localhost:3000${NC}"
    else
        echo -e "${RED}Frontend failed to start. Check logs with: $0 logs frontend${NC}"
        rm -f "$PID_DIR/frontend.pid"
        return 1
    fi
}

start_worker() {
    # Check if already running
    if check_if_running "worker"; then
        echo -e "${YELLOW}Worker is already running${NC}"
        return 0
    fi
    
    check_venv
    echo -e "${YELLOW}Starting worker...${NC}"
    cd "$BACKEND_DIR"
    source venv/bin/activate
    nohup python worker.py > "$SCRIPT_DIR/logs/worker.log" 2>&1 &
    local pid=$!
    echo $pid > "$PID_DIR/worker.pid"
    
    # Wait a moment and verify the process started
    sleep 2
    if ps -p $pid > /dev/null 2>&1; then
        echo -e "${GREEN}Worker started${NC}"
    else
        echo -e "${RED}Worker failed to start. Check logs with: $0 logs worker${NC}"
        rm -f "$PID_DIR/worker.pid"
        return 1
    fi
}

start_event_monitor() {
    # Check if already running
    if check_if_running "event-monitor"; then
        echo -e "${YELLOW}Event monitor is already running${NC}"
        return 0
    fi
    
    check_venv
    echo -e "${YELLOW}Starting event monitor...${NC}"
    cd "$BACKEND_DIR"
    source venv/bin/activate
    nohup python event_monitor_service.py > "$SCRIPT_DIR/logs/event-monitor.log" 2>&1 &
    local pid=$!
    echo $pid > "$PID_DIR/event-monitor.pid"
    
    # Wait a moment and verify the process started
    sleep 2
    if ps -p $pid > /dev/null 2>&1; then
        echo -e "${GREEN}Event monitor started${NC}"
    else
        echo -e "${RED}Event monitor failed to start. Check logs with: $0 logs event-monitor${NC}"
        rm -f "$PID_DIR/event-monitor.pid"
        return 1
    fi
}

start_scheduler() {
    # Check if already running
    if check_if_running "scheduler"; then
        echo -e "${YELLOW}Scheduler is already running${NC}"
        return 0
    fi
    
    check_venv
    echo -e "${YELLOW}Starting scheduler...${NC}"
    cd "$BACKEND_DIR"
    source venv/bin/activate
    nohup python scheduler_service.py > "$SCRIPT_DIR/logs/scheduler.log" 2>&1 &
    local pid=$!
    echo $pid > "$PID_DIR/scheduler.pid"
    
    # Wait a moment and verify the process started
    sleep 2
    if ps -p $pid > /dev/null 2>&1; then
        echo -e "${GREEN}Scheduler started${NC}"
    else
        echo -e "${RED}Scheduler failed to start. Check logs with: $0 logs scheduler${NC}"
        rm -f "$PID_DIR/scheduler.pid"
        return 1
    fi
}

# Stop services
stop_service() {
    local service=$1
    local pid_file="$PID_DIR/$service.pid"
    
    if [ -f "$pid_file" ]; then
        PID=$(cat "$pid_file")
        if ps -p $PID > /dev/null 2>&1; then
            echo -e "${YELLOW}Stopping $service (PID: $PID)...${NC}"
            kill $PID
            rm "$pid_file"
            echo -e "${GREEN}$service stopped${NC}"
        else
            echo -e "${YELLOW}$service not running (stale PID file)${NC}"
            rm "$pid_file"
        fi
    else
        echo -e "${YELLOW}$service not running${NC}"
    fi
}

stop_docker() {
    echo -e "${YELLOW}Stopping Docker containers...${NC}"
    cd "$SCRIPT_DIR"
    docker-compose down
    echo -e "${GREEN}Docker containers stopped${NC}"
}

# Check service status
check_status() {
    local service=$1
    local pid_file="$PID_DIR/$service.pid"
    
    if [ -f "$pid_file" ]; then
        PID=$(cat "$pid_file")
        if ps -p $PID > /dev/null 2>&1; then
            echo -e "${GREEN}✓ $service is running (PID: $PID)${NC}"
            return 0
        else
            echo -e "${RED}✗ $service is not running (stale PID file)${NC}"
            return 1
        fi
    else
        echo -e "${RED}✗ $service is not running${NC}"
        return 1
    fi
}

check_docker_status() {
    if docker ps | grep -q "pbs-rclone"; then
        echo -e "${GREEN}✓ Docker containers are running${NC}"
        docker ps --format "table {{.Names}}\t{{.Status}}" | grep "pbs-rclone"
    else
        echo -e "${RED}✗ Docker containers are not running${NC}"
    fi
}

# View logs
view_logs() {
    local service=$1
    local log_file="$SCRIPT_DIR/logs/$service.log"
    
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
        mkdir -p "$SCRIPT_DIR/logs"
        if [ -z "$2" ]; then
            # Start all services
            start_docker
            sleep 5  # Wait for containers
            start_backend
            sleep 3  # Wait for backend
            start_frontend
            start_worker
            start_event_monitor
            # start_scheduler  # Uncomment when ready
        else
            # Start specific service
            case "$2" in
                docker) start_docker ;;
                backend) start_backend ;;
                frontend) start_frontend ;;
                worker) start_worker ;;
                event-monitor) start_event_monitor ;;
                scheduler) start_scheduler ;;
                *) echo -e "${RED}Unknown service: $2${NC}"; exit 1 ;;
            esac
        fi
        ;;
    
    stop)
        if [ -z "$2" ]; then
            # Stop all services
            stop_service "scheduler"
            stop_service "event-monitor"
            stop_service "worker"
            stop_service "frontend"
            stop_service "backend"
            stop_docker
        else
            # Stop specific service
            case "$2" in
                docker) stop_docker ;;
                backend|frontend|worker|event-monitor|scheduler) stop_service "$2" ;;
                *) echo -e "${RED}Unknown service: $2${NC}"; exit 1 ;;
            esac
        fi
        ;;
    
    restart)
        $0 stop $2
        sleep 2
        $0 start $2
        ;;
    
    status)
        echo -e "${YELLOW}=== PBS Rclone MVP Status ===${NC}"
        check_docker_status
        check_status "backend" || true
        check_status "frontend" || true
        check_status "worker" || true
        check_status "event-monitor" || true
        check_status "scheduler" || true
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
        echo "PBS Rclone MVP Management Script"
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