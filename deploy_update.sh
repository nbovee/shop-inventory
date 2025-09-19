#!/bin/bash
set -e

# Shop Inventory Update Script
# Deploys changes to a running Raspberry Pi without full rebuild

# Configuration - will be set by get_connection_info() and load_config()
PI_HOST=""
PI_USER=""
APP_DIR=""
CONFIG_DIR=""
BACKUP_DIR="/tmp/shop-inventory-backup-$(date +%Y%m%d-%H%M%S)"

# SSH options for password authentication
SSH_OPTS="-o PasswordAuthentication=yes -o PreferredAuthentications=password -o ConnectTimeout=10"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

load_config() {
    if [ ! -f "config" ]; then
        log_error "Config file not found. Please create a config file first."
        exit 1
    fi
    
    log_info "Loading configuration from config file..."
    
    # Source the config file to get variables
    # shellcheck source=/dev/null
    . ./config
    
    # Set directory paths from config
    APP_DIR="$APP_INSTALL_DIR"
    CONFIG_DIR="$APP_ENV_DIR"
    
    log_info "App directory: $APP_DIR"
    log_info "Config directory: $CONFIG_DIR"
}

get_connection_info() {
    echo "Shop Inventory Deployment Script"
    echo "================================"
    echo
    
    # Get hostname/IP
    if [ -n "$1" ]; then
        PI_HOST="$1"
        log_info "Using provided hostname/IP: $PI_HOST"
    else
        read -r -p "Enter Pi hostname or IP address [default: 10.42.0.1]: " PI_HOST
        PI_HOST="${PI_HOST:-10.42.0.1}"
    fi
    
    # Get username
    if [ -n "$2" ]; then
        PI_USER="$2"
        log_info "Using provided username: $PI_USER"
    else
        read -r -p "Enter Pi username [default: user]: " PI_USER
        PI_USER="${PI_USER:-user}"
    fi
    
    log_info "Will connect to: $PI_USER@$PI_HOST"
    echo
}

setup_ssh_auth() {
    # Check if SSH key authentication works first
    if ssh -o ConnectTimeout=5 -o PasswordAuthentication=no "$PI_USER@$PI_HOST" 'echo "Key auth works"' > /dev/null 2>&1; then
        SSH_CMD="ssh"
        SCP_CMD="scp"
        RSYNC_CMD="rsync"
        log_info "Using SSH key authentication"
        return 0
    fi
    
    # Fall back to password authentication
    log_info "SSH key authentication failed, using password authentication"
    
    # Check if sshpass is available
    if ! command -v sshpass > /dev/null 2>&1; then
        log_error "sshpass is required for password authentication but not installed"
        log_info "Install with: sudo apt-get install sshpass (Ubuntu/Debian) or brew install hudochenkov/sshpass/sshpass (macOS)"
        exit 1
    fi
    
    # Prompt for password
    read -s -r -p "Enter password for $PI_USER@$PI_HOST: " PI_PASSWORD
    echo
    
    # Set up commands with sshpass (using environment variable for security)
    export SSHPASS="$PI_PASSWORD"
    SSH_CMD="sshpass -e ssh $SSH_OPTS"
    SCP_CMD="sshpass -e scp $SSH_OPTS"
    RSYNC_CMD="sshpass -e rsync -e 'ssh $SSH_OPTS'"
}

check_pi_connection() {
    log_info "Checking connection to Pi at $PI_HOST..."
    setup_ssh_auth
    
    if ! eval "$SSH_CMD '$PI_USER@$PI_HOST' 'echo \"Connected\"'" > /dev/null 2>&1; then
        log_error "Cannot connect to Pi at $PI_HOST"
        log_info "Usage: $0 [HOSTNAME_OR_IP] [USERNAME]"
        exit 1
    fi
    log_info "Connected to Pi successfully"
}

check_dependency_changes() {
    log_info "Checking for dependency changes..."
    
    # Check if uv is available, otherwise skip dependency check
    if ! command -v uv > /dev/null 2>&1; then
        log_warn "uv not available locally, skipping dependency change detection"
        log_info "Will use pre-built requirements.txt from stageCustom/00-shop/files/"
        return 1
    fi
    
    # Generate current requirements
    if ! uv pip compile -o /tmp/current_requirements.txt pyproject.toml > /dev/null 2>&1; then
        log_warn "Failed to compile current requirements with uv"
        log_info "Will use pre-built requirements.txt from stageCustom/00-shop/files/"
        return 1
    fi
    
    # Get remote requirements
    eval "$SSH_CMD '$PI_USER@$PI_HOST' 'cat $APP_DIR/requirements.txt'" > /tmp/remote_requirements.txt 2>/dev/null || {
        log_warn "Could not fetch remote requirements.txt"
        return 1
    }
    
    # Compare requirements (ignore comments and uv header)
    if ! diff -u <(grep -v '^#' /tmp/remote_requirements.txt | sort) \
                 <(grep -v '^#' /tmp/current_requirements.txt | sort) > /tmp/requirements_diff.txt; then
        log_warn "Dependencies have changed:"
        cat /tmp/requirements_diff.txt
        return 1
    fi
    
    log_info "Dependencies unchanged"
    return 0
}

create_local_backup() {
    log_info "Creating local backup before deployment..."
    
    # Create local backup directory
    LOCAL_BACKUP_DIR="./backups/$(date +%Y%m%d-%H%M%S)-pre-deploy"
    mkdir -p "$LOCAL_BACKUP_DIR"
    
    # Get the database path from Django settings
    DB_PATH=$(eval "$SSH_CMD '$PI_USER@$PI_HOST' '
        cd $APP_DIR
        source venv/bin/activate
        python -c \"import os; os.environ.setdefault(\\\"DJANGO_SETTINGS_MODULE\\\", \\\"_core.settings\\\"); from django.conf import settings; print(settings.DATABASES[\\\"default\\\"][\\\"NAME\\\"])\"
    '")
    
    if [ -z "$DB_PATH" ]; then
        log_warn "Could not determine database path, skipping database backup"
    else
        log_info "Downloading database from: $DB_PATH"
        # Download the database file
        eval "$SCP_CMD '$PI_USER@$PI_HOST:$DB_PATH' '$LOCAL_BACKUP_DIR/db.sqlite3'"
        log_info "Database backed up to: $LOCAL_BACKUP_DIR/db.sqlite3"
    fi
    
    # Download current application files for comparison/rollback
    log_info "Backing up current application files..."
    eval "$RSYNC_CMD -av '$PI_USER@$PI_HOST:$APP_DIR/' '$LOCAL_BACKUP_DIR/app/' \
        --exclude='venv/' \
        --exclude='staticfiles/' \
        --exclude='*.pyc' \
        --exclude='__pycache__/' \
        --exclude='logs/'"
    
    # Download current config
    eval "$SCP_CMD '$PI_USER@$PI_HOST:$CONFIG_DIR/config' '$LOCAL_BACKUP_DIR/config'"
    
    # Create backup metadata
    cat > "$LOCAL_BACKUP_DIR/backup_info.txt" << EOF
Backup created: $(date)
Pi host: $PI_HOST
Pi user: $PI_USER
App directory: $APP_DIR
Config directory: $CONFIG_DIR
Database path: $DB_PATH
Git commit: $(git rev-parse HEAD 2>/dev/null || echo "unknown")
Git branch: $(git branch --show-current 2>/dev/null || echo "unknown")
EOF
    
    log_info "Local backup completed: $LOCAL_BACKUP_DIR"
    echo
}

create_backup() {
    log_info "Creating backup on Pi..."
    eval "$SSH_CMD '$PI_USER@$PI_HOST' '
        sudo mkdir -p $BACKUP_DIR
        sudo cp -r $APP_DIR $BACKUP_DIR/app_backup
        sudo cp $CONFIG_DIR/config $BACKUP_DIR/config_backup
    '"
    log_info "Backup created at $BACKUP_DIR"
}

update_dependencies() {
    log_info "Updating Python dependencies..."
    
    # Check if requirements file exists locally
    if [ ! -f "stageCustom/00-shop/files/requirements.txt" ]; then
        log_error "requirements.txt not found in stageCustom/00-shop/files/"
        log_info "Run 'uv pip compile -o stageCustom/00-shop/files/requirements.txt pyproject.toml' first"
        exit 1
    fi
    
    # Copy new requirements
    eval "$SCP_CMD stageCustom/00-shop/files/requirements.txt '$PI_USER@$PI_HOST:/tmp/'"
    
    # Install new dependencies
    eval "$SSH_CMD '$PI_USER@$PI_HOST' '
        cd $APP_DIR
        sudo -u $APP_USER ./venv/bin/pip install -r /tmp/requirements.txt
        sudo cp /tmp/requirements.txt $APP_DIR/
    '"
}

update_application() {
    log_info "Updating application files..."
    
    # More efficient: sync directly from source without temp directory
    eval "$RSYNC_CMD -av --delete 'src/shop-inventory/' '$PI_USER@$PI_HOST:$APP_DIR/' \
        --exclude='db/' \
        --exclude='logs/' \
        --exclude='venv/' \
        --exclude='staticfiles/' \
        --exclude='*.pyc' \
        --exclude='__pycache__/' \
        --exclude='*.log'"
    
    # Set correct permissions
    eval "$SSH_CMD '$PI_USER@$PI_HOST' '
        sudo chown -R $APP_USER:$APP_GROUP $APP_DIR
        sudo chmod +x $APP_DIR/start.sh
        sudo chmod +x $APP_DIR/manage.py
    '"
}

update_config() {
    if [ ! -f "config" ]; then
        return 1
    fi
    
    # More efficient: compare checksums instead of copying file first
    LOCAL_CHECKSUM=$(md5sum config | cut -d' ' -f1)
    REMOTE_CHECKSUM=$(eval "$SSH_CMD '$PI_USER@$PI_HOST' 'md5sum $CONFIG_DIR/config 2>/dev/null | cut -d\" \" -f1'" 2>/dev/null || echo "")
    
    if [ "$LOCAL_CHECKSUM" != "$REMOTE_CHECKSUM" ]; then
        log_info "Updating configuration..."
        eval "$SCP_CMD config '$PI_USER@$PI_HOST:/tmp/config'"
        eval "$SSH_CMD '$PI_USER@$PI_HOST' 'sudo cp /tmp/config $CONFIG_DIR/config && sudo rm /tmp/config'"
        return 0
    fi
    
    log_info "Configuration unchanged"
    return 1
}

run_django_tasks() {
    log_info "Running Django management tasks..."
    eval "$SSH_CMD '$PI_USER@$PI_HOST' '
        cd $APP_DIR
        sudo -u $APP_USER ./venv/bin/python manage.py collectstatic --noinput
        sudo -u $APP_USER ./venv/bin/python manage.py migrate --noinput
    '"
}

restart_services() {
    log_info "Restarting services..."
    eval "$SSH_CMD '$PI_USER@$PI_HOST' '
        sudo systemctl restart $APP_NAME
        sudo systemctl restart nginx
    '"
    
    # Wait for services to come up
    sleep 3
    
    # Check service status
    if eval "$SSH_CMD '$PI_USER@$PI_HOST' 'sudo systemctl is-active $APP_NAME nginx'" | grep -q "inactive"; then
        log_error "Service restart failed"
        eval "$SSH_CMD '$PI_USER@$PI_HOST' 'sudo systemctl status $APP_NAME nginx'"
        return 1
    fi
    
    log_info "Services restarted successfully"
}

verify_deployment() {
    log_info "Verifying deployment..."
    
    # Test HTTP response
    if eval "$SSH_CMD '$PI_USER@$PI_HOST' 'curl -s -o /dev/null -w \"%{http_code}\" http://localhost'" | grep -q "200"; then
        log_info "Application is responding correctly"
    else
        log_error "Application health check failed"
        return 1
    fi
}

cleanup() {
    rm -f /tmp/current_requirements.txt /tmp/remote_requirements.txt /tmp/requirements_diff.txt
    # Clear password from environment
    unset SSHPASS
}

rollback_deployment() {
    log_warn "Rolling back deployment..."
    eval "$SSH_CMD '$PI_USER@$PI_HOST' '
        if [ -d \"$BACKUP_DIR/app_backup\" ]; then
            sudo systemctl stop $APP_NAME
            sudo rm -rf $APP_DIR
            sudo cp -r $BACKUP_DIR/app_backup $APP_DIR
            sudo chown -R $APP_USER:$APP_GROUP $APP_DIR
            sudo systemctl start $APP_NAME
            echo \"Application files rolled back\"
        fi
        
        if [ -f \"$BACKUP_DIR/config_backup\" ]; then
            sudo cp $BACKUP_DIR/config_backup $CONFIG_DIR/config
            echo \"Configuration rolled back\"
        fi
    '"
    log_info "Rollback completed. Check service status manually."
}

main() {
    trap cleanup EXIT
    
    # Get connection info and display header
    get_connection_info "$1" "$2"
    
    # Pre-flight checks
    if [ ! -d "src/shop-inventory" ]; then
        log_error "Must run from shop-inventory project root"
        exit 1
    fi
    
    # Check for required files
    if [ ! -f "stageCustom/00-shop/files/requirements.txt" ]; then
        log_warn "requirements.txt not found. Generating from pyproject.toml..."
        if command -v uv > /dev/null 2>&1; then
            uv pip compile -o stageCustom/00-shop/files/requirements.txt pyproject.toml
        else
            log_error "requirements.txt missing and uv not available to generate it"
            log_info "Either install uv or manually create stageCustom/00-shop/files/requirements.txt"
            exit 1
        fi
    fi
    
    # Load configuration to get proper directory paths
    load_config
    
    check_pi_connection
    
    # Create local backup before any changes
    create_local_backup
    
    # Check for dependency changes
    DEPS_CHANGED=false
    if ! check_dependency_changes; then
        read -p "Dependencies have changed. Continue with update? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Update cancelled"
            exit 0
        fi
        DEPS_CHANGED=true
    fi
    
    create_backup
    
    # Update dependencies if changed
    if [ "$DEPS_CHANGED" = true ]; then
        update_dependencies
    fi
    
    update_application
    
    # Check if config needs updating
    CONFIG_CHANGED=false
    if update_config; then
        CONFIG_CHANGED=true
    fi
    
    run_django_tasks
    
    # Restart services if dependencies or config changed
    if [ "$DEPS_CHANGED" = true ] || [ "$CONFIG_CHANGED" = true ]; then
        restart_services
    else
        # Just restart the app service for code changes
        log_info "Restarting application service..."
        eval "$SSH_CMD '$PI_USER@$PI_HOST' 'sudo systemctl restart $APP_NAME'"
    fi
    
    if ! verify_deployment; then
        log_error "Deployment verification failed!"
        read -p "Rollback to previous version? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rollback_deployment
            exit 1
        else
            log_warn "Deployment may be in unstable state. Check logs manually."
            log_info "Backup available at: $BACKUP_DIR"
            exit 1
        fi
    fi
    
    log_info "Deployment completed successfully!"
    log_info "Backup available at: $BACKUP_DIR"
}

main "$@"