# LaTeX Template Automation Implementation

## Overview and Purpose

The LaTeX Template Automation feature provides MCP (Model Context Protocol) tools for generating complete and fully referenced documents using modular LaTeX templates. This feature enables AI assistants to create professional, structured documents with consistent formatting and proper variable substitution.

### Key Features

- **Template Discovery**: List and explore available LaTeX templates
- **Schema Validation**: Get template requirements and validate document data
- **Variable Substitution**: Automatic replacement of template variables with actual data
- **Multi-format Output**: Support for both TEX and PDF output formats
- **Modular Design**: Support for multiple template types beyond just attack reports
- **Error Handling**: Comprehensive validation and error reporting

## Technical Design and Architecture

### Core Components

#### 1. LaTeXTemplateTools Class (`src/latex_template_tools.py`)

The main class that provides all LaTeX template automation functionality:

```python
class LaTeXTemplateTools:
    """MCP tools for LaTeX template automation and document generation."""
    
    def __init__(self, template_base_path: Optional[str] = None):
        """Initialize with template directory path."""
    
    async def generate_document(self, template_name: str, document_data: Dict[str, Any], ...) -> Dict[str, Any]:
        """Generate complete document from template."""
    
    async def list_available_templates(self) -> Dict[str, Any]:
        """List all available templates with metadata."""
    
    async def get_template_schema(self, template_name: str) -> Dict[str, Any]:
        """Get template schema and requirements."""
    
    async def validate_document_data(self, template_name: str, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate document data against template requirements."""
```

#### 2. Template Structure

Templates follow a standardized directory structure:

```
templates/
├── Attack_Report/
│   ├── template_info.json          # Template metadata and requirements
│   ├── main_report.tex            # Main compilation file
│   ├── document_body.tex          # Document structure
│   ├── preamble.tex               # Document preamble
│   ├── sections/                  # Modular sections
│   │   ├── title_page.tex
│   │   ├── executive_summary.tex
│   │   └── campaign_overview.tex
│   └── assets/                    # Template assets (optional)
```

#### 3. Template Configuration (template_info.json)

```json
{
    "template_name": "DShield-MCP Attack Observation Report",
    "version": "2.1",
    "description": "Modular LaTeX template for DShield-MCP attack analysis reports",
    "sections": [
        "title_page",
        "executive_summary",
        "campaign_overview"
    ],
    "required_variables": {
        "report_metadata": ["REPORT_NUMBER", "REPORT_TITLE", "AUTHOR_NAME", "REPORT_DATE"],
        "analysis_data": ["CAMPAIGN_NAME", "TOTAL_SESSIONS", "MCP_VERSION"]
    }
}
```

### MCP Integration

The LaTeX tools are integrated into the main MCP server (`mcp_server.py`) with four new tools:

1. **generate_latex_document**: Generate complete documents from templates
2. **list_latex_templates**: List available templates with metadata
3. **get_latex_template_schema**: Get template requirements and schema
4. **validate_latex_document_data**: Validate document data against requirements

## Dependencies and Requirements

### Core Dependencies

- **Python 3.8+**: For async/await support and type hints
- **pathlib**: For cross-platform path handling
- **tempfile**: For temporary working directories
- **subprocess**: For LaTeX compilation (optional)
- **structlog**: For structured logging

### Optional Dependencies

- **LaTeX Distribution**: For PDF generation (pdflatex command)
  - TeX Live (Linux/macOS)
  - MiKTeX (Windows)
  - BasicTeX (macOS minimal)

### Template Requirements

- **template_info.json**: Required metadata file
- **main_report.tex**: Main compilation entry point
- **Modular sections**: Organized in sections/ directory
- **Variable placeholders**: Using {{VARIABLE_NAME}} syntax

## Implementation Details and Code Examples

### Variable Substitution

The system uses a simple but effective variable substitution mechanism:

```python
def _substitute_variables(self, content: str, document_data: Dict[str, Any]) -> str:
    """Substitute variables in template content."""
    for var_name, var_value in document_data.items():
        placeholder = f"{{{{{var_name}}}}}"
        if isinstance(var_value, str):
            content = content.replace(placeholder, var_value)
        else:
            content = content.replace(placeholder, str(var_value))
    return content
```

### Document Generation Workflow

1. **Template Validation**: Check template exists and load configuration
2. **Data Validation**: Validate document data against template requirements
3. **File Preparation**: Copy template files to temporary directory
4. **Variable Substitution**: Process all template files with data
5. **Compilation** (PDF only): Run pdflatex if PDF output requested
6. **Output Management**: Copy generated files to final location

### Error Handling

Comprehensive error handling covers:

- **Template not found**: Clear error messages for missing templates
- **Invalid data**: Detailed validation errors with missing variables
- **Compilation failures**: LaTeX compilation error capture and reporting
- **File system errors**: Graceful handling of permission and path issues

## Configuration and Setup Instructions

### Basic Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Create Template Directory**:
   ```bash
   mkdir -p templates/Attack_Report
   ```

3. **Add Template Files**: Copy LaTeX template files to the template directory

4. **Configure template_info.json**: Define template metadata and requirements

### LaTeX Setup (Optional)

For PDF generation, install a LaTeX distribution:

**Ubuntu/Debian**:
```bash
sudo apt-get install texlive-full
```

**macOS**:
```bash
brew install --cask mactex
```

**Windows**:
Download and install MiKTeX from https://miktex.org/

### Environment Variables

No additional environment variables are required. The system uses the default template path (`templates/Attack_Report`) or accepts a custom path during initialization.

## Testing Approach and Considerations

### Test Coverage

The test suite (`tests/test_latex_template_tools.py`) covers:

- **Initialization**: Valid and invalid template paths
- **Template Discovery**: Listing available templates
- **Schema Retrieval**: Getting template requirements
- **Data Validation**: Valid and invalid document data
- **Document Generation**: TEX and PDF output formats
- **Error Handling**: Various failure scenarios
- **Variable Substitution**: Template processing
- **File Operations**: Template copying and output management

### Test Strategy

- **Unit Tests**: Individual method testing with mocked dependencies
- **Integration Tests**: End-to-end workflow testing
- **Error Scenarios**: Comprehensive error condition testing
- **Mocking**: LaTeX compilation mocking for CI/CD compatibility

### Example Test

```python
async def test_generate_document_tex_format(self, latex_tools: LaTeXTemplateTools, sample_document_data: Dict[str, Any]) -> None:
    """Test LaTeX document generation in TEX format."""
    result = await latex_tools.generate_document(
        template_name="Attack_Report",
        document_data=sample_document_data,
        output_format="tex"
    )
    
    assert result["success"] is True
    assert result["document"]["template_name"] == "Attack_Report"
    assert result["document"]["output_format"] == "tex"
```

## Security Implications

### File System Security

- **Temporary Directories**: Uses `tempfile.TemporaryDirectory()` for secure temporary file handling
- **Path Validation**: Validates template paths to prevent directory traversal
- **File Permissions**: Maintains appropriate file permissions for generated documents

### Input Validation

- **Template Validation**: Validates template structure and configuration
- **Data Validation**: Validates document data against template requirements
- **Variable Sanitization**: Ensures variable substitution doesn't introduce security issues

### LaTeX Compilation Security

- **Command Injection Prevention**: Uses subprocess with proper argument handling
- **Timeout Protection**: 60-second timeout on LaTeX compilation
- **Error Isolation**: Compilation errors don't expose system information

## Performance Considerations

### Optimization Strategies

1. **Temporary File Management**: Efficient use of temporary directories
2. **File Copying**: Optimized file copying with shutil
3. **Variable Substitution**: Efficient string replacement
4. **Memory Management**: Proper cleanup of temporary resources

### Scalability

- **Template Caching**: Template configurations are loaded once per instance
- **Parallel Processing**: Async/await support for concurrent operations
- **Resource Cleanup**: Automatic cleanup of temporary files

### Monitoring

- **Structured Logging**: Comprehensive logging for debugging and monitoring
- **Performance Metrics**: Generation time and file size tracking
- **Error Tracking**: Detailed error reporting for troubleshooting

## Migration Steps

### From Manual LaTeX Generation

1. **Template Migration**: Convert existing LaTeX documents to template format
2. **Variable Extraction**: Identify and extract template variables
3. **Configuration Creation**: Create template_info.json files
4. **Testing**: Validate template functionality with new system

### From Other Template Systems

1. **Template Conversion**: Convert templates to LaTeX format
2. **Variable Mapping**: Map existing variables to new system
3. **Integration**: Update existing workflows to use new MCP tools
4. **Validation**: Ensure output quality matches existing system

## Usage Examples

### Basic Document Generation

```python
from src.latex_template_tools import LaTeXTemplateTools

latex_tools = LaTeXTemplateTools()

document_data = {
    "REPORT_NUMBER": "REP-2024-001",
    "REPORT_TITLE": "Security Analysis Report",
    "AUTHOR_NAME": "Security Team",
    "REPORT_DATE": "2024-01-15",
    "CAMPAIGN_NAME": "APT-2024-001",
    "TOTAL_SESSIONS": "150",
    "MCP_VERSION": "1.0.0"
}

result = await latex_tools.generate_document(
    template_name="Attack_Report",
    document_data=document_data,
    output_format="pdf"
)
```

### Template Discovery

```python
# List available templates
templates = await latex_tools.list_available_templates()

# Get template schema
schema = await latex_tools.get_template_schema("Attack_Report")

# Validate document data
validation = await latex_tools.validate_document_data("Attack_Report", document_data)
```

### MCP Tool Usage

```json
{
    "name": "generate_latex_document",
    "arguments": {
        "template_name": "Attack_Report",
        "document_data": {
            "REPORT_NUMBER": "REP-2024-001",
            "REPORT_TITLE": "Security Analysis Report",
            "AUTHOR_NAME": "Security Team",
            "REPORT_DATE": "2024-01-15",
            "CAMPAIGN_NAME": "APT-2024-001",
            "TOTAL_SESSIONS": "150",
            "MCP_VERSION": "1.0.0"
        },
        "output_format": "pdf",
        "include_assets": true
    }
}
```

## Future Enhancements

### Planned Features

1. **Template Versioning**: Support for template version management
2. **Advanced Variables**: Support for complex data types and conditional content
3. **Template Inheritance**: Support for template inheritance and composition
4. **Custom Output Formats**: Support for additional output formats (HTML, DOCX)
5. **Template Marketplace**: Repository of community-contributed templates

### Integration Opportunities

1. **Campaign Analysis Integration**: Direct integration with campaign analysis tools
2. **Threat Intelligence**: Automatic inclusion of threat intelligence data
3. **Report Scheduling**: Automated report generation and distribution
4. **Collaborative Editing**: Multi-user template editing and review

## Conclusion

The LaTeX Template Automation feature provides a robust, scalable solution for generating professional documents through MCP tools. The modular design, comprehensive validation, and flexible configuration make it suitable for various use cases beyond security reporting.

The implementation follows best practices for security, performance, and maintainability, with extensive testing and documentation to ensure reliability and ease of use. 