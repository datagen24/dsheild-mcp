#!/usr/bin/env python3
"""Tests for LaTeX Template Automation MCP Tools.

Tests for the LaTeX template automation functionality including
document generation, template listing, schema validation, and
error handling.
"""

import json
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Dict, Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from src.latex_template_tools import LaTeXTemplateTools

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture
    from _pytest.fixtures import FixtureRequest
    from _pytest.logging import LogCaptureFixture
    from _pytest.monkeypatch import MonkeyPatch
    from pytest_mock.plugin import MockerFixture


class TestLaTeXTemplateTools:
    """Test cases for LaTeXTemplateTools class."""

    @pytest_asyncio.fixture
    async def latex_tools(self, tmp_path: Path) -> LaTeXTemplateTools:
        """Create LaTeXTemplateTools instance with temporary template directory."""
        template_dir = tmp_path / "templates" / "Attack_Report"
        template_dir.mkdir(parents=True)
        
        # Create template_info.json
        template_config = {
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
        
        with open(template_dir / "template_info.json", 'w') as f:
            json.dump(template_config, f)
        
        # Create sample LaTeX files
        (template_dir / "main_report.tex").write_text(r"""
% DShield-MCP Main Report Compilation File
\input{preamble}
\input{document_body}
""")
        
        (template_dir / "document_body.tex").write_text(r"""
\begin{document}
\input{sections/title_page}
\input{sections/executive_summary}
\input{sections/campaign_overview}
\end{document}
""")
        
        (template_dir / "preamble.tex").write_text(r"""
\documentclass{article}
\title{{{REPORT_TITLE}}}
\author{{{AUTHOR_NAME}}}
\date{{{REPORT_DATE}}}
""")
        
        # Create sections directory
        sections_dir = template_dir / "sections"
        sections_dir.mkdir()
        
        (sections_dir / "title_page.tex").write_text(r"""
\maketitle
Report Number: {REPORT_NUMBER}
""")
        
        (sections_dir / "executive_summary.tex").write_text(r"""
\section{Executive Summary}
Campaign: {CAMPAIGN_NAME}
Total Sessions: {TOTAL_SESSIONS}
MCP Version: {MCP_VERSION}
""")
        
        (sections_dir / "campaign_overview.tex").write_text(r"""
\section{Campaign Overview}
Analysis of campaign {CAMPAIGN_NAME}.
""")
        
        # Create assets directory to avoid errors
        assets_dir = template_dir / "assets"
        assets_dir.mkdir(exist_ok=True)
        
        return LaTeXTemplateTools(str(template_dir))

    @pytest_asyncio.fixture
    async def sample_document_data(self) -> Dict[str, Any]:
        """Sample document data for testing."""
        return {
            "REPORT_NUMBER": "REP-2024-001",
            "REPORT_TITLE": "Test Attack Report",
            "AUTHOR_NAME": "Test Analyst",
            "REPORT_DATE": "2024-01-15",
            "CAMPAIGN_NAME": "Test Campaign",
            "TOTAL_SESSIONS": "150",
            "MCP_VERSION": "1.0.0"
        }

    @pytest.mark.asyncio
    async def test_init_with_valid_template_path(self, tmp_path: Path) -> None:
        """Test initialization with valid template path."""
        template_dir = tmp_path / "templates" / "TestTemplate"
        template_dir.mkdir(parents=True)
        
        tools = LaTeXTemplateTools(str(template_dir))
        assert tools.template_base_path == template_dir

    @pytest.mark.asyncio
    async def test_init_with_invalid_template_path(self, tmp_path: Path) -> None:
        """Test initialization with invalid template path."""
        invalid_path = tmp_path / "nonexistent"
        
        with pytest.raises(FileNotFoundError, match="Template directory not found"):
            LaTeXTemplateTools(str(invalid_path))

    @pytest.mark.asyncio
    async def test_list_available_templates(self, latex_tools: LaTeXTemplateTools) -> None:
        """Test listing available templates."""
        result = await latex_tools.list_available_templates()
        
        assert result["success"] is True
        assert len(result["templates"]) >= 1
        assert result["total_templates"] >= 1
        
        # Check template metadata
        template = result["templates"][0]
        assert "name" in template
        assert "display_name" in template
        assert "version" in template
        assert "description" in template
        assert "sections" in template
        assert "required_variables" in template

    @pytest.mark.asyncio
    async def test_get_template_schema(self, latex_tools: LaTeXTemplateTools) -> None:
        """Test getting template schema."""
        result = await latex_tools.get_template_schema("Attack_Report")
        
        assert result["success"] is True
        assert result["schema"] is not None
        
        schema = result["schema"]
        assert "template_name" in schema
        assert "version" in schema
        assert "description" in schema
        assert "sections" in schema
        assert "required_variables" in schema
        assert "variable_types" in schema
        assert "section_descriptions" in schema
        assert "example_data" in schema

    @pytest.mark.asyncio
    async def test_get_template_schema_invalid_template(self, latex_tools: LaTeXTemplateTools) -> None:
        """Test getting schema for invalid template."""
        result = await latex_tools.get_template_schema("InvalidTemplate")
        
        assert result["success"] is False
        assert "error" in result
        assert "Template not found" in result["error"]

    @pytest.mark.asyncio
    async def test_validate_document_data_valid(self, latex_tools: LaTeXTemplateTools, sample_document_data: Dict[str, Any]) -> None:
        """Test validation of valid document data."""
        result = await latex_tools.validate_document_data("Attack_Report", sample_document_data)
        
        assert result["success"] is True
        assert result["validation"]["valid"] is True
        assert len(result["validation"]["errors"]) == 0

    @pytest.mark.asyncio
    async def test_validate_document_data_missing_variables(self, latex_tools: LaTeXTemplateTools) -> None:
        """Test validation of document data with missing variables."""
        incomplete_data = {
            "REPORT_TITLE": "Test Report",
            "AUTHOR_NAME": "Test Analyst"
            # Missing required variables
        }
        
        result = await latex_tools.validate_document_data("Attack_Report", incomplete_data)
        
        assert result["success"] is True
        assert result["validation"]["valid"] is False
        assert len(result["validation"]["errors"]) > 0
        assert len(result["validation"]["missing_variables"]) > 0

    @pytest.mark.asyncio
    async def test_validate_document_data_unused_variables(self, latex_tools: LaTeXTemplateTools, sample_document_data: Dict[str, Any]) -> None:
        """Test validation of document data with unused variables."""
        data_with_extras = sample_document_data.copy()
        data_with_extras["EXTRA_VARIABLE"] = "extra value"
        
        result = await latex_tools.validate_document_data("Attack_Report", data_with_extras)
        
        assert result["success"] is True
        assert result["validation"]["valid"] is True
        assert len(result["validation"]["warnings"]) > 0
        assert "EXTRA_VARIABLE" in result["validation"]["unused_variables"]

    @pytest.mark.asyncio
    @patch('subprocess.run')
    async def test_generate_document_pdf_success(self, mock_run: MagicMock, latex_tools: LaTeXTemplateTools, sample_document_data: Dict[str, Any]) -> None:
        """Test successful PDF document generation."""
        # Mock pdflatex availability check
        mock_run.return_value.returncode = 0
        
        # Mock successful compilation
        mock_run.return_value.stdout = "LaTeX compilation successful"
        mock_run.return_value.stderr = ""
        
        # Patch Path.exists to simulate PDF existence only for the expected PDF path
        original_exists = Path.exists
        def fake_exists(self):
            if self.name == "main_report.pdf":
                # Actually create the file if it doesn't exist
                if not original_exists(self):
                    self.write_text("PDF content")
                return True
            return original_exists(self)
        
        with patch('pathlib.Path.exists', new=fake_exists):
            result = await latex_tools.generate_document(
                template_name="Attack_Report",
                document_data=sample_document_data,
                output_format="pdf"
            )
        
        assert result["success"] is True
        assert result["document"] is not None
        assert result["document"]["template_name"] == "Attack_Report"
        assert result["document"]["output_format"] == "pdf"

    @pytest.mark.asyncio
    @patch('subprocess.run')
    async def test_generate_document_pdf_compilation_failure(self, mock_run: MagicMock, latex_tools: LaTeXTemplateTools, sample_document_data: Dict[str, Any]) -> None:
        """Test PDF document generation with compilation failure."""
        # Mock pdflatex availability check
        mock_run.return_value.returncode = 0
        
        # Mock compilation failure
        mock_run.return_value.stdout = ""
        mock_run.return_value.stderr = "LaTeX compilation failed"
        
        # Patch Path.exists to simulate PDF not being created, but allow template files to be found
        original_exists = Path.exists
        def fake_exists(self):
            if self.name == "main_report.pdf":
                return False
            return original_exists(self)
        
        with patch('pathlib.Path.exists', new=fake_exists):
            result = await latex_tools.generate_document(
                template_name="Attack_Report",
                document_data=sample_document_data,
                output_format="pdf"
            )
        
        assert result["success"] is False
        assert "error" in result
        assert "PDF generation failed" in result["error"]

    @pytest.mark.asyncio
    @patch('subprocess.run')
    async def test_generate_document_pdflatex_not_found(self, mock_run: MagicMock, latex_tools: LaTeXTemplateTools, sample_document_data: Dict[str, Any]) -> None:
        """Test PDF document generation when pdflatex is not available."""
        # Mock pdflatex not found
        mock_run.return_value.returncode = 1
        
        result = await latex_tools.generate_document(
            template_name="Attack_Report",
            document_data=sample_document_data,
            output_format="pdf"
        )
        
        assert result["success"] is False
        assert "error" in result
        assert "pdflatex not found" in result["error"]

    @pytest.mark.asyncio
    async def test_generate_document_tex_format(self, latex_tools: LaTeXTemplateTools, sample_document_data: Dict[str, Any]) -> None:
        """Test LaTeX document generation in TEX format."""
        result = await latex_tools.generate_document(
            template_name="Attack_Report",
            document_data=sample_document_data,
            output_format="tex"
        )
        
        assert result["success"] is True
        assert result["document"] is not None
        assert result["document"]["template_name"] == "Attack_Report"
        assert result["document"]["output_format"] == "tex"
        assert "generated_files" in result["document"]

    @pytest.mark.asyncio
    async def test_generate_document_invalid_template(self, latex_tools: LaTeXTemplateTools, sample_document_data: Dict[str, Any]) -> None:
        """Test document generation with invalid template."""
        result = await latex_tools.generate_document(
            template_name="InvalidTemplate",
            document_data=sample_document_data,
            output_format="pdf"
        )
        
        assert result["success"] is False
        assert "error" in result
        assert "Template not found" in result["error"]

    @pytest.mark.asyncio
    async def test_generate_document_invalid_data(self, latex_tools: LaTeXTemplateTools) -> None:
        """Test document generation with invalid data."""
        invalid_data = {
            "REPORT_TITLE": "Test Report"
            # Missing required variables
        }
        
        result = await latex_tools.generate_document(
            template_name="Attack_Report",
            document_data=invalid_data,
            output_format="pdf"
        )
        
        assert result["success"] is False
        assert "error" in result
        assert "Invalid document data" in result["error"]

    @pytest.mark.asyncio
    async def test_variable_substitution(self, latex_tools: LaTeXTemplateTools) -> None:
        """Test variable substitution in template content."""
        content = r"""
\title{{{REPORT_TITLE}}}
\author{{{AUTHOR_NAME}}}
\date{{{REPORT_DATE}}}
Report Number: {{REPORT_NUMBER}}
"""
        
        document_data = {
            "REPORT_TITLE": "Test Report",
            "AUTHOR_NAME": "Test Analyst",
            "REPORT_DATE": "2024-01-15",
            "REPORT_NUMBER": "REP-001"
        }
        
        processed_content = latex_tools._substitute_variables(content, document_data)
        
        assert "Test Report" in processed_content
        assert "Test Analyst" in processed_content
        assert "2024-01-15" in processed_content
        assert "REP-001" in processed_content
        assert "{{REPORT_TITLE}}" not in processed_content

    @pytest.mark.asyncio
    async def test_infer_variable_types(self, latex_tools: LaTeXTemplateTools) -> None:
        """Test variable type inference."""
        template_config = {
            "required_variables": {
                "metadata": ["REPORT_DATE", "AUTHOR_NAME", "TOTAL_COUNT", "CONFIDENCE_SCORE"]
            }
        }
        
        variable_types = latex_tools._infer_variable_types(template_config)
        
        assert variable_types["REPORT_DATE"] == "datetime"
        assert variable_types["AUTHOR_NAME"] == "string"
        assert variable_types["TOTAL_COUNT"] == "integer"
        assert variable_types["CONFIDENCE_SCORE"] == "float"

    @pytest.mark.asyncio
    async def test_generate_example_data(self, latex_tools: LaTeXTemplateTools) -> None:
        """Test example data generation."""
        template_config = {
            "required_variables": {
                "metadata": ["REPORT_DATE", "AUTHOR_NAME", "TOTAL_COUNT", "CONFIDENCE_SCORE"]
            }
        }
        
        example_data = latex_tools._generate_example_data(template_config)
        
        assert "REPORT_DATE" in example_data
        assert "AUTHOR_NAME" in example_data
        assert "TOTAL_COUNT" in example_data
        assert "CONFIDENCE_SCORE" in example_data
        assert example_data["REPORT_DATE"] == "2024-01-15"
        assert example_data["CONFIDENCE_SCORE"] == "0.85"

    @pytest.mark.asyncio
    async def test_get_section_descriptions(self, latex_tools: LaTeXTemplateTools) -> None:
        """Test section descriptions retrieval."""
        template_path = latex_tools.template_base_path
        descriptions = latex_tools._get_section_descriptions(template_path)
        
        assert "title_page" in descriptions
        assert "executive_summary" in descriptions
        assert "campaign_overview" in descriptions
        assert isinstance(descriptions["title_page"], str)
        assert len(descriptions["title_page"]) > 0

    @pytest.mark.asyncio
    async def test_copy_template_files(self, latex_tools: LaTeXTemplateTools, tmp_path: Path) -> None:
        """Test template file copying."""
        source_path = latex_tools.template_base_path
        dest_path = tmp_path / "dest"
        dest_path.mkdir()
        
        latex_tools._copy_template_files(source_path, dest_path, include_assets=True)
        
        # Check that files were copied
        assert (dest_path / "main_report.tex").exists()
        assert (dest_path / "document_body.tex").exists()
        assert (dest_path / "preamble.tex").exists()
        assert (dest_path / "sections").exists()
        assert (dest_path / "sections" / "title_page.tex").exists()

    @pytest.mark.asyncio
    async def test_process_template_file(self, latex_tools: LaTeXTemplateTools, tmp_path: Path) -> None:
        """Test template file processing with variable substitution."""
        # Create a test file
        test_file = tmp_path / "test.tex"
        test_file.write_text(r"""
\title{{{REPORT_TITLE}}}
\author{{{AUTHOR_NAME}}}
""")
        
        document_data = {
            "REPORT_TITLE": "Test Report",
            "AUTHOR_NAME": "Test Analyst"
        }
        
        await latex_tools._process_template_file(test_file, document_data)
        
        # Check that variables were substituted
        content = test_file.read_text()
        assert "Test Report" in content
        assert "Test Analyst" in content
        assert "{{REPORT_TITLE}}" not in content
        assert "{{AUTHOR_NAME}}" not in content

    @pytest.mark.asyncio
    async def test_copy_output_files(self, latex_tools: LaTeXTemplateTools, tmp_path: Path) -> None:
        """Test output file copying."""
        # Create temporary directory with output files
        temp_path = tmp_path / "temp"
        temp_path.mkdir()
        
        # Create mock output files
        (temp_path / "main_report.pdf").write_text("PDF content")
        (temp_path / "main_report.tex").write_text("TEX content")
        
        output_files = latex_tools._copy_output_files(temp_path, "Attack_Report")
        
        # Check that output files were created
        assert "pdf" in output_files
        assert "tex" in output_files
        
        # Check that files exist in output directory
        pdf_path = Path(output_files["pdf"])
        tex_path = Path(output_files["tex"])
        
        assert pdf_path.exists()
        assert tex_path.exists()
        assert pdf_path.read_text() == "PDF content"
        assert tex_path.read_text() == "TEX content" 