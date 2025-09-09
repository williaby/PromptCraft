#!/bin/bash
# PromptCraft Hybrid Deployment Script
# Intelligently deploys PromptCraft with discovery-based MCP and agent systems

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="docker-compose.hybrid.yml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Docker and Docker Compose
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi
    
    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Discover existing services
discover_services() {
    log_info "Discovering existing services..."
    
    local services_found=()
    
    # Check for Zen MCP Server
    if curl -f -s http://localhost:8000/health &> /dev/null; then
        log_success "Found existing Zen MCP Server at localhost:8000"
        services_found+=("zen-mcp")
        export ZEN_MCP_EXTERNAL=true
    elif curl -f -s http://localhost:8001/health &> /dev/null; then
        log_success "Found existing Zen MCP Server at localhost:8001"
        services_found+=("zen-mcp")
        export ZEN_MCP_EXTERNAL=true
    else
        log_warn "No external Zen MCP Server found, will use embedded"
        export ZEN_MCP_EXTERNAL=false
    fi
    
    # Check for Qdrant
    if curl -f -s "http://${QDRANT_HOST:-192.168.1.16}:${QDRANT_PORT:-6333}/health" &> /dev/null; then
        log_success "Found external Qdrant at ${QDRANT_HOST:-192.168.1.16}:${QDRANT_PORT:-6333}"
        services_found+=("qdrant")
        export QDRANT_EXTERNAL=true
    else
        log_warn "External Qdrant not accessible, will use local instance"
        export QDRANT_EXTERNAL=false
    fi
    
    # Check for Redis
    if redis-cli -h "${REDIS_HOST:-localhost}" -p "${REDIS_PORT:-6379}" ping &> /dev/null; then
        log_success "Found external Redis at ${REDIS_HOST:-localhost}:${REDIS_PORT:-6379}"
        services_found+=("redis")
        export REDIS_EXTERNAL=true
    else
        log_warn "No external Redis found, will use embedded"
        export REDIS_EXTERNAL=false
    fi
    
    if [ ${#services_found[@]} -eq 0 ]; then
        log_warn "No external services found, using fully embedded deployment"
    else
        log_success "Found external services: ${services_found[*]}"
    fi
}

# Check resource availability
check_resources() {
    log_info "Checking system resources..."
    
    # Check available memory (in MB)
    local available_mem
    if command -v free &> /dev/null; then
        available_mem=$(free -m | awk 'NR==2{printf "%.0f", $7}')
    else
        # macOS fallback
        available_mem=$(vm_stat | awk '/Pages free:/{free=$3} /Pages inactive:/{inactive=$3} END{print (free+inactive)*4096/1024/1024}')
    fi
    
    log_info "Available memory: ${available_mem}MB"
    
    if [ "$available_mem" -lt 2048 ]; then
        log_warn "Low memory available (${available_mem}MB). Consider increasing limits."
        export MEMORY_CONSTRAINT=true
    else
        log_success "Sufficient memory available"
        export MEMORY_CONSTRAINT=false
    fi
    
    # Check available disk space (in GB)
    local available_disk
    available_disk=$(df "$PROJECT_DIR" | awk 'NR==2 {printf "%.0f", $4/1024/1024}')
    log_info "Available disk space: ${available_disk}GB"
    
    if [ "$available_disk" -lt 5 ]; then
        log_warn "Low disk space available (${available_disk}GB)"
    fi
}

# Build deployment profiles
build_profiles() {
    log_info "Building deployment profiles..."
    
    local profiles=()
    
    # Always include base services
    profiles+=("base")
    
    # Add MCP server if not external
    if [ "${ZEN_MCP_EXTERNAL:-false}" = "false" ]; then
        profiles+=("with-zen")
        log_info "Including embedded Zen MCP Server"
    fi
    
    # Add Qdrant if not external
    if [ "${QDRANT_EXTERNAL:-false}" = "false" ]; then
        profiles+=("with-qdrant")
        log_info "Including local Qdrant instance"
    fi
    
    # Add monitoring if requested
    if [ "${ENABLE_MONITORING:-false}" = "true" ]; then
        profiles+=("monitoring")
        log_info "Including monitoring stack"
    fi
    
    # Add production services if requested
    if [ "${ENVIRONMENT:-development}" = "production" ]; then
        profiles+=("production")
        log_info "Including production services"
    fi
    
    export DOCKER_PROFILES="${profiles[*]}"
    log_success "Deployment profiles: ${DOCKER_PROFILES}"
}

# Validate configuration
validate_config() {
    log_info "Validating configuration..."
    
    # Check .env file
    if [ ! -f "$PROJECT_DIR/.env" ]; then
        log_warn "No .env file found, creating from template"
        if [ -f "$PROJECT_DIR/.env.template" ]; then
            cp "$PROJECT_DIR/.env.template" "$PROJECT_DIR/.env"
            log_success "Created .env from template"
        else
            log_error ".env.template not found"
            exit 1
        fi
    fi
    
    # Check required configuration directories
    local required_dirs=(".mcp" ".agents")
    for dir in "${required_dirs[@]}"; do
        if [ ! -d "$PROJECT_DIR/$dir" ]; then
            log_error "Required directory $dir not found"
            exit 1
        fi
    done
    
    # Validate MCP configuration
    if [ ! -f "$PROJECT_DIR/.mcp/discovery-config.yaml" ]; then
        log_error "MCP discovery configuration not found"
        exit 1
    fi
    
    # Validate agent configuration
    if [ ! -f "$PROJECT_DIR/.agents/discovery-config.yaml" ]; then
        log_error "Agent discovery configuration not found"
        exit 1
    fi
    
    log_success "Configuration validation passed"
}

# Deploy services
deploy_services() {
    log_info "Deploying PromptCraft hybrid stack..."
    
    cd "$PROJECT_DIR"
    
    # Build images if needed
    if [ "${FORCE_BUILD:-false}" = "true" ]; then
        log_info "Building Docker images..."
        docker-compose -f "$COMPOSE_FILE" build --no-cache
    fi
    
    # Convert profiles to Docker Compose format
    local profile_args=()
    for profile in $DOCKER_PROFILES; do
        if [ "$profile" != "base" ]; then
            profile_args+=("--profile" "$profile")
        fi
    done
    
    # Deploy with selected profiles
    log_info "Starting services with profiles: $DOCKER_PROFILES"
    docker-compose -f "$COMPOSE_FILE" "${profile_args[@]}" up -d
    
    log_success "Services deployed successfully"
}

# Health check
health_check() {
    log_info "Performing health checks..."
    
    local services=("promptcraft")
    
    if [ "${ZEN_MCP_EXTERNAL:-false}" = "false" ]; then
        services+=("zen-mcp")
    fi
    
    local max_wait=120  # 2 minutes
    local wait_interval=5
    local elapsed=0
    
    while [ $elapsed -lt $max_wait ]; do
        local all_healthy=true
        
        for service in "${services[@]}"; do
            if ! docker-compose -f "$COMPOSE_FILE" ps --filter "health=healthy" | grep -q "$service"; then
                all_healthy=false
                break
            fi
        done
        
        if [ "$all_healthy" = true ]; then
            log_success "All services are healthy"
            return 0
        fi
        
        log_info "Waiting for services to become healthy... (${elapsed}s/${max_wait}s)"
        sleep $wait_interval
        elapsed=$((elapsed + wait_interval))
    done
    
    log_error "Health check timeout"
    docker-compose -f "$COMPOSE_FILE" ps
    return 1
}

# Show deployment status
show_status() {
    log_info "Deployment Status:"
    echo
    
    # Service status
    docker-compose -f "$COMPOSE_FILE" ps
    echo
    
    # Service URLs
    log_info "Service URLs:"
    echo "  PromptCraft UI:    http://localhost:7860"
    echo "  PromptCraft API:   http://localhost:7862"
    
    if [ "${ZEN_MCP_EXTERNAL:-false}" = "false" ]; then
        echo "  Zen MCP Server:    http://localhost:8001"
    fi
    
    if [ "${QDRANT_EXTERNAL:-false}" = "false" ]; then
        echo "  Qdrant (local):    http://localhost:6334"
    fi
    
    if [[ "$DOCKER_PROFILES" == *"monitoring"* ]]; then
        echo "  Prometheus:        http://localhost:9090"
        echo "  Grafana:           http://localhost:3000 (admin:${GRAFANA_PASSWORD:-admin})"
    fi
    
    echo
    log_info "Configuration:"
    echo "  External Zen MCP:  ${ZEN_MCP_EXTERNAL:-false}"
    echo "  External Qdrant:   ${QDRANT_EXTERNAL:-false}"  
    echo "  External Redis:    ${REDIS_EXTERNAL:-false}"
    echo "  Profiles:          $DOCKER_PROFILES"
    echo
}

# Main execution
main() {
    log_info "Starting PromptCraft Hybrid Deployment"
    echo
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --build)
                export FORCE_BUILD=true
                shift
                ;;
            --monitoring)
                export ENABLE_MONITORING=true
                shift
                ;;
            --production)
                export ENVIRONMENT=production
                shift
                ;;
            --help)
                echo "Usage: $0 [options]"
                echo "Options:"
                echo "  --build        Force rebuild of Docker images"
                echo "  --monitoring   Enable monitoring stack (Prometheus/Grafana)"
                echo "  --production   Deploy in production mode"
                echo "  --help         Show this help message"
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    # Execute deployment steps
    check_prerequisites
    discover_services
    check_resources
    build_profiles
    validate_config
    deploy_services
    
    if health_check; then
        show_status
        log_success "PromptCraft deployed successfully!"
        echo
        log_info "To stop services: docker-compose -f $COMPOSE_FILE down"
        log_info "To view logs: docker-compose -f $COMPOSE_FILE logs -f"
    else
        log_error "Deployment failed health checks"
        docker-compose -f "$COMPOSE_FILE" logs
        exit 1
    fi
}

# Execute main function with all arguments
main "$@"