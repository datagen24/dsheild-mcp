# DShield MCP - Elastic SIEM Integration

This MCP (Model Context Protocol) utility connects your DShield SIEM with ChatGPT to enhance security analysis and threat intelligence workflows. It's specifically optimized for DShield SIEM data structures and patterns.

## Features

- **DShield SIEM Integration**: Query DShield-specific indices and data from Elasticsearch
- **DShield Threat Intelligence**: Correlate IP addresses with DShield reputation and attack data
- **DShield Attack Analysis**: Analyze attack patterns, top attackers, and geographic distribution
- **DShield Statistics**: Generate comprehensive DShield-specific security statistics
- **Structured Data Export**: Format DShield security data for ChatGPT analysis
- **Real-time Context Injection**: Provide relevant DShield security context to AI conversations
- **Comprehensive Data Dictionary**: Built-in data dictionary with field descriptions, query examples, and analysis guidelines
- **Model Optimization**: Initial prompts and data patterns to reduce trial and error for AI models
- **Config Optimization**: Streamlined index patterns to minimize connection retries
- **LaTeX Template Automation**: Generate professional security reports using customizable LaTeX templates with variable substitution and PDF compilation

## DShield-Specific Capabilities

### DShield Indices Support
The following index patterns are supported and optimized for minimal retries:

**Cowrie Honeypot Data:**
- `cowrie-*` - General Cowrie honeypot data
- `cowrie.dshield-*` - DShield-specific Cowrie data
- `cowrie.vt_data-*` - VirusTotal integration data
- `cowrie.webhoneypot-*` - Web honeypot data

**Zeek Network Data:**
- `filebeat-zeek-*` - Filebeat Zeek logs
- `zeek.connection*` - Zeek connection logs
- `zeek.dns*` - Zeek DNS logs
- `zeek.files*` - Zeek file logs
- `zeek.http*` - Zeek HTTP logs
- `zeek.ssl*` - Zeek SSL/TLS logs

*Note: Non-existent index patterns have been removed to optimize performance and reduce connection retries.*

### DShield Data Models
- **DShieldAttack**: Structured attack event data
- **DShieldReputation**: IP reputation and threat intelligence
- **DShieldTopAttacker**: Top attacker analysis
- **DShieldGeographicData**: Geographic attack distribution
- **DShieldPortData**: Port-based attack analysis
- **DShieldStatistics**: Comprehensive DShield statistics

### Data Dictionary & Model Optimization
The system includes a comprehensive data dictionary that helps AI models understand DShield data structures:

- **Field Descriptions**: Detailed explanations of all available fields with examples
- **Query Examples**: Pre-built query patterns for common security analysis tasks
- **Data Patterns**: Recognition patterns for attack types, threat levels, and time-based analysis
- **Analysis Guidelines**: Correlation rules and response priorities for threat assessment
- **Initial Prompts**: Built-in prompts provided to models during initialization to reduce trial and error

**Available as:**
- MCP Tool: `get_data_dictionary`
- MCP Resource: `dshield://data-dictionary`
- Server Initialization: Included in experimental capabilities

## Documentation

### API Documentation
Comprehensive API documentation is available for developers and integrators:

- **[API Reference](docs/API_DOCUMENTATION.md)**: Complete API reference with usage examples
- **[Generated HTML Docs](docs/api/index.html)**: Auto-generated HTML documentation
- **[Build Script](scripts/build_api_docs.sh)**: Generate updated API documentation

To generate the latest API documentation:
```bash
# Install development dependencies (includes pdoc)
pip install -r requirements-dev.txt

# Generate API documentation
./scripts/build_api_docs.sh
```

### Implementation Documentation
For detailed implementation information and development history:

- **[Implementation Docs](docs/)**: Comprehensive implementation documentation
- **[Enhancements](docs/Enhancements.md)**: Feature additions and improvements
- **[Changelog](docs/CHANGELOG.md)**: Version history and changes

## Quick Start

### Prerequisites

- Python 3.8 or higher
- Access to Elasticsearch cluster with DShield data
- DShield API key (optional, for threat intelligence enrichment)
- LaTeX distribution (optional, for PDF report generation)
  - **macOS**: Install MacTeX or BasicTeX via `brew install --cask mactex` or `brew install --cask basictex`
  - **Linux**: Install TeX Live via `sudo apt-get install texlive-full` (Ubuntu/Debian) or `sudo yum install texlive-scheme-full` (RHEL/CentOS)
  - **Windows**: Install MiKTeX from https://miktex.org/download

### Virtual Environment Setup

#### Option 1: Automated Setup (Recommended)

**Linux/macOS:**
```bash
# Make setup script executable (if needed)
chmod +x setup_venv.sh

# Run automated setup
./setup_venv.sh
```

**Windows:**
```cmd
# Run automated setup
setup_venv.bat
```

#### Option 2: Manual Setup

**Linux/macOS:**
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
```

**Windows:**
```cmd
# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate.bat

# Upgrade pip
python -m pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Copy environment template
copy .env.example .env
```

### Configuration

1. **Edit Environment Variables**:
   ```bash
   # Edit the .env file with your configuration
   nano .env  # or use your preferred editor
   ```

2. **Required Configuration**:
   ```bash
   # Elasticsearch Configuration
   ELASTICSEARCH_URL=https://your-elasticsearch-cluster:9200
   ELASTICSEARCH_USERNAME=elastic
   ELASTICSEARCH_PASSWORD=your-password
   
   # DShield API Configuration (optional)
   DSHIELD_API_KEY=your-dshield-api-key
   DSHIELD_API_URL=https://dshield.org/api
   ```

### Advanced User Configuration

See [docs/README.md](docs/README.md) (User Configuration Management section) for advanced settings, environment variable overrides, and runtime customization.

### Running the Application

#### Activate Virtual Environment

**Linux/macOS:**
```bash
# Use the activation script
./activate_venv.sh

# Or manually activate
source venv/bin/activate
```

**Windows:**
```cmd
venv\Scripts\activate.bat
```

#### Run the MCP Server
```bash
# Activate virtual environment first
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate.bat  # Windows

# Run the MCP server
python mcp_server.py
```

#### Run Examples
```bash
# Basic usage example
python examples/basic_usage.py

# Data dictionary usage example
python examples/data_dictionary_usage.py

# LaTeX template usage example
python examples/latex_template_usage.py

# Test installation (in dev_tools folder)
cd dev_tools && python test_installation.py

# Test data dictionary functionality (in dev_tools folder)
cd dev_tools && python test_data_dictionary.py

# Configure settings
python config.py
```

#### Deactivate Virtual Environment
```bash
deactivate
```

## 📚 Documentation

For comprehensive documentation, see the [docs/](docs/) folder:

- **[Documentation Index](docs/README.md)** - Complete documentation overview
- **[Usage Guide](docs/USAGE.md)** - Detailed usage examples and API reference
- **[Changelog](docs/CHANGELOG.md)** - Version history and changes
- **[Release Notes](docs/RELEASE_NOTES_v1.0.md)** - Current release information
- **[Enhancements](docs/Enhancements.md)** - Planned features and roadmap
- **[Implementation Guides](docs/)** - Technical implementation details

## Development Setup

For development work, install additional development dependencies:

```bash
# Activate virtual environment
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate.bat  # Windows

# Install development dependencies
pip install -r requirements-dev.txt
```

### Development Tools

- **Testing**: `pytest`
- **Code Formatting**: `black`
- **Linting**: `flake8`
- **Type Checking**: `mypy`
- **Documentation**: `sphinx`

### Development Scripts

Development and testing scripts are located in the `dev_tools/` folder:

```bash
# Navigate to development tools
cd dev_tools

# Run core functionality tests
python test_mcp_server.py
python test_installation.py

# Run feature tests
python test_enhanced_features.py
python test_streaming.py

# Debug tools
python debug_elasticsearch.py
```

**Note**: The `dev_tools/` folder is excluded from releases and contains scripts for development and debugging purposes only. See `dev_tools/README.md` for detailed documentation.

## Configuration

### Environment Variables

- `ELASTICSEARCH_URL`: Your Elasticsearch cluster URL
- `ELASTICSEARCH_USERNAME`: Elasticsearch username
- `ELASTICSEARCH_PASSWORD`: Elasticsearch password
- `DSHIELD_API_KEY`: DShield API key for threat intelligence
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

### 1Password Integration

The DShield MCP supports 1Password CLI integration for secure secret management. You can use `op://` URLs in your environment variables to automatically resolve secrets from 1Password.

#### Setup 1Password CLI

1. **Install 1Password CLI**:
   ```bash
   # macOS (using Homebrew)
   brew install 1password-cli
   
   # Linux
   # Download from: https://1password.com/downloads/command-line/
   
   # Windows
   # Download from: https://1password.com/downloads/command-line/
   ```

2. **Authenticate with 1Password**:
   ```bash
   op signin
   ```

#### Using op:// URLs

Replace sensitive values in your `.env` file with 1Password URLs:

```bash
# Instead of plain text passwords/keys:
ELASTICSEARCH_PASSWORD=your-password-here
DSHIELD_API_KEY=your-api-key-here

# Use 1Password URLs:
ELASTICSEARCH_PASSWORD=op://vault/elasticsearch/password
DSHIELD_API_KEY=op://vault/dshield/api-key
```

#### 1Password URL Format

- **Format**: `op://vault-name/item-name/field-name`
- **Examples**:
  - `op://vault/elasticsearch/password` - Password from Elasticsearch item
  - `op://vault/dshield/api-key` - API key from DShield item
  - `op://vault/credentials/username` - Username from credentials item

#### Testing 1Password Integration

Test your 1Password setup:
```bash
# Activate virtual environment
source venv/bin/activate

# Test 1Password integration (in dev_tools folder)
cd dev_tools && python test_op_integration.py
```

#### Security Benefits

- **No plain text secrets** in configuration files
- **Centralized secret management** in 1Password
- **Automatic secret rotation** through 1Password
- **Audit trail** for secret access
- **Team collaboration** on secret management

#### Fallback Behavior

If 1Password CLI is not available or fails to resolve a URL:
- The system will log a warning
- The original `op://` URL will be used as-is
- This prevents application crashes if 1Password is unavailable

### DShield Elasticsearch Indices

The utility is specifically configured to work with DShield SIEM indices:
- Automatically discovers available DShield indices
- Falls back to general SIEM indices if DShield-specific ones don't exist
- Supports DShield field mappings and data structures

## Usage Examples

### Query DShield Events
```python
# Get DShield events from the last 24 hours
events = query_dshield_events(hours=24)

# Get DShield attack data specifically
attacks = query_dshield_attacks(hours=24)

# Get DShield top attackers
top_attackers = query_dshield_top_attackers(hours=24, limit=100)

# Get DShield geographic data
geo_data = query_dshield_geographic_data()

# Get DShield port data
port_data = query_dshield_port_data()
```

### DShield Reputation and Threat Intelligence
```python
# Query DShield reputation data for IP addresses
reputation = query_dshield_reputation(ip_addresses=["192.168.1.100"])

# Enrich IP with DShield threat intelligence
threat_data = enrich_ip_with_dshield("192.168.1.100")

# Get DShield statistics
stats = get_dshield_statistics(time_range_hours=24)
```

### Generate DShield Attack Report
```python
# Generate structured attack report with DShield data
report = generate_attack_report(events=events, threat_intelligence=ti_data)

# Get security summary with DShield enrichment
summary = get_security_summary(include_threat_intelligence=True)
```

### LaTeX Template Automation
```python
# List available templates
templates = list_latex_templates()

# Get template schema and requirements
schema = get_latex_template_schema(template_name="Attack_Report")

# Validate document data
validation = validate_latex_document_data(
    template_name="Attack_Report",
    document_data={"title": "Security Incident Report", "author": "Security Team"}
)

# Generate LaTeX document with PDF compilation
result = generate_latex_document(
    template_name="Attack_Report",
    document_data={
        "title": "DShield Attack Analysis Report",
        "author": "Security Operations Center",
        "date": "2025-01-27",
        "executive_summary": "Critical security incident detected...",
        "threat_actors": ["APT29", "Lazarus Group"],
        "affected_systems": ["Web Server", "Database"],
        "recommendations": ["Implement MFA", "Update firewall rules"]
    },
    output_format="pdf",
    output_directory="./reports"
)
```

## DShield-Specific Tools

### Available MCP Tools

1. **query_dshield_events** - Query DShield events from Elasticsearch
2. **query_dshield_attacks** - Query DShield attack data specifically
3. **query_dshield_reputation** - Query DShield reputation data for IP addresses
4. **query_dshield_top_attackers** - Query DShield top attackers data
5. **query_dshield_geographic_data** - Query DShield geographic attack data
6. **query_dshield_port_data** - Query DShield port attack data
7. **get_dshield_statistics** - Get comprehensive DShield statistics
8. **enrich_ip_with_dshield** - Enrich IP with DShield threat intelligence
9. **generate_attack_report** - Generate attack report with DShield data
10. **query_events_by_ip** - Query DShield events for specific IP addresses
11. **get_security_summary** - Get security summary with DShield enrichment
12. **list_latex_templates** - List available LaTeX templates
13. **get_latex_template_schema** - Get schema and variable requirements for a template
14. **validate_latex_document_data** - Validate document data against template schema
15. **generate_latex_document** - Generate LaTeX document with variable substitution

### Available Resources

- `dshield://events` - Recent DShield events
- `dshield://attacks` - Recent DShield attack data
- `dshield://top-attackers` - DShield top attackers data
- `dshield://statistics` - DShield statistics and summary data
- `dshield://threat-intelligence` - DShield threat intelligence data

## DShield Data Analysis

### Attack Pattern Detection
The utility detects DShield-specific attack patterns:
- Brute force attacks
- Port scanning
- SQL injection
- Cross-site scripting (XSS)
- DDoS attacks
- Malware activity
- Phishing attempts
- Reconnaissance
- Exploits
- Backdoors
- Data exfiltration
- Privilege escalation
- Persistence mechanisms

### Geographic Analysis
- Attack distribution by country
- Top attacking countries
- Geographic threat intelligence
- Country-based reputation scoring

### Network Analysis
- Port-based attack analysis
- Protocol usage patterns
- ASN-based threat analysis
- Organization-based threat analysis

### Reputation Analysis
- DShield reputation scoring
- Threat level assessment
- Historical attack data
- First/last seen timestamps
- Attack type categorization

## Architecture

### Core Components

1. **ElasticsearchClient** - Optimized for DShield SIEM queries
2. **DShieldClient** - DShield API integration for threat intelligence
3. **DataProcessor** - DShield-specific data processing and analysis
4. **ContextInjector** - Prepare DShield context for ChatGPT
5. **MCP Server** - Protocol communication and tool coordination

### Data Flow

1. **Query DShield Data**: Query DShield-specific indices in Elasticsearch
2. **Enrich with Threat Intelligence**: Correlate with DShield API data
3. **Process and Analyze**: Apply DShield-specific analysis patterns
4. **Generate Reports**: Create structured DShield attack reports
5. **Inject Context**: Provide DShield context to ChatGPT

## Security Considerations

- **API Key Management**: Store DShield API keys securely
- **Rate Limiting**: Respect DShield API rate limits
- **Data Privacy**: Ensure compliance with data protection regulations
- **Network Security**: Use secure connections to Elasticsearch and DShield APIs
- **Access Control**: Implement proper access controls for the MCP server

## Performance Optimization

- **Index Discovery**: Automatically discover available DShield indices
- **Field Mapping**: Optimized DShield field mappings for efficient queries
- **Caching**: Implement caching for frequently accessed DShield data
- **Batch Processing**: Process DShield data in batches for efficiency
- **Connection Pooling**: Reuse connections to Elasticsearch and DShield APIs

## Troubleshooting

### Common Issues

1. **Virtual Environment Issues**:
   - Ensure Python 3.8+ is installed
   - Check that `python3 -m venv` is available
   - Verify virtual environment is activated before running commands

2. **DShield Indices Not Found**: Check if DShield indices exist in your Elasticsearch cluster
3. **API Rate Limiting**: Implement proper rate limiting for DShield API calls
4. **Field Mapping Issues**: Verify DShield field mappings match your data structure
5. **Connection Timeouts**: Adjust timeout settings for large DShield queries

### Debug Mode

Enable debug logging to troubleshoot issues:
```bash
# Activate virtual environment first
source venv/bin/activate

# Set debug logging
export LOG_LEVEL=DEBUG

# Run with debug output
python mcp_server.py
```

### Virtual Environment Management

**Check if virtual environment is active:**
```bash
# Should show path to venv/bin/python
which python
```

**Recreate virtual environment if needed:**
```bash
# Remove old environment
rm -rf venv

# Run setup again
./setup_venv.sh
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Set up development environment:
   ```bash
   ./setup_venv.sh
   pip install -r requirements-dev.txt
   ```
4. Make your changes
5. Add tests for new DShield functionality
6. Run tests: `pytest`
7. Format code: `black .`
8. Submit a pull request

## License

This project is licensed under the BSD 4-Clause License - see the [LICENSE](LICENSE) file for details.

## Support

For support and questions about DShield integration:
- Check the [USAGE.md](USAGE.md) for detailed usage instructions
- Review the examples in the `examples/` directory
- Open an issue on GitHub for bugs or feature requests

## DShield Integration Credits

This utility is specifically designed to work with the [DShield-SIEM](https://github.com/bruneaug/DShield-SIEM) project and follows DShield data patterns and structures. 