from sqlalchemy import Column, String, Integer, Boolean, JSON, DateTime
from sqlalchemy.sql import func

from app.core.database import Base


class Settings(Base):
    """
    Persistent application settings stored in the database.
    This model stores user-configurable settings that should persist across restarts.
    """
    __tablename__ = "settings"
    
    # Using a key-based approach for flexibility
    key = Column(String, primary_key=True, index=True)
    value = Column(JSON, nullable=False)
    
    # Metadata about the setting
    description = Column(String, nullable=True)
    category = Column(String, nullable=True)  # e.g., "email", "throttling", "monitoring"
    
    # Type hint for frontend validation
    value_type = Column(String, default="string")  # string, number, boolean, json
    
    # Default value (for reset functionality)
    default_value = Column(JSON, nullable=True)
    
    # Visibility and editability
    is_visible = Column(Boolean, default=True)  # Show in UI
    is_editable = Column(Boolean, default=True)  # Can be edited by users
    
    # Audit trail
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    updated_by = Column(String, nullable=True)  # Username or system
    
    # Versioning (for rollback capability)
    version = Column(Integer, default=1)
    previous_value = Column(JSON, nullable=True)
    
    @property
    def typed_value(self):
        """Get the value with proper type conversion based on value_type."""
        # First, get the actual value (might be encrypted)
        actual_value = self.get_decrypted_value()
        
        if self.value_type == "boolean":
            return bool(actual_value)
        elif self.value_type == "number":
            return int(actual_value) if isinstance(actual_value, (int, str)) else float(actual_value)
        elif self.value_type == "json":
            return actual_value if isinstance(actual_value, dict) else {}
        else:  # string
            return str(actual_value)
    
    def get_decrypted_value(self):
        """Get the decrypted value if this setting is encrypted."""
        # Import here to avoid circular imports
        from app.utils.encryption import encryption_service, should_encrypt_setting
        
        if should_encrypt_setting(self.key) and self.value:
            return encryption_service.decrypt(str(self.value))
        return self.value


# Predefined setting keys that match the config.py settings
SETTING_KEYS = {
    # Email settings
    "email.smtp_host": {
        "description": "SMTP server hostname",
        "category": "email",
        "value_type": "string",
        "default_value": "smtp.ctf.org"
    },
    "email.smtp_port": {
        "description": "SMTP server port",
        "category": "email",
        "value_type": "number",
        "default_value": 587
    },
    "email.smtp_user": {
        "description": "SMTP username for authentication",
        "category": "email",
        "value_type": "string",
        "default_value": None
    },
    "email.smtp_password": {
        "description": "SMTP password for authentication",
        "category": "email",
        "value_type": "string",
        "default_value": None,
        "is_visible": False  # Hide password in UI
    },
    "email.smtp_from": {
        "description": "From address for email notifications",
        "category": "email",
        "value_type": "string",
        "default_value": "noreply@ctf.org"
    },
    "email.smtp_tls": {
        "description": "Use TLS for SMTP connection",
        "category": "email",
        "value_type": "boolean",
        "default_value": True
    },
    
    # Throttling settings
    "throttling.default_max_concurrent": {
        "description": "Default maximum concurrent transfers",
        "category": "throttling",
        "value_type": "number",
        "default_value": 5
    },
    "throttling.check_interval": {
        "description": "Throttle check interval in seconds",
        "category": "throttling",
        "value_type": "number",
        "default_value": 1
    },
    
    # Event monitoring
    "monitoring.enable_event_monitoring": {
        "description": "Enable automatic event monitoring",
        "category": "monitoring",
        "value_type": "boolean",
        "default_value": True
    },
    "monitoring.event_poll_interval": {
        "description": "Event polling interval in seconds",
        "category": "monitoring",
        "value_type": "number",
        "default_value": 30
    },
    
    # AWS settings (for S3 events)
    "aws.region": {
        "description": "AWS region for S3 operations",
        "category": "aws",
        "value_type": "string",
        "default_value": "us-east-1"
    },
    "aws.access_key_id": {
        "description": "AWS Access Key ID",
        "category": "aws",
        "value_type": "string",
        "default_value": None
    },
    "aws.secret_access_key": {
        "description": "AWS Secret Access Key",
        "category": "aws",
        "value_type": "string",
        "default_value": None,
        "is_visible": False  # Hide secret in UI
    },
    "aws.sqs_queue_url": {
        "description": "SQS Queue URL for S3 events",
        "category": "aws",
        "value_type": "string",
        "default_value": None
    },
    
    # File watching
    "file_watch.directories": {
        "description": "Directories to watch for file changes",
        "category": "file_watch",
        "value_type": "json",  # Store as array
        "default_value": []
    },
    
    # General settings
    "general.project_name": {
        "description": "Project display name",
        "category": "general",
        "value_type": "string",
        "default_value": "CTF Rclone MVP"
    },
    "general.access_token_expire_minutes": {
        "description": "Access token expiration time in minutes",
        "category": "general",
        "value_type": "number",
        "default_value": 10080  # 7 days
    },
    "general.rclone_binary_path": {
        "description": "Path to rclone executable",
        "category": "general",
        "value_type": "string",
        "default_value": "/usr/local/bin/rclone"
    },
    "general.log_level": {
        "description": "Logging verbosity level",
        "category": "general",
        "value_type": "string",
        "default_value": "info"
    },
    "general.max_log_size_mb": {
        "description": "Maximum log file size before rotation",
        "category": "general",
        "value_type": "number",
        "default_value": 100
    },
    "general.log_retention_days": {
        "description": "Number of days to keep log files",
        "category": "general",
        "value_type": "number",
        "default_value": 30
    },
    "general.temp_directory": {
        "description": "Directory for temporary files during transfers",
        "category": "general",
        "value_type": "string",
        "default_value": "/tmp/file-orbit"
    },
    "general.enable_atomic_delivery": {
        "description": "Use temporary files and rename on completion",
        "category": "general",
        "value_type": "boolean",
        "default_value": True
    },
    
    # Performance/Throttling settings
    "throttling.default_bandwidth_limit": {
        "description": "Default bandwidth limit for transfers",
        "category": "throttling",
        "value_type": "string",
        "default_value": "100M"
    },
    "throttling.buffer_size_mb": {
        "description": "Transfer buffer size in megabytes",
        "category": "throttling",
        "value_type": "number",
        "default_value": 16
    },
    
    # Monitoring settings
    "monitoring.enable_prometheus_metrics": {
        "description": "Enable Prometheus metrics export",
        "category": "monitoring",
        "value_type": "boolean",
        "default_value": True
    },
    "monitoring.metrics_port": {
        "description": "Port for Prometheus metrics endpoint",
        "category": "monitoring",
        "value_type": "number",
        "default_value": 9090
    },
    "monitoring.webhook_url": {
        "description": "Webhook URL for notifications",
        "category": "monitoring",
        "value_type": "string",
        "default_value": ""
    },
    "monitoring.enable_webhook_notifications": {
        "description": "Enable webhook notifications",
        "category": "monitoring",
        "value_type": "boolean",
        "default_value": False
    },
    
    # Email settings
    "email.enable_notifications": {
        "description": "Enable email notifications",
        "category": "email",
        "value_type": "boolean",
        "default_value": True
    },
    
    # Security settings
    "security.enable_ldap": {
        "description": "Enable LDAP authentication",
        "category": "security",
        "value_type": "boolean",
        "default_value": False
    },
    "security.ldap_server": {
        "description": "LDAP server URL",
        "category": "security",
        "value_type": "string",
        "default_value": "ldap://ldap.ctf.org"
    },
    "security.ldap_base_dn": {
        "description": "LDAP base distinguished name",
        "category": "security",
        "value_type": "string",
        "default_value": "dc=ctf,dc=org"
    },
    "security.ldap_bind_dn": {
        "description": "LDAP bind distinguished name",
        "category": "security",
        "value_type": "string",
        "default_value": ""
    },
    "security.ldap_bind_password": {
        "description": "LDAP bind password",
        "category": "security",
        "value_type": "string",
        "default_value": "",
        "is_visible": False  # Hide password in UI
    },
    "security.api_key_expiry_days": {
        "description": "API key expiration in days",
        "category": "security",
        "value_type": "number",
        "default_value": 90
    },
    "security.enable_audit_logging": {
        "description": "Enable audit logging",
        "category": "security",
        "value_type": "boolean",
        "default_value": True
    },
    "security.compliance_mode": {
        "description": "Security compliance level",
        "category": "security",
        "value_type": "string",
        "default_value": "standard"
    }
}