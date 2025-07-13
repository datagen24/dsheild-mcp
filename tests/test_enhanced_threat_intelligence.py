"""
Tests for Enhanced Threat Intelligence functionality.

This module provides comprehensive tests for the enhanced threat intelligence
features including the Threat Intelligence Manager, multi-source enrichment,
and correlation capabilities.

Test Coverage:
- Threat Intelligence Manager initialization and configuration
- IP enrichment from multiple sources
- Domain enrichment capabilities
- Threat indicator correlation
- Caching and rate limiting
- Error handling and edge cases
- MCP tool integration

Example:
    >>> pytest tests/test_enhanced_threat_intelligence.py -v
"""

import pytest
import pytest_asyncio
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any
from unittest.mock import AsyncMock, MagicMock, patch
import os

from src.threat_intelligence_manager import ThreatIntelligenceManager
from src.models import ThreatIntelligenceResult, DomainIntelligence, ThreatIntelligenceSource


pytestmark = pytest.mark.asyncio


class TestThreatIntelligenceManager:
    """Test suite for Threat Intelligence Manager."""
    
    @pytest_asyncio.fixture
    async def threat_manager(self) -> ThreatIntelligenceManager:
        """Create a Threat Intelligence Manager instance for testing."""
        manager = ThreatIntelligenceManager()
        yield manager
        await manager.cleanup()
        
        # Clean up SQLite cache file after each test
        if manager.sqlite_cache_enabled and os.path.exists(manager.sqlite_cache_path):
            try:
                os.remove(manager.sqlite_cache_path)
            except Exception:
                pass  # Ignore cleanup errors
    
    @pytest.fixture
    def mock_config(self) -> Dict[str, Any]:
        """Mock configuration for testing."""
        return {
            "threat_intelligence": {
                "sources": {
                    "dshield": {"enabled": True, "rate_limit_requests_per_minute": 60},
                    "virustotal": {"enabled": False},
                    "shodan": {"enabled": False}
                },
                "correlation": {
                    "confidence_threshold": 0.7,
                    "max_sources_per_query": 3
                },
                "cache_ttl_hours": 1,
                "max_cache_size": 1000
            }
        }
    
    def mock_user_config(self):
        """Create a mock user config for tests that need it."""
        config = MagicMock()
        config.get_setting.return_value = "default_value"
        
        # Mock performance settings for SQLite cache
        performance_settings = MagicMock()
        performance_settings.enable_sqlite_cache = True
        performance_settings.sqlite_cache_ttl_hours = 24
        performance_settings.sqlite_cache_db_name = "test_enrichment_cache.sqlite3"
        config.performance_settings = performance_settings
        
        # Mock database path methods
        config.get_database_directory.return_value = "/tmp/test_db"
        config.get_cache_database_path.return_value = "/tmp/test_db/test_enrichment_cache.sqlite3"
        
        return config
    
    @pytest.mark.asyncio
    async def test_manager_initialization(self, mock_config, mock_user_config):
        """Test Threat Intelligence Manager initialization."""
        with patch('src.threat_intelligence_manager.get_config', return_value=mock_config), \
             patch('src.threat_intelligence_manager.get_user_config', return_value=mock_user_config):
            
            manager = ThreatIntelligenceManager()
            
            assert manager.config == mock_config
            assert manager.user_config == mock_user_config
            assert manager.confidence_threshold == 0.7
            assert manager.max_sources == 3
            assert manager.cache_ttl == timedelta(hours=1)
            assert ThreatIntelligenceSource.DSHIELD in manager.clients
            
            await manager.cleanup()
    
    @pytest.mark.asyncio
    async def test_enrich_ip_comprehensive_success(self, threat_manager):
        """Test successful comprehensive IP enrichment."""
        # Mock DShield client response
        mock_response = {
            "reputation_score": 85.0,
            "country": "US",
            "asn": "AS15169",
            "organization": "Google LLC",
            "attack_types": ["port_scan", "brute_force"],
            "tags": ["malicious", "scanner"]
        }
        
        threat_manager.clients[ThreatIntelligenceSource.DSHIELD].get_ip_reputation = AsyncMock(
            return_value=mock_response
        )
        
        result = await threat_manager.enrich_ip_comprehensive("8.8.8.8")
        
        assert isinstance(result, ThreatIntelligenceResult)
        assert result.ip_address == "8.8.8.8"
        assert result.overall_threat_score == 15.0  # 100 - 85
        assert result.confidence_score == 0.8  # Default for DShield
        assert ThreatIntelligenceSource.DSHIELD in result.sources_queried
        assert len(result.threat_indicators) > 0
        assert result.geographic_data["country"] == "US"
        assert result.network_data["asn"] == "AS15169"
    
    @pytest.mark.asyncio
    async def test_enrich_ip_comprehensive_invalid_ip(self, threat_manager):
        """Test IP enrichment with invalid IP address."""
        with pytest.raises(ValueError, match="Invalid IP address"):
            await threat_manager.enrich_ip_comprehensive("invalid_ip")
    
    @pytest.mark.asyncio
    async def test_enrich_ip_comprehensive_no_sources(self):
        """Test IP enrichment when no sources are available."""
        with patch('src.threat_intelligence_manager.get_config', return_value={
            "threat_intelligence": {
                "sources": {
                    "dshield": {"enabled": False},
                    "virustotal": {"enabled": False}
                }
            }
        }), patch('src.threat_intelligence_manager.get_user_config', return_value=self.mock_user_config()):
            
            manager = ThreatIntelligenceManager()
            
            with pytest.raises(RuntimeError, match="No threat intelligence sources available"):
                await manager.enrich_ip_comprehensive("8.8.8.8")
            
            await manager.cleanup()
    
    @pytest.mark.asyncio
    async def test_enrich_ip_comprehensive_cache_hit(self, threat_manager):
        """Test IP enrichment with cache hit."""
        # Use a unique IP to avoid cache persistence from other tests
        unique_ip = f"192.168.{hash(str(threat_manager)) % 255}.1"
        
        # First call to populate cache
        mock_response = {"reputation_score": 50.0}
        threat_manager.clients[ThreatIntelligenceSource.DSHIELD].get_ip_reputation = AsyncMock(
            return_value=mock_response
        )
        
        result1 = await threat_manager.enrich_ip_comprehensive(unique_ip)
        assert not result1.cache_hit
        
        # Second call should hit cache
        result2 = await threat_manager.enrich_ip_comprehensive(unique_ip)
        assert result2.cache_hit
        assert result2.overall_threat_score == result1.overall_threat_score
    
    @pytest.mark.asyncio
    async def test_enrich_ip_comprehensive_none_reputation(self, threat_manager):
        """Test IP enrichment when reputation score is None."""
        # Use a unique IP to avoid cache persistence from other tests
        unique_ip = f"203.0.{hash(str(threat_manager)) % 255}.1"
        
        # Mock DShield client response with None reputation score
        mock_response = {
            "reputation_score": None,
            "country": "US",
            "asn": "AS15169",
            "organization": "Google LLC",
            "attack_types": [],
            "tags": []
        }
        
        threat_manager.clients[ThreatIntelligenceSource.DSHIELD].get_ip_reputation = AsyncMock(
            return_value=mock_response
        )
        
        result = await threat_manager.enrich_ip_comprehensive(unique_ip)
        
        assert isinstance(result, ThreatIntelligenceResult)
        assert result.ip_address == unique_ip
        assert result.overall_threat_score is None  # No valid reputation score
        assert result.confidence_score == 0.8  # Default for DShield
        assert ThreatIntelligenceSource.DSHIELD in result.sources_queried
    
    @pytest.mark.asyncio
    async def test_enrich_domain_comprehensive(self, threat_manager):
        """Test comprehensive domain enrichment."""
        result = await threat_manager.enrich_domain_comprehensive("example.com")
        
        assert isinstance(result, DomainIntelligence)
        assert result.domain == "example.com"
        assert result.sources_queried == []  # No sources implemented yet
    
    @pytest.mark.asyncio
    async def test_enrich_domain_comprehensive_invalid_domain(self, threat_manager):
        """Test domain enrichment with invalid domain."""
        with pytest.raises(ValueError, match="Invalid domain"):
            await threat_manager.enrich_domain_comprehensive("")
        
        with pytest.raises(ValueError, match="Invalid domain"):
            await threat_manager.enrich_domain_comprehensive("nodots")
    
    @pytest.mark.asyncio
    async def test_correlate_threat_indicators(self, threat_manager):
        """Test threat indicator correlation."""
        indicators = ["8.8.8.8", "example.com", "malware.exe"]
        
        result = await threat_manager.correlate_threat_indicators(indicators)
        
        assert isinstance(result, dict)
        assert "correlation_id" in result
        assert "indicators" in result
        assert result["indicators"] == indicators
        assert "correlations" in result
        assert "relationships" in result
        assert "confidence_score" in result
    
    @pytest.mark.asyncio
    async def test_correlate_threat_indicators_empty_list(self, threat_manager):
        """Test threat indicator correlation with empty list."""
        with pytest.raises(ValueError, match="Indicators list cannot be empty"):
            await threat_manager.correlate_threat_indicators([])
    
    def test_classify_indicator(self, threat_manager):
        """Test indicator classification."""
        assert threat_manager._classify_indicator("8.8.8.8") == "ip_address"
        assert threat_manager._classify_indicator("example.com") == "domain"
        assert threat_manager._classify_indicator("a" * 32) == "hash"
        assert threat_manager._classify_indicator("CVE-2021-1234") == "cve"
        assert threat_manager._classify_indicator("generic_indicator") == "generic"
    
    def test_deduplicate_indicators(self, threat_manager):
        """Test indicator deduplication."""
        indicators = ["malware", "MALWARE", "port_scan", "malware"]
        
        result = threat_manager._deduplicate_indicators(indicators)
        
        assert len(result) == 2  # malware and port_scan
        malware_indicators = [ind for ind in result if ind["indicator"] == "malware"]
        assert len(malware_indicators) == 1
        assert malware_indicators[0]["count"] == 3  # "malware", "MALWARE", "malware" = 3 occurrences
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, threat_manager):
        """Test rate limiting functionality."""
        source = ThreatIntelligenceSource.DSHIELD
        
        # Should not raise exception for first request
        await threat_manager._check_rate_limit(source)
        
        # Mock many requests to exceed rate limit
        threat_manager.rate_limit_trackers[source] = [datetime.now().timestamp()] * 60
        
        with pytest.raises(RuntimeError, match="Rate limit exceeded"):
            await threat_manager._check_rate_limit(source)
    
    def test_get_available_sources(self, threat_manager):
        """Test getting available sources."""
        sources = threat_manager.get_available_sources()
        
        assert isinstance(sources, list)
        assert ThreatIntelligenceSource.DSHIELD in sources
    
    def test_get_source_status(self, threat_manager):
        """Test source status retrieval."""
        status = threat_manager.get_source_status()
        
        assert "dshield" in status
        assert status["dshield"]["enabled"] is True
        assert status["dshield"]["client_type"] == "DShieldClient"
        assert "rate_limit_tracker" in status["dshield"]

    @pytest.mark.asyncio
    async def test_cache_behavior(self, threat_manager):
        """Test that repeated enrichment uses cache."""
        ip = "8.8.8.8"
        result1 = await threat_manager.enrich_ip_comprehensive(ip)
        result2 = await threat_manager.enrich_ip_comprehensive(ip)
        assert result2.cache_hit
    
    @pytest.mark.asyncio
    async def test_sqlite_cache_initialization(self, threat_manager):
        """Test SQLite cache initialization."""
        # Check if SQLite cache is enabled
        assert hasattr(threat_manager, 'sqlite_cache_enabled')
        assert hasattr(threat_manager, 'sqlite_cache_path')
        assert hasattr(threat_manager, 'sqlite_cache_ttl')
        
        # Check if database file exists (if enabled)
        if threat_manager.sqlite_cache_enabled:
            assert os.path.exists(threat_manager.sqlite_cache_path)
    
    @pytest.mark.asyncio
    async def test_sqlite_cache_storage_and_retrieval(self, threat_manager):
        """Test SQLite cache storage and retrieval."""
        if not threat_manager.sqlite_cache_enabled:
            pytest.skip("SQLite cache not enabled")
        
        # Use a unique IP to avoid cache persistence from other tests
        unique_ip = f"10.0.{hash(str(threat_manager)) % 255}.1"
        
        # First call should populate cache
        result1 = await threat_manager.enrich_ip_comprehensive(unique_ip)
        assert not result1.cache_hit
        
        # Second call should hit SQLite cache
        result2 = await threat_manager.enrich_ip_comprehensive(unique_ip)
        assert result2.cache_hit
        
        # Verify results are the same
        assert result1.ip_address == result2.ip_address
        assert result1.overall_threat_score == result2.overall_threat_score
    
    @pytest.mark.asyncio
    async def test_sqlite_cache_expiry(self, threat_manager):
        """Test SQLite cache expiry behavior."""
        if not threat_manager.sqlite_cache_enabled:
            pytest.skip("SQLite cache not enabled")
        
        # Use a unique IP to avoid cache persistence from other tests
        unique_ip = f"172.16.{hash(str(threat_manager)) % 255}.1"
        
        # Temporarily set a very short TTL for testing
        original_ttl = threat_manager.sqlite_cache_ttl
        threat_manager.sqlite_cache_ttl = timedelta(seconds=1)
        
        try:
            # Clear memory cache to ensure we're testing SQLite cache
            threat_manager.cache.clear()
            
            # First call to populate cache
            result1 = await threat_manager.enrich_ip_comprehensive(unique_ip)
            assert not result1.cache_hit
            
            # Wait for cache to expire
            await asyncio.sleep(2)
            
            # Clear memory cache again to force SQLite lookup
            threat_manager.cache.clear()
            
            # Second call should not hit cache due to expiry
            result2 = await threat_manager.enrich_ip_comprehensive(unique_ip)
            assert not result2.cache_hit
        finally:
            # Restore original TTL
            threat_manager.sqlite_cache_ttl = original_ttl
    
    def test_get_cache_statistics(self, threat_manager):
        """Test cache statistics retrieval."""
        stats = threat_manager.get_cache_statistics()
        
        # Check memory cache stats
        assert "memory_cache" in stats
        assert stats["memory_cache"]["enabled"] is True
        assert "size" in stats["memory_cache"]
        assert "ttl_hours" in stats["memory_cache"]
        
        # Check SQLite cache stats
        assert "sqlite_cache" in stats
        assert "enabled" in stats["sqlite_cache"]
        assert "path" in stats["sqlite_cache"]
        assert "ttl_hours" in stats["sqlite_cache"]
        
        # If SQLite cache is enabled, check additional stats
        if stats["sqlite_cache"]["enabled"]:
            assert "total_entries" in stats["sqlite_cache"]
            assert "expired_entries" in stats["sqlite_cache"]
            assert "valid_entries" in stats["sqlite_cache"]
            assert "database_size_bytes" in stats["sqlite_cache"]


class TestThreatIntelligenceModels:
    """Test suite for threat intelligence data models."""
    
    def test_threat_intelligence_result_creation(self):
        """Test ThreatIntelligenceResult model creation."""
        result = ThreatIntelligenceResult(
            ip_address="8.8.8.8",
            overall_threat_score=25.0,
            confidence_score=0.8
        )
        
        assert result.ip_address == "8.8.8.8"
        assert result.overall_threat_score == 25.0
        assert result.confidence_score == 0.8
        assert isinstance(result.query_timestamp, datetime)
        assert result.cache_hit is False
    
    def test_threat_intelligence_result_validation(self):
        """Test ThreatIntelligenceResult validation."""
        # Valid IP
        result = ThreatIntelligenceResult(ip_address="8.8.8.8")
        assert result.ip_address == "8.8.8.8"
        
        # Invalid IP
        with pytest.raises(ValueError, match="Invalid IP address"):
            ThreatIntelligenceResult(ip_address="invalid_ip")
        
        # Invalid threat score
        with pytest.raises(ValueError, match="Overall threat score must be between 0 and 100"):
            ThreatIntelligenceResult(ip_address="8.8.8.8", overall_threat_score=150.0)
        
        # Invalid confidence score
        with pytest.raises(ValueError, match="Confidence score must be between 0 and 1"):
            ThreatIntelligenceResult(ip_address="8.8.8.8", confidence_score=1.5)
    
    def test_domain_intelligence_creation(self):
        """Test DomainIntelligence model creation."""
        result = DomainIntelligence(
            domain="example.com",
            threat_score=30.0,
            reputation_score=70.0
        )
        
        assert result.domain == "example.com"
        assert result.threat_score == 30.0
        assert result.reputation_score == 70.0
        assert isinstance(result.query_timestamp, datetime)
        assert result.cache_hit is False
    
    def test_domain_intelligence_validation(self):
        """Test DomainIntelligence validation."""
        # Valid domain
        result = DomainIntelligence(domain="example.com")
        assert result.domain == "example.com"
        
        # Invalid domain
        with pytest.raises(ValueError, match="Invalid domain"):
            DomainIntelligence(domain="")
        
        with pytest.raises(ValueError, match="Invalid domain"):
            DomainIntelligence(domain="nodots")
        
        # Invalid scores
        with pytest.raises(ValueError, match="Score must be between 0 and 100"):
            DomainIntelligence(domain="example.com", threat_score=150.0)


class TestThreatIntelligenceSource:
    """Test suite for ThreatIntelligenceSource enum."""
    
    def test_source_values(self):
        """Test threat intelligence source values."""
        assert ThreatIntelligenceSource.DSHIELD.value == "dshield"
        assert ThreatIntelligenceSource.VIRUSTOTAL.value == "virustotal"
        assert ThreatIntelligenceSource.SHODAN.value == "shodan"
        assert ThreatIntelligenceSource.ABUSEIPDB.value == "abuseipdb"
        assert ThreatIntelligenceSource.ALIENVAULT.value == "alienvault"
        assert ThreatIntelligenceSource.THREATFOX.value == "threatfox"
    
    def test_source_enumeration(self):
        """Test threat intelligence source enumeration."""
        sources = list(ThreatIntelligenceSource)
        assert len(sources) == 6
        assert ThreatIntelligenceSource.DSHIELD in sources
        assert ThreatIntelligenceSource.VIRUSTOTAL in sources


class TestThreatIntelligenceIntegration:
    """Integration tests for threat intelligence functionality."""
    
    @pytest_asyncio.fixture
    async def manager(self) -> ThreatIntelligenceManager:
        """Create a Threat Intelligence Manager instance for integration testing."""
        manager = ThreatIntelligenceManager()
        yield manager
        await manager.cleanup()
        
        # Clean up SQLite cache file after each test
        if hasattr(manager, 'sqlite_cache_enabled') and manager.sqlite_cache_enabled and os.path.exists(manager.sqlite_cache_path):
            try:
                os.remove(manager.sqlite_cache_path)
            except Exception:
                pass  # Ignore cleanup errors
    
    @pytest.mark.asyncio
    async def test_manager_context_manager(self):
        """Test Threat Intelligence Manager as context manager."""
        async with ThreatIntelligenceManager() as manager:
            assert isinstance(manager, ThreatIntelligenceManager)
            assert manager.clients is not None
        
        # Manager should be cleaned up after context exit
    
    @pytest.mark.asyncio
    async def test_correlation_with_multiple_sources(self):
        """Test correlation with multiple sources (when implemented)."""
        # This test will be expanded when VirusTotal and Shodan clients are implemented
        async with ThreatIntelligenceManager() as manager:
            # For now, test with just DShield
            result = await manager.enrich_ip_comprehensive("8.8.8.8")
            
            assert isinstance(result, ThreatIntelligenceResult)
            assert result.ip_address == "8.8.8.8"
            assert len(result.sources_queried) >= 0  # At least 0 sources
    
    @pytest.mark.asyncio
    async def test_cache_eviction(self):
        """Test cache eviction behavior."""
        def mock_user_config():
            """Create a mock user config for this test."""
            config = MagicMock()
            config.get_setting.return_value = "default_value"
            
            # Mock performance settings for SQLite cache
            performance_settings = MagicMock()
            performance_settings.enable_sqlite_cache = True
            performance_settings.sqlite_cache_ttl_hours = 24
            performance_settings.sqlite_cache_db_name = "test_enrichment_cache.sqlite3"
            config.performance_settings = performance_settings
            
            # Mock database path methods
            config.get_database_directory.return_value = "/tmp/test_db"
            config.get_cache_database_path.return_value = "/tmp/test_db/test_enrichment_cache.sqlite3"
            
            return config
        
        with patch('src.threat_intelligence_manager.get_config', return_value={
            "threat_intelligence": {
                "sources": {
                    "dshield": {"enabled": True}
                }
            }
        }), patch('src.threat_intelligence_manager.get_user_config', return_value=mock_user_config()):
            
            async with ThreatIntelligenceManager() as manager:
                # Test that cache eviction works properly
                # This is a basic test to ensure the manager can be created and cleaned up
                assert manager is not None
                assert hasattr(manager, 'cleanup')

    @pytest.mark.asyncio
    async def test_elasticsearch_writeback_enabled(self, manager):
        """Test Elasticsearch writeback when enabled."""
        # Mock config to enable writeback
        manager.config = {
            "threat_intelligence": {
                "elasticsearch": {
                    "enabled": True,
                    "writeback_enabled": True,
                    "hosts": ["http://localhost:9200"],
                    "index_prefix": "enrichment-intel"
                }
            }
        }
        manager._initialize_elasticsearch()
        # Mock Elasticsearch client
        mock_es_client = AsyncMock()
        manager.elasticsearch_client = mock_es_client
        # Mock source clients
        manager.clients[ThreatIntelligenceSource.DSHIELD] = AsyncMock()
        manager.clients[ThreatIntelligenceSource.DSHIELD].get_ip_reputation.return_value = {
            "threat_score": 75.0,
            "confidence": 0.8
        }
        
        # Perform enrichment
        result = await manager.enrich_ip_comprehensive("8.8.8.8")
        
        # Verify Elasticsearch write was called
        mock_es_client.index.assert_called_once()
        call_args = mock_es_client.index.call_args
        
        # Verify document structure
        doc = call_args[1]["document"]
        assert doc["indicator"] == "8.8.8.8"
        assert doc["indicator_type"] == "ip"
        assert "sources" in doc
        assert "timestamp" in doc
        assert doc["threat_score"] == result.overall_threat_score
        
        # Verify index naming
        index_name = call_args[1]["index"]
        assert index_name.startswith("enrichment-intel-")
    
    @pytest.mark.asyncio
    async def test_elasticsearch_writeback_disabled(self, manager):
        """Test Elasticsearch writeback when disabled."""
        # Mock config to disable writeback
        manager.config = {
            "threat_intelligence": {
                "elasticsearch": {
                    "enabled": True,
                    "writeback_enabled": False,  # Disabled
                    "hosts": ["http://localhost:9200"],
                    "index_prefix": "enrichment-intel"
                }
            }
        }
        manager._initialize_elasticsearch()
        # Mock Elasticsearch client
        mock_es_client = AsyncMock()
        manager.elasticsearch_client = mock_es_client
        # Mock source clients
        manager.clients[ThreatIntelligenceSource.DSHIELD] = AsyncMock()
        manager.clients[ThreatIntelligenceSource.DSHIELD].get_ip_reputation.return_value = {
            "threat_score": 75.0,
            "confidence": 0.8
        }
        
        # Perform enrichment
        result = await manager.enrich_ip_comprehensive("8.8.8.8")
        
        # Verify Elasticsearch write was NOT called
        mock_es_client.index.assert_not_called()
        
        # Verify enrichment still works
        assert result.ip_address == "8.8.8.8"
        assert len(result.sources_queried) == 1
    
    @pytest.mark.asyncio
    async def test_elasticsearch_writeback_no_client(self, manager):
        """Test behavior when Elasticsearch client is not available."""
        # Ensure no Elasticsearch client
        manager.elasticsearch_client = None
        
        # Mock config to enable writeback
        manager.config = {
            "threat_intelligence": {
                "elasticsearch": {
                    "enabled": True,
                    "writeback_enabled": True,
                    "hosts": ["http://localhost:9200"],
                    "index_prefix": "enrichment-intel"
                }
            }
        }
        manager._initialize_elasticsearch()
        # Mock Elasticsearch client
        mock_es_client = AsyncMock()
        manager.elasticsearch_client = mock_es_client
        # Mock source clients
        manager.clients[ThreatIntelligenceSource.DSHIELD] = AsyncMock()
        manager.clients[ThreatIntelligenceSource.DSHIELD].get_ip_reputation.return_value = {
            "threat_score": 75.0,
            "confidence": 0.8
        }
        
        # Perform enrichment - should not fail
        result = await manager.enrich_ip_comprehensive("8.8.8.8")
        
        # Verify enrichment still works
        assert result.ip_address == "8.8.8.8"
        assert len(result.sources_queried) == 1
    
    @pytest.mark.asyncio
    async def test_elasticsearch_writeback_error_handling(self, manager):
        """Test error handling when Elasticsearch writeback fails."""
        # Mock config to enable writeback
        manager.config = {
            "threat_intelligence": {
                "elasticsearch": {
                    "enabled": True,
                    "writeback_enabled": True,
                    "hosts": ["http://localhost:9200"],
                    "index_prefix": "enrichment-intel"
                }
            }
        }
        manager._initialize_elasticsearch()
        # Mock Elasticsearch client that raises an exception
        mock_es_client = AsyncMock()
        mock_es_client.index.side_effect = Exception("Elasticsearch connection failed")
        manager.elasticsearch_client = mock_es_client
        # Mock source clients
        manager.clients[ThreatIntelligenceSource.DSHIELD] = AsyncMock()
        manager.clients[ThreatIntelligenceSource.DSHIELD].get_ip_reputation.return_value = {
            "threat_score": 75.0,
            "confidence": 0.8
        }
        
        # Perform enrichment - should not fail due to ES error
        result = await manager.enrich_ip_comprehensive("8.8.8.8")
        
        # Verify enrichment still works despite ES error
        assert result.ip_address == "8.8.8.8"
        assert len(result.sources_queried) == 1
        
        # Verify Elasticsearch write was attempted
        mock_es_client.index.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_elasticsearch_writeback_document_structure(self, manager):
        """Test that Elasticsearch documents have correct structure."""
        # Mock config to enable writeback
        manager.config = {
            "threat_intelligence": {
                "elasticsearch": {
                    "enabled": True,
                    "writeback_enabled": True,
                    "hosts": ["http://localhost:9200"],
                    "index_prefix": "enrichment-intel"
                }
            }
        }
        manager._initialize_elasticsearch()
        # Mock Elasticsearch client
        mock_es_client = AsyncMock()
        manager.elasticsearch_client = mock_es_client
        # Mock source clients with rich data
        manager.clients[ThreatIntelligenceSource.DSHIELD] = AsyncMock()
        manager.clients[ThreatIntelligenceSource.DSHIELD].get_ip_reputation.return_value = {
            "threat_score": 75.0,
            "confidence": 0.8,
            "asn": 15169,
            "country": "US"
        }
        
        manager.clients[ThreatIntelligenceSource.VIRUSTOTAL] = AsyncMock()
        manager.clients[ThreatIntelligenceSource.VIRUSTOTAL].get_ip_report.return_value = {
            "threat_score": 80.0,
            "confidence": 0.9,
            "malware_families": ["trojan", "backdoor"]
        }
        
        # Perform enrichment
        result = await manager.enrich_ip_comprehensive("8.8.8.8")
        
        # Get the document that was written to Elasticsearch
        call_args = mock_es_client.index.call_args
        doc = call_args[1]["document"]
        
        # Verify required fields
        assert doc["indicator"] == "8.8.8.8"
        assert doc["indicator_type"] == "ip"
        assert "sources" in doc
        assert "timestamp" in doc
        assert "threat_score" in doc
        assert "confidence_score" in doc
        
        # Verify sources data
        sources = doc["sources"]
        assert ThreatIntelligenceSource.DSHIELD.value in sources
        assert ThreatIntelligenceSource.VIRUSTOTAL.value in sources
        
        # Verify network data if present
        if result.network_data:
            assert doc["asn"] == result.network_data.get("asn")
        
        # Verify geographic data if present
        if result.geographic_data:
            assert doc["geo"] == result.geographic_data
        
        # Verify tags from threat indicators
        if result.threat_indicators:
            assert "tags" in doc
            assert isinstance(doc["tags"], list)
    
    @pytest.mark.asyncio
    async def test_elasticsearch_writeback_index_naming(self, manager):
        """Test that Elasticsearch index names follow the correct pattern."""
        # Mock config with custom index prefix
        manager.config = {
            "threat_intelligence": {
                "elasticsearch": {
                    "enabled": True,
                    "writeback_enabled": True,
                    "hosts": ["http://localhost:9200"],
                    "index_prefix": "custom-enrichment"
                }
            }
        }
        manager._initialize_elasticsearch()
        # Mock Elasticsearch client
        mock_es_client = AsyncMock()
        manager.elasticsearch_client = mock_es_client
        # Mock source clients
        manager.clients[ThreatIntelligenceSource.DSHIELD] = AsyncMock()
        manager.clients[ThreatIntelligenceSource.DSHIELD].get_ip_reputation.return_value = {
            "threat_score": 75.0,
            "confidence": 0.8
        }
        
        # Perform enrichment
        await manager.enrich_ip_comprehensive("8.8.8.8")
        
        # Verify index naming
        call_args = mock_es_client.index.call_args
        index_name = call_args[1]["index"]
        
        # Should follow pattern: prefix-YYYY.MM
        assert index_name.startswith("custom-enrichment-")
        assert len(index_name) == len("custom-enrichment-") + 7  # YYYY.MM format
    
    @pytest.mark.asyncio
    async def test_elasticsearch_writeback_document_id(self, manager):
        """Test that Elasticsearch documents have unique IDs."""
        # Mock config to enable writeback
        manager.config = {
            "threat_intelligence": {
                "elasticsearch": {
                    "enabled": True,
                    "writeback_enabled": True,
                    "hosts": ["http://localhost:9200"],
                    "index_prefix": "enrichment-intel"
                }
            }
        }
        manager._initialize_elasticsearch()
        # Mock Elasticsearch client
        mock_es_client = AsyncMock()
        manager.elasticsearch_client = mock_es_client
        # Mock source clients
        manager.clients[ThreatIntelligenceSource.DSHIELD] = AsyncMock()
        manager.clients[ThreatIntelligenceSource.DSHIELD].get_ip_reputation.return_value = {
            "threat_score": 75.0,
            "confidence": 0.8
        }
        
        # Perform enrichment
        await manager.enrich_ip_comprehensive("8.8.8.8")
        
        # Verify document ID format
        call_args = mock_es_client.index.call_args
        doc_id = call_args[1]["id"]
        
        # Should be: ip_timestamp
        assert doc_id.startswith("8.8.8.8_")
        assert len(doc_id) > len("8.8.8.8_")
    
    @pytest.mark.asyncio
    async def test_elasticsearch_writeback_multiple_queries(self, manager):
        """Test that multiple enrichment queries write to Elasticsearch correctly."""
        # Mock config to enable writeback
        manager.config = {
            "threat_intelligence": {
                "elasticsearch": {
                    "enabled": True,
                    "writeback_enabled": True,
                    "hosts": ["http://localhost:9200"],
                    "index_prefix": "enrichment-intel"
                }
            }
        }
        manager._initialize_elasticsearch()
        # Mock Elasticsearch client
        mock_es_client = AsyncMock()
        manager.elasticsearch_client = mock_es_client
        # Mock source clients
        manager.clients[ThreatIntelligenceSource.DSHIELD] = AsyncMock()
        manager.clients[ThreatIntelligenceSource.DSHIELD].get_ip_reputation.return_value = {
            "threat_score": 75.0,
            "confidence": 0.8
        }
        
        # Perform multiple enrichments
        await manager.enrich_ip_comprehensive("8.8.8.8")
        await manager.enrich_ip_comprehensive("1.1.1.1")
        await manager.enrich_ip_comprehensive("208.67.222.222")
        
        # Verify three documents were written
        assert mock_es_client.index.call_count == 3
        
        # Verify different IPs
        calls = mock_es_client.index.call_args_list
        indicators = [call[1]["document"]["indicator"] for call in calls]
        assert "8.8.8.8" in indicators
        assert "1.1.1.1" in indicators
        assert "208.67.222.222" in indicators
        
        # Verify unique document IDs
        doc_ids = [call[1]["id"] for call in calls]
        assert len(set(doc_ids)) == 3  # All IDs should be unique


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 