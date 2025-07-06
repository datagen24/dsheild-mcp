#!/usr/bin/env python3
"""
User Configuration Management for DShield MCP
Extends the existing configuration system with user-customizable settings,
validation, and environment variable support.
"""

import os
import yaml
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from pathlib import Path
import structlog
from dotenv import load_dotenv

from .config_loader import get_config, ConfigError
from .op_secrets import OnePasswordSecrets

logger = structlog.get_logger(__name__)

# Load environment variables
load_dotenv()


@dataclass
class QuerySettings:
    """User-configurable query settings."""
    default_page_size: int = 100
    max_page_size: int = 1000
    default_timeout_seconds: int = 30
    max_timeout_seconds: int = 300
    enable_smart_optimization: bool = True
    fallback_strategy: str = "aggregate"  # aggregate, sample, error
    max_query_complexity: int = 1000


@dataclass
class PaginationSettings:
    """User-configurable pagination settings."""
    default_method: str = "page"  # page, cursor
    max_pages_per_request: int = 10
    cursor_timeout_seconds: int = 300
    enable_metadata: bool = True
    include_performance_metrics: bool = True


@dataclass
class StreamingSettings:
    """User-configurable streaming settings."""
    default_chunk_size: int = 50
    max_chunk_size: int = 200
    session_context_fields: List[str] = field(default_factory=lambda: [
        "source.ip", "user.name", "session.id"
    ])
    enable_session_summaries: bool = True
    session_timeout_minutes: int = 30


@dataclass
class PerformanceSettings:
    """User-configurable performance settings."""
    enable_caching: bool = True
    cache_ttl_seconds: int = 300
    max_cache_size: int = 1000
    enable_connection_pooling: bool = True
    connection_pool_size: int = 10
    request_timeout_seconds: int = 30


@dataclass
class SecuritySettings:
    """User-configurable security settings."""
    rate_limit_requests_per_minute: int = 60
    max_query_results: int = 1000
    enable_field_validation: bool = True
    allowed_field_patterns: List[str] = field(default_factory=lambda: [
        r"^[a-zA-Z_][a-zA-Z0-9_.]*$"
    ])
    block_sensitive_fields: bool = True
    sensitive_field_patterns: List[str] = field(default_factory=lambda: [
        r"password", r"secret", r"key", r"token"
    ])


@dataclass
class LoggingSettings:
    """User-configurable logging settings."""
    log_level: str = "INFO"
    log_format: str = "json"
    enable_query_logging: bool = True
    enable_performance_logging: bool = True
    log_sensitive_data: bool = False
    max_log_size_mb: int = 100


@dataclass
class CampaignSettings:
    """User-configurable campaign analysis settings."""
    correlation_window_minutes: int = 30
    min_confidence_threshold: float = 0.7
    max_campaign_events: int = 10000
    enable_geospatial_correlation: bool = True
    enable_infrastructure_correlation: bool = True
    enable_behavioral_correlation: bool = True
    enable_temporal_correlation: bool = True
    enable_ip_correlation: bool = True
    max_expansion_depth: int = 3
    expansion_timeout_seconds: int = 300


class UserConfigManager:
    """Manages user-configurable settings with validation and environment variable support."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path
        self.op_secrets = OnePasswordSecrets()
        
        # Load base configuration
        try:
            self.base_config = get_config(config_path)
        except ConfigError as e:
            logger.warning(f"Failed to load base config: {e}")
            self.base_config = {}
        
        # Initialize settings with defaults
        self.query_settings = QuerySettings()
        self.pagination_settings = PaginationSettings()
        self.streaming_settings = StreamingSettings()
        self.performance_settings = PerformanceSettings()
        self.security_settings = SecuritySettings()
        self.logging_settings = LoggingSettings()
        self.campaign_settings = CampaignSettings()
        
        # Load user configuration
        self._load_user_config()
        
    def _load_user_config(self):
        """Load user configuration from multiple sources with precedence."""
        # Priority order: environment variables > user config file > base config > defaults
        
        # Load from user config file
        user_config = self._load_user_config_file()
        
        # Apply environment variable overrides
        self._apply_env_overrides()
        
        # Apply user config file settings
        self._apply_user_config(user_config)
        
        # Validate all settings
        self._validate_settings()
        
    def _load_user_config_file(self) -> Dict[str, Any]:
        """Load user configuration from file."""
        user_config_paths = [
            Path("user_config.yaml"),
            Path("config/user_config.yaml"),
            Path.home() / ".dshield-mcp" / "user_config.yaml"
        ]
        
        for config_path in user_config_paths:
            if config_path.exists():
                try:
                    with open(config_path, 'r') as f:
                        config = yaml.safe_load(f)
                    logger.info(f"Loaded user config from: {config_path}")
                    return config or {}
                except Exception as e:
                    logger.warning(f"Failed to load user config from {config_path}: {e}")
        
        return {}
    
    def _apply_env_overrides(self):
        """Apply environment variable overrides to settings."""
        # Query Settings
        self.query_settings.default_page_size = int(os.getenv("DEFAULT_PAGE_SIZE", self.query_settings.default_page_size))
        self.query_settings.max_page_size = int(os.getenv("MAX_PAGE_SIZE", self.query_settings.max_page_size))
        self.query_settings.default_timeout_seconds = int(os.getenv("DEFAULT_TIMEOUT_SECONDS", self.query_settings.default_timeout_seconds))
        self.query_settings.max_timeout_seconds = int(os.getenv("MAX_TIMEOUT_SECONDS", self.query_settings.max_timeout_seconds))
        self.query_settings.enable_smart_optimization = os.getenv("ENABLE_SMART_OPTIMIZATION", str(self.query_settings.enable_smart_optimization)).lower() == "true"
        self.query_settings.fallback_strategy = os.getenv("FALLBACK_STRATEGY", self.query_settings.fallback_strategy)
        self.query_settings.max_query_complexity = int(os.getenv("MAX_QUERY_COMPLEXITY", self.query_settings.max_query_complexity))
        
        # Pagination Settings
        self.pagination_settings.default_method = os.getenv("PAGINATION_METHOD", self.pagination_settings.default_method)
        self.pagination_settings.max_pages_per_request = int(os.getenv("MAX_PAGES_PER_REQUEST", self.pagination_settings.max_pages_per_request))
        self.pagination_settings.cursor_timeout_seconds = int(os.getenv("CURSOR_TIMEOUT_SECONDS", self.pagination_settings.cursor_timeout_seconds))
        self.pagination_settings.enable_metadata = os.getenv("ENABLE_PAGINATION_METADATA", str(self.pagination_settings.enable_metadata)).lower() == "true"
        self.pagination_settings.include_performance_metrics = os.getenv("INCLUDE_PERFORMANCE_METRICS", str(self.pagination_settings.include_performance_metrics)).lower() == "true"
        
        # Streaming Settings
        self.streaming_settings.default_chunk_size = int(os.getenv("DEFAULT_CHUNK_SIZE", self.streaming_settings.default_chunk_size))
        self.streaming_settings.max_chunk_size = int(os.getenv("MAX_CHUNK_SIZE", self.streaming_settings.max_chunk_size))
        session_fields = os.getenv("SESSION_CONTEXT_FIELDS")
        if session_fields:
            self.streaming_settings.session_context_fields = [f.strip() for f in session_fields.split(",")]
        self.streaming_settings.enable_session_summaries = os.getenv("ENABLE_SESSION_SUMMARIES", str(self.streaming_settings.enable_session_summaries)).lower() == "true"
        self.streaming_settings.session_timeout_minutes = int(os.getenv("SESSION_TIMEOUT_MINUTES", self.streaming_settings.session_timeout_minutes))
        
        # Performance Settings
        self.performance_settings.enable_caching = os.getenv("ENABLE_CACHING", str(self.performance_settings.enable_caching)).lower() == "true"
        self.performance_settings.cache_ttl_seconds = int(os.getenv("CACHE_TTL_SECONDS", self.performance_settings.cache_ttl_seconds))
        self.performance_settings.max_cache_size = int(os.getenv("MAX_CACHE_SIZE", self.performance_settings.max_cache_size))
        self.performance_settings.enable_connection_pooling = os.getenv("ENABLE_CONNECTION_POOLING", str(self.performance_settings.enable_connection_pooling)).lower() == "true"
        self.performance_settings.connection_pool_size = int(os.getenv("CONNECTION_POOL_SIZE", self.performance_settings.connection_pool_size))
        self.performance_settings.request_timeout_seconds = int(os.getenv("REQUEST_TIMEOUT_SECONDS", self.performance_settings.request_timeout_seconds))
        
        # Security Settings
        self.security_settings.rate_limit_requests_per_minute = int(os.getenv("RATE_LIMIT_REQUESTS_PER_MINUTE", self.security_settings.rate_limit_requests_per_minute))
        self.security_settings.max_query_results = int(os.getenv("MAX_QUERY_RESULTS", self.security_settings.max_query_results))
        self.security_settings.enable_field_validation = os.getenv("ENABLE_FIELD_VALIDATION", str(self.security_settings.enable_field_validation)).lower() == "true"
        allowed_patterns = os.getenv("ALLOWED_FIELD_PATTERNS")
        if allowed_patterns:
            self.security_settings.allowed_field_patterns = [p.strip() for p in allowed_patterns.split(",")]
        self.security_settings.block_sensitive_fields = os.getenv("BLOCK_SENSITIVE_FIELDS", str(self.security_settings.block_sensitive_fields)).lower() == "true"
        sensitive_patterns = os.getenv("SENSITIVE_FIELD_PATTERNS")
        if sensitive_patterns:
            self.security_settings.sensitive_field_patterns = [p.strip() for p in sensitive_patterns.split(",")]
        
        # Logging Settings
        self.logging_settings.log_level = os.getenv("LOG_LEVEL", self.logging_settings.log_level)
        self.logging_settings.log_format = os.getenv("LOG_FORMAT", self.logging_settings.log_format)
        self.logging_settings.enable_query_logging = os.getenv("ENABLE_QUERY_LOGGING", str(self.logging_settings.enable_query_logging)).lower() == "true"
        self.logging_settings.enable_performance_logging = os.getenv("ENABLE_PERFORMANCE_LOGGING", str(self.logging_settings.enable_performance_logging)).lower() == "true"
        self.logging_settings.log_sensitive_data = os.getenv("LOG_SENSITIVE_DATA", str(self.logging_settings.log_sensitive_data)).lower() == "true"
        self.logging_settings.max_log_size_mb = int(os.getenv("MAX_LOG_SIZE_MB", self.logging_settings.max_log_size_mb))
        
        # Campaign Settings
        self.campaign_settings.correlation_window_minutes = int(os.getenv("CORRELATION_WINDOW_MINUTES", self.campaign_settings.correlation_window_minutes))
        self.campaign_settings.min_confidence_threshold = float(os.getenv("MIN_CONFIDENCE_THRESHOLD", self.campaign_settings.min_confidence_threshold))
        self.campaign_settings.max_campaign_events = int(os.getenv("MAX_CAMPAIGN_EVENTS", self.campaign_settings.max_campaign_events))
        self.campaign_settings.enable_geospatial_correlation = os.getenv("ENABLE_GEOSPATIAL_CORRELATION", str(self.campaign_settings.enable_geospatial_correlation)).lower() == "true"
        self.campaign_settings.enable_infrastructure_correlation = os.getenv("ENABLE_INFRASTRUCTURE_CORRELATION", str(self.campaign_settings.enable_infrastructure_correlation)).lower() == "true"
        self.campaign_settings.enable_behavioral_correlation = os.getenv("ENABLE_BEHAVIORAL_CORRELATION", str(self.campaign_settings.enable_behavioral_correlation)).lower() == "true"
        self.campaign_settings.enable_temporal_correlation = os.getenv("ENABLE_TEMPORAL_CORRELATION", str(self.campaign_settings.enable_temporal_correlation)).lower() == "true"
        self.campaign_settings.enable_ip_correlation = os.getenv("ENABLE_IP_CORRELATION", str(self.campaign_settings.enable_ip_correlation)).lower() == "true"
        self.campaign_settings.max_expansion_depth = int(os.getenv("MAX_EXPANSION_DEPTH", self.campaign_settings.max_expansion_depth))
        self.campaign_settings.expansion_timeout_seconds = int(os.getenv("EXPANSION_TIMEOUT_SECONDS", self.campaign_settings.expansion_timeout_seconds))
    
    def _apply_user_config(self, user_config: Dict[str, Any]):
        """Apply user configuration file settings."""
        # Query Settings
        if "query" in user_config:
            query_config = user_config["query"]
            self.query_settings.default_page_size = query_config.get("default_page_size", self.query_settings.default_page_size)
            self.query_settings.max_page_size = query_config.get("max_page_size", self.query_settings.max_page_size)
            self.query_settings.default_timeout_seconds = query_config.get("default_timeout_seconds", self.query_settings.default_timeout_seconds)
            self.query_settings.max_timeout_seconds = query_config.get("max_timeout_seconds", self.query_settings.max_timeout_seconds)
            self.query_settings.enable_smart_optimization = query_config.get("enable_smart_optimization", self.query_settings.enable_smart_optimization)
            self.query_settings.fallback_strategy = query_config.get("fallback_strategy", self.query_settings.fallback_strategy)
            self.query_settings.max_query_complexity = query_config.get("max_query_complexity", self.query_settings.max_query_complexity)
        
        # Pagination Settings
        if "pagination" in user_config:
            pagination_config = user_config["pagination"]
            self.pagination_settings.default_method = pagination_config.get("default_method", self.pagination_settings.default_method)
            self.pagination_settings.max_pages_per_request = pagination_config.get("max_pages_per_request", self.pagination_settings.max_pages_per_request)
            self.pagination_settings.cursor_timeout_seconds = pagination_config.get("cursor_timeout_seconds", self.pagination_settings.cursor_timeout_seconds)
            self.pagination_settings.enable_metadata = pagination_config.get("enable_metadata", self.pagination_settings.enable_metadata)
            self.pagination_settings.include_performance_metrics = pagination_config.get("include_performance_metrics", self.pagination_settings.include_performance_metrics)
        
        # Streaming Settings
        if "streaming" in user_config:
            streaming_config = user_config["streaming"]
            self.streaming_settings.default_chunk_size = streaming_config.get("default_chunk_size", self.streaming_settings.default_chunk_size)
            self.streaming_settings.max_chunk_size = streaming_config.get("max_chunk_size", self.streaming_settings.max_chunk_size)
            if "session_context_fields" in streaming_config:
                self.streaming_settings.session_context_fields = streaming_config["session_context_fields"]
            self.streaming_settings.enable_session_summaries = streaming_config.get("enable_session_summaries", self.streaming_settings.enable_session_summaries)
            self.streaming_settings.session_timeout_minutes = streaming_config.get("session_timeout_minutes", self.streaming_settings.session_timeout_minutes)
        
        # Performance Settings
        if "performance" in user_config:
            performance_config = user_config["performance"]
            self.performance_settings.enable_caching = performance_config.get("enable_caching", self.performance_settings.enable_caching)
            self.performance_settings.cache_ttl_seconds = performance_config.get("cache_ttl_seconds", self.performance_settings.cache_ttl_seconds)
            self.performance_settings.max_cache_size = performance_config.get("max_cache_size", self.performance_settings.max_cache_size)
            self.performance_settings.enable_connection_pooling = performance_config.get("enable_connection_pooling", self.performance_settings.enable_connection_pooling)
            self.performance_settings.connection_pool_size = performance_config.get("connection_pool_size", self.performance_settings.connection_pool_size)
            self.performance_settings.request_timeout_seconds = performance_config.get("request_timeout_seconds", self.performance_settings.request_timeout_seconds)
        
        # Security Settings
        if "security" in user_config:
            security_config = user_config["security"]
            self.security_settings.rate_limit_requests_per_minute = security_config.get("rate_limit_requests_per_minute", self.security_settings.rate_limit_requests_per_minute)
            self.security_settings.max_query_results = security_config.get("max_query_results", self.security_settings.max_query_results)
            self.security_settings.enable_field_validation = security_config.get("enable_field_validation", self.security_settings.enable_field_validation)
            if "allowed_field_patterns" in security_config:
                self.security_settings.allowed_field_patterns = security_config["allowed_field_patterns"]
            self.security_settings.block_sensitive_fields = security_config.get("block_sensitive_fields", self.security_settings.block_sensitive_fields)
            if "sensitive_field_patterns" in security_config:
                self.security_settings.sensitive_field_patterns = security_config["sensitive_field_patterns"]
        
        # Logging Settings
        if "logging" in user_config:
            logging_config = user_config["logging"]
            self.logging_settings.log_level = logging_config.get("log_level", self.logging_settings.log_level)
            self.logging_settings.log_format = logging_config.get("log_format", self.logging_settings.log_format)
            self.logging_settings.enable_query_logging = logging_config.get("enable_query_logging", self.logging_settings.enable_query_logging)
            self.logging_settings.enable_performance_logging = logging_config.get("enable_performance_logging", self.logging_settings.enable_performance_logging)
            self.logging_settings.log_sensitive_data = logging_config.get("log_sensitive_data", self.logging_settings.log_sensitive_data)
            self.logging_settings.max_log_size_mb = logging_config.get("max_log_size_mb", self.logging_settings.max_log_size_mb)
        
        # Campaign Settings
        if "campaign" in user_config:
            campaign_config = user_config["campaign"]
            self.campaign_settings.correlation_window_minutes = campaign_config.get("correlation_window_minutes", self.campaign_settings.correlation_window_minutes)
            self.campaign_settings.min_confidence_threshold = campaign_config.get("min_confidence_threshold", self.campaign_settings.min_confidence_threshold)
            self.campaign_settings.max_campaign_events = campaign_config.get("max_campaign_events", self.campaign_settings.max_campaign_events)
            self.campaign_settings.enable_geospatial_correlation = campaign_config.get("enable_geospatial_correlation", self.campaign_settings.enable_geospatial_correlation)
            self.campaign_settings.enable_infrastructure_correlation = campaign_config.get("enable_infrastructure_correlation", self.campaign_settings.enable_infrastructure_correlation)
            self.campaign_settings.enable_behavioral_correlation = campaign_config.get("enable_behavioral_correlation", self.campaign_settings.enable_behavioral_correlation)
            self.campaign_settings.enable_temporal_correlation = campaign_config.get("enable_temporal_correlation", self.campaign_settings.enable_temporal_correlation)
            self.campaign_settings.enable_ip_correlation = campaign_config.get("enable_ip_correlation", self.campaign_settings.enable_ip_correlation)
            self.campaign_settings.max_expansion_depth = campaign_config.get("max_expansion_depth", self.campaign_settings.max_expansion_depth)
            self.campaign_settings.expansion_timeout_seconds = campaign_config.get("expansion_timeout_seconds", self.campaign_settings.expansion_timeout_seconds)
    
    def _validate_settings(self):
        """Validate all settings and log warnings for invalid values."""
        errors = []
        warnings = []
        
        # Query Settings Validation
        if self.query_settings.default_page_size > self.query_settings.max_page_size:
            errors.append("default_page_size cannot be greater than max_page_size")
        if self.query_settings.default_timeout_seconds > self.query_settings.max_timeout_seconds:
            errors.append("default_timeout_seconds cannot be greater than max_timeout_seconds")
        if self.query_settings.fallback_strategy not in ["aggregate", "sample", "error"]:
            errors.append("fallback_strategy must be one of: aggregate, sample, error")
        
        # Pagination Settings Validation
        if self.pagination_settings.default_method not in ["page", "cursor"]:
            errors.append("pagination_method must be one of: page, cursor")
        if self.pagination_settings.max_pages_per_request <= 0:
            errors.append("max_pages_per_request must be positive")
        
        # Streaming Settings Validation
        if self.streaming_settings.default_chunk_size > self.streaming_settings.max_chunk_size:
            errors.append("default_chunk_size cannot be greater than max_chunk_size")
        if self.streaming_settings.session_timeout_minutes <= 0:
            errors.append("session_timeout_minutes must be positive")
        
        # Performance Settings Validation
        if self.performance_settings.cache_ttl_seconds <= 0:
            errors.append("cache_ttl_seconds must be positive")
        if self.performance_settings.max_cache_size <= 0:
            errors.append("max_cache_size must be positive")
        if self.performance_settings.connection_pool_size <= 0:
            errors.append("connection_pool_size must be positive")
        
        # Security Settings Validation
        if self.security_settings.rate_limit_requests_per_minute <= 0:
            errors.append("rate_limit_requests_per_minute must be positive")
        if self.security_settings.max_query_results <= 0:
            errors.append("max_query_results must be positive")
        
        # Logging Settings Validation
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.logging_settings.log_level.upper() not in valid_log_levels:
            errors.append(f"log_level must be one of: {', '.join(valid_log_levels)}")
        if self.logging_settings.log_format not in ["json", "text"]:
            errors.append("log_format must be one of: json, text")
        if self.logging_settings.max_log_size_mb <= 0:
            errors.append("max_log_size_mb must be positive")
        
        # Campaign Settings Validation
        if self.campaign_settings.correlation_window_minutes <= 0:
            errors.append("correlation_window_minutes must be positive")
        if not 0.0 <= self.campaign_settings.min_confidence_threshold <= 1.0:
            errors.append("min_confidence_threshold must be between 0.0 and 1.0")
        if self.campaign_settings.max_campaign_events <= 0:
            errors.append("max_campaign_events must be positive")
        if self.campaign_settings.max_expansion_depth <= 0:
            errors.append("max_expansion_depth must be positive")
        if self.campaign_settings.expansion_timeout_seconds <= 0:
            errors.append("expansion_timeout_seconds must be positive")
        
        # Log errors and warnings
        if errors:
            raise ValueError(f"Configuration validation errors: {'; '.join(errors)}")
        
        if warnings:
            for warning in warnings:
                logger.warning(warning)
    
    def get_setting(self, category: str, setting: str) -> Any:
        """Get a specific setting value."""
        settings_map = {
            "query": self.query_settings,
            "pagination": self.pagination_settings,
            "streaming": self.streaming_settings,
            "performance": self.performance_settings,
            "security": self.security_settings,
            "logging": self.logging_settings,
            "campaign": self.campaign_settings
        }
        
        if category not in settings_map:
            raise ValueError(f"Unknown category: {category}")
        
        settings_obj = settings_map[category]
        if not hasattr(settings_obj, setting):
            raise ValueError(f"Unknown setting: {category}.{setting}")
        
        return getattr(settings_obj, setting)
    
    def update_setting(self, category: str, setting: str, value: Any):
        """Update a specific setting value."""
        settings_map = {
            "query": self.query_settings,
            "pagination": self.pagination_settings,
            "streaming": self.streaming_settings,
            "performance": self.performance_settings,
            "security": self.security_settings,
            "logging": self.logging_settings,
            "campaign": self.campaign_settings
        }
        
        if category not in settings_map:
            raise ValueError(f"Unknown category: {category}")
        
        settings_obj = settings_map[category]
        if not hasattr(settings_obj, setting):
            raise ValueError(f"Unknown setting: {category}.{setting}")
        
        setattr(settings_obj, setting, value)
        self._validate_settings()
        logger.info(f"Updated setting: {category}.{setting} = {value}")
    
    def export_config(self) -> Dict[str, Any]:
        """Export current configuration as a dictionary."""
        return {
            "query": {
                "default_page_size": self.query_settings.default_page_size,
                "max_page_size": self.query_settings.max_page_size,
                "default_timeout_seconds": self.query_settings.default_timeout_seconds,
                "max_timeout_seconds": self.query_settings.max_timeout_seconds,
                "enable_smart_optimization": self.query_settings.enable_smart_optimization,
                "fallback_strategy": self.query_settings.fallback_strategy,
                "max_query_complexity": self.query_settings.max_query_complexity
            },
            "pagination": {
                "default_method": self.pagination_settings.default_method,
                "max_pages_per_request": self.pagination_settings.max_pages_per_request,
                "cursor_timeout_seconds": self.pagination_settings.cursor_timeout_seconds,
                "enable_metadata": self.pagination_settings.enable_metadata,
                "include_performance_metrics": self.pagination_settings.include_performance_metrics
            },
            "streaming": {
                "default_chunk_size": self.streaming_settings.default_chunk_size,
                "max_chunk_size": self.streaming_settings.max_chunk_size,
                "session_context_fields": self.streaming_settings.session_context_fields,
                "enable_session_summaries": self.streaming_settings.enable_session_summaries,
                "session_timeout_minutes": self.streaming_settings.session_timeout_minutes
            },
            "performance": {
                "enable_caching": self.performance_settings.enable_caching,
                "cache_ttl_seconds": self.performance_settings.cache_ttl_seconds,
                "max_cache_size": self.performance_settings.max_cache_size,
                "enable_connection_pooling": self.performance_settings.enable_connection_pooling,
                "connection_pool_size": self.performance_settings.connection_pool_size,
                "request_timeout_seconds": self.performance_settings.request_timeout_seconds
            },
            "security": {
                "rate_limit_requests_per_minute": self.security_settings.rate_limit_requests_per_minute,
                "max_query_results": self.security_settings.max_query_results,
                "enable_field_validation": self.security_settings.enable_field_validation,
                "allowed_field_patterns": self.security_settings.allowed_field_patterns,
                "block_sensitive_fields": self.security_settings.block_sensitive_fields,
                "sensitive_field_patterns": self.security_settings.sensitive_field_patterns
            },
            "logging": {
                "log_level": self.logging_settings.log_level,
                "log_format": self.logging_settings.log_format,
                "enable_query_logging": self.logging_settings.enable_query_logging,
                "enable_performance_logging": self.logging_settings.enable_performance_logging,
                "log_sensitive_data": self.logging_settings.log_sensitive_data,
                "max_log_size_mb": self.logging_settings.max_log_size_mb
            },
            "campaign": {
                "correlation_window_minutes": self.campaign_settings.correlation_window_minutes,
                "min_confidence_threshold": self.campaign_settings.min_confidence_threshold,
                "max_campaign_events": self.campaign_settings.max_campaign_events,
                "enable_geospatial_correlation": self.campaign_settings.enable_geospatial_correlation,
                "enable_infrastructure_correlation": self.campaign_settings.enable_infrastructure_correlation,
                "enable_behavioral_correlation": self.campaign_settings.enable_behavioral_correlation,
                "enable_temporal_correlation": self.campaign_settings.enable_temporal_correlation,
                "enable_ip_correlation": self.campaign_settings.enable_ip_correlation,
                "max_expansion_depth": self.campaign_settings.max_expansion_depth,
                "expansion_timeout_seconds": self.campaign_settings.expansion_timeout_seconds
            }
        }
    
    def save_user_config(self, file_path: Optional[str] = None):
        """Save current configuration to a user config file."""
        if file_path is None:
            config_dir = Path.home() / ".dshield-mcp"
            config_dir.mkdir(exist_ok=True)
            file_path = config_dir / "user_config.yaml"
        
        config_data = self.export_config()
        
        try:
            with open(file_path, 'w') as f:
                yaml.dump(config_data, f, default_flow_style=False, indent=2)
            logger.info(f"Saved user configuration to: {file_path}")
        except Exception as e:
            logger.error(f"Failed to save user configuration: {e}")
            raise
    
    def get_environment_variables(self) -> Dict[str, str]:
        """Get environment variable names and their current values."""
        return {
            # Query Settings
            "DEFAULT_PAGE_SIZE": str(self.query_settings.default_page_size),
            "MAX_PAGE_SIZE": str(self.query_settings.max_page_size),
            "DEFAULT_TIMEOUT_SECONDS": str(self.query_settings.default_timeout_seconds),
            "MAX_TIMEOUT_SECONDS": str(self.query_settings.max_timeout_seconds),
            "ENABLE_SMART_OPTIMIZATION": str(self.query_settings.enable_smart_optimization),
            "FALLBACK_STRATEGY": self.query_settings.fallback_strategy,
            "MAX_QUERY_COMPLEXITY": str(self.query_settings.max_query_complexity),
            
            # Pagination Settings
            "PAGINATION_METHOD": self.pagination_settings.default_method,
            "MAX_PAGES_PER_REQUEST": str(self.pagination_settings.max_pages_per_request),
            "CURSOR_TIMEOUT_SECONDS": str(self.pagination_settings.cursor_timeout_seconds),
            "ENABLE_PAGINATION_METADATA": str(self.pagination_settings.enable_metadata),
            "INCLUDE_PERFORMANCE_METRICS": str(self.pagination_settings.include_performance_metrics),
            
            # Streaming Settings
            "DEFAULT_CHUNK_SIZE": str(self.streaming_settings.default_chunk_size),
            "MAX_CHUNK_SIZE": str(self.streaming_settings.max_chunk_size),
            "SESSION_CONTEXT_FIELDS": ",".join(self.streaming_settings.session_context_fields),
            "ENABLE_SESSION_SUMMARIES": str(self.streaming_settings.enable_session_summaries),
            "SESSION_TIMEOUT_MINUTES": str(self.streaming_settings.session_timeout_minutes),
            
            # Performance Settings
            "ENABLE_CACHING": str(self.performance_settings.enable_caching),
            "CACHE_TTL_SECONDS": str(self.performance_settings.cache_ttl_seconds),
            "MAX_CACHE_SIZE": str(self.performance_settings.max_cache_size),
            "ENABLE_CONNECTION_POOLING": str(self.performance_settings.enable_connection_pooling),
            "CONNECTION_POOL_SIZE": str(self.performance_settings.connection_pool_size),
            "REQUEST_TIMEOUT_SECONDS": str(self.performance_settings.request_timeout_seconds),
            
            # Security Settings
            "RATE_LIMIT_REQUESTS_PER_MINUTE": str(self.security_settings.rate_limit_requests_per_minute),
            "MAX_QUERY_RESULTS": str(self.security_settings.max_query_results),
            "ENABLE_FIELD_VALIDATION": str(self.security_settings.enable_field_validation),
            "ALLOWED_FIELD_PATTERNS": ",".join(self.security_settings.allowed_field_patterns),
            "BLOCK_SENSITIVE_FIELDS": str(self.security_settings.block_sensitive_fields),
            "SENSITIVE_FIELD_PATTERNS": ",".join(self.security_settings.sensitive_field_patterns),
            
            # Logging Settings
            "LOG_LEVEL": self.logging_settings.log_level,
            "LOG_FORMAT": self.logging_settings.log_format,
            "ENABLE_QUERY_LOGGING": str(self.logging_settings.enable_query_logging),
            "ENABLE_PERFORMANCE_LOGGING": str(self.logging_settings.enable_performance_logging),
            "LOG_SENSITIVE_DATA": str(self.logging_settings.log_sensitive_data),
            "MAX_LOG_SIZE_MB": str(self.logging_settings.max_log_size_mb),
            
            # Campaign Settings
            "CORRELATION_WINDOW_MINUTES": str(self.campaign_settings.correlation_window_minutes),
            "MIN_CONFIDENCE_THRESHOLD": str(self.campaign_settings.min_confidence_threshold),
            "MAX_CAMPAIGN_EVENTS": str(self.campaign_settings.max_campaign_events),
            "ENABLE_GEOSPATIAL_CORRELATION": str(self.campaign_settings.enable_geospatial_correlation),
            "ENABLE_INFRASTRUCTURE_CORRELATION": str(self.campaign_settings.enable_infrastructure_correlation),
            "ENABLE_BEHAVIORAL_CORRELATION": str(self.campaign_settings.enable_behavioral_correlation),
            "ENABLE_TEMPORAL_CORRELATION": str(self.campaign_settings.enable_temporal_correlation),
            "ENABLE_IP_CORRELATION": str(self.campaign_settings.enable_ip_correlation),
            "MAX_EXPANSION_DEPTH": str(self.campaign_settings.max_expansion_depth),
            "EXPANSION_TIMEOUT_SECONDS": str(self.campaign_settings.expansion_timeout_seconds)
        }


# Global instance for easy access
_user_config_manager: Optional[UserConfigManager] = None


def get_user_config() -> UserConfigManager:
    """Get the global user configuration manager instance."""
    global _user_config_manager
    if _user_config_manager is None:
        _user_config_manager = UserConfigManager()
    return _user_config_manager


def reset_user_config():
    """Reset the global user configuration manager instance."""
    global _user_config_manager
    _user_config_manager = None 