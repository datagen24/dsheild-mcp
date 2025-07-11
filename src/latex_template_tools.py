#!/usr/bin/env python3
"""LaTeX Template Automation MCP Tools.

MCP tools for LaTeX template automation and document generation.
Provides functionality to generate complete and fully referenced documents
using modular LaTeX templates.
"""

import asyncio
import json
import os
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import structlog

from .user_config import get_user_config

logger = structlog.get_logger(__name__)


class LaTeXTemplateTools:
    """MCP tools for LaTeX template automation and document generation."""
    
    def __init__(self, template_base_path: Optional[str] = None):
        """Initialize LaTeXTemplateTools.

        Args:
            template_base_path: Base path for LaTeX templates. Defaults to templates/Attack_Report.

        """
        self.template_base_path = Path(template_base_path or "templates/Attack_Report")
        self.user_config = get_user_config()
        
        # Ensure template directory exists
        if not self.template_base_path.exists():
            raise FileNotFoundError(f"Template directory not found: {self.template_base_path}")
    
    async def generate_document(
        self,
        template_name: str,
        document_data: Dict[str, Any],
        output_format: str = "pdf",
        include_assets: bool = True,
        compile_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate a complete document from a LaTeX template.
        
        Args:
            template_name: Name of the template to use (e.g., "Attack_Report")
            document_data: Data to populate the template with
            output_format: Output format (pdf, tex, html)
            include_assets: Whether to include template assets
            compile_options: Additional compilation options
        
        Returns:
            Document generation results with file paths and metadata

        """
        logger.info("Starting document generation",
                   template_name=template_name,
                   output_format=output_format,
                   include_assets=include_assets)
        
        try:
            # Validate template
            template_path = self._get_template_path(template_name)
            if not template_path.exists():
                return {
                    "success": False,
                    "error": f"Template not found: {template_name}",
                    "document": None
                }
            
            # Load template configuration
            template_config = self._load_template_config(template_path)
            
            # Validate required data
            validation_result = self._validate_document_data(document_data, template_config)
            if not validation_result["valid"]:
                return {
                    "success": False,
                    "error": f"Invalid document data: {validation_result['errors']}",
                    "document": None
                }
            
            # Create temporary working directory
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Copy template files
                self._copy_template_files(template_path, temp_path, include_assets)
                
                # Generate document content
                generated_files = await self._generate_document_content(
                    temp_path, document_data, template_config
                )
                
                # Compile document
                if output_format == "pdf":
                    compile_result = await self._compile_latex_document(temp_path, compile_options)
                    if not compile_result["success"]:
                        return {
                            "success": False,
                            "error": f"LaTeX compilation failed: {compile_result['error']}",
                            "document": None
                        }
                    
                    # Copy output files
                    output_files = self._copy_output_files(temp_path, template_name)
                    
                    return {
                        "success": True,
                        "document": {
                            "template_name": template_name,
                            "output_format": output_format,
                            "generated_files": generated_files,
                            "output_files": output_files,
                            "compilation_log": compile_result.get("log"),
                            "metadata": {
                                "generated_at": datetime.now().isoformat(),
                                "template_version": template_config.get("version"),
                                "total_sections": len(template_config.get("sections", [])),
                                "variables_used": len(document_data)
                            }
                        }
                    }
                else:
                    # For non-PDF formats, return generated files
                    return {
                        "success": True,
                        "document": {
                            "template_name": template_name,
                            "output_format": output_format,
                            "generated_files": generated_files,
                            "metadata": {
                                "generated_at": datetime.now().isoformat(),
                                "template_version": template_config.get("version"),
                                "total_sections": len(template_config.get("sections", [])),
                                "variables_used": len(document_data)
                            }
                        }
                    }
                    
        except Exception as e:
            logger.error("Document generation failed", error=str(e))
            return {
                "success": False,
                "error": f"Document generation failed: {str(e)}",
                "document": None
            }
    
    async def list_available_templates(self) -> Dict[str, Any]:
        """List all available LaTeX templates.
        
        Returns:
            List of available templates with metadata

        """
        logger.info("Listing available templates")
        
        try:
            templates = []
            
            # Look for template directories
            for item in self.template_base_path.parent.iterdir():
                if item.is_dir() and item != self.template_base_path:
                    template_config_path = item / "template_info.json"
                    if template_config_path.exists():
                        try:
                            with open(template_config_path, 'r') as f:
                                config = json.load(f)
                            
                            templates.append({
                                "name": item.name,
                                "display_name": config.get("template_name", item.name),
                                "version": config.get("version", "1.0"),
                                "description": config.get("description", ""),
                                "sections": config.get("sections", []),
                                "required_variables": config.get("required_variables", {}),
                                "created_date": config.get("created_date", ""),
                                "path": str(item)
                            })
                        except Exception as e:
                            logger.warning(f"Failed to load template config for {item.name}: {e}")
            
            # Add current template if it exists
            current_config_path = self.template_base_path / "template_info.json"
            if current_config_path.exists():
                try:
                    with open(current_config_path, 'r') as f:
                        config = json.load(f)
                    
                    templates.append({
                        "name": self.template_base_path.name,
                        "display_name": config.get("template_name", self.template_base_path.name),
                        "version": config.get("version", "1.0"),
                        "description": config.get("description", ""),
                        "sections": config.get("sections", []),
                        "required_variables": config.get("required_variables", {}),
                        "created_date": config.get("created_date", ""),
                        "path": str(self.template_base_path)
                    })
                except Exception as e:
                    logger.warning(f"Failed to load current template config: {e}")
            
            return {
                "success": True,
                "templates": templates,
                "total_templates": len(templates)
            }
            
        except Exception as e:
            logger.error("Failed to list templates", error=str(e))
            return {
                "success": False,
                "error": f"Failed to list templates: {str(e)}",
                "templates": []
            }
    
    async def get_template_schema(self, template_name: str) -> Dict[str, Any]:
        """Get the schema and requirements for a specific template.
        
        Args:
            template_name: Name of the template to get schema for
        
        Returns:
            Template schema with required variables and structure

        """
        logger.info("Getting template schema", template_name=template_name)
        
        try:
            template_path = self._get_template_path(template_name)
            if not template_path.exists():
                return {
                    "success": False,
                    "error": f"Template not found: {template_name}",
                    "schema": None
                }
            
            template_config = self._load_template_config(template_path)
            
            # Build schema from template configuration
            schema = {
                "template_name": template_config.get("template_name", template_name),
                "version": template_config.get("version", "1.0"),
                "description": template_config.get("description", ""),
                "sections": template_config.get("sections", []),
                "required_variables": template_config.get("required_variables", {}),
                "variable_types": self._infer_variable_types(template_config),
                "section_descriptions": self._get_section_descriptions(template_path),
                "example_data": self._generate_example_data(template_config)
            }
            
            return {
                "success": True,
                "schema": schema
            }
            
        except Exception as e:
            logger.error("Failed to get template schema", error=str(e))
            return {
                "success": False,
                "error": f"Failed to get template schema: {str(e)}",
                "schema": None
            }
    
    async def validate_document_data(
        self,
        template_name: str,
        document_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate document data against template requirements.
        
        Args:
            template_name: Name of the template to validate against
            document_data: Document data to validate
        
        Returns:
            Validation results with errors and warnings

        """
        logger.info("Validating document data", template_name=template_name)
        
        try:
            template_path = self._get_template_path(template_name)
            if not template_path.exists():
                return {
                    "success": False,
                    "error": f"Template not found: {template_name}",
                    "validation": None
                }
            
            template_config = self._load_template_config(template_path)
            validation_result = self._validate_document_data(document_data, template_config)
            
            return {
                "success": True,
                "validation": validation_result
            }
            
        except Exception as e:
            logger.error("Failed to validate document data", error=str(e))
            return {
                "success": False,
                "error": f"Failed to validate document data: {str(e)}",
                "validation": None
            }
    
    def _get_template_path(self, template_name: str) -> Path:
        """Get the path to a specific template.
        
        Args:
            template_name: Name of the template
        
        Returns:
            Path to the template directory

        """
        if template_name == "Attack_Report":
            return self.template_base_path
        else:
            return self.template_base_path.parent / template_name
    
    def _load_template_config(self, template_path: Path) -> Dict[str, Any]:
        """Load template configuration from template_info.json.
        
        Args:
            template_path: Path to the template directory
        
        Returns:
            Template configuration dictionary

        """
        config_path = template_path / "template_info.json"
        if not config_path.exists():
            raise FileNotFoundError(f"Template config not found: {config_path}")
        
        with open(config_path, 'r') as f:
            return json.load(f)
    
    def _validate_document_data(
        self,
        document_data: Dict[str, Any],
        template_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate document data against template requirements.
        
        Args:
            document_data: Document data to validate
            template_config: Template configuration
        
        Returns:
            Validation results

        """
        errors = []
        warnings = []
        missing_vars = []
        
        required_vars = template_config.get("required_variables", {})
        
        # Check required variables
        for category, variables in required_vars.items():
            for var in variables:
                if var not in document_data:
                    missing_vars.append(var)
                    errors.append(f"Missing required variable: {var}")
        
        # Check for unused variables
        used_vars = set()
        for category_vars in required_vars.values():
            used_vars.update(category_vars)
        
        unused_vars = set(document_data.keys()) - used_vars
        if unused_vars:
            warnings.append(f"Unused variables: {', '.join(unused_vars)}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "missing_variables": missing_vars,
            "unused_variables": list(unused_vars),
            "total_variables": len(document_data),
            "required_variables": len([v for vars in required_vars.values() for v in vars])
        }
    
    async def _generate_document_content(
        self,
        temp_path: Path,
        document_data: Dict[str, Any],
        template_config: Dict[str, Any]
    ) -> List[str]:
        """Generate document content by processing template files.
        
        Args:
            temp_path: Temporary working directory
            document_data: Data to populate template with
            template_config: Template configuration
        
        Returns:
            List of generated file paths

        """
        generated_files = []
        
        # Process main document files
        main_files = ["main_report.tex", "document_body.tex", "preamble.tex"]
        for file_name in main_files:
            file_path = temp_path / file_name
            if file_path.exists():
                await self._process_template_file(file_path, document_data)
                generated_files.append(str(file_path))
        
        # Process section files
        sections_dir = temp_path / "sections"
        if sections_dir.exists():
            for section_file in sections_dir.glob("*.tex"):
                await self._process_template_file(section_file, document_data)
                generated_files.append(str(section_file))
        
        return generated_files
    
    async def _process_template_file(
        self,
        file_path: Path,
        document_data: Dict[str, Any]
    ) -> None:
        """Process a single template file with variable substitution.
        
        Args:
            file_path: Path to the template file
            document_data: Data to substitute

        """
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Perform variable substitution
            processed_content = self._substitute_variables(content, document_data)
            
            with open(file_path, 'w') as f:
                f.write(processed_content)
                
        except Exception as e:
            logger.error(f"Failed to process template file {file_path}: {e}")
            raise
    
    def _substitute_variables(self, content: str, document_data: Dict[str, Any]) -> str:
        """Substitute variables in template content.
        
        Args:
            content: Template content
            document_data: Data to substitute
        
        Returns:
            Processed content with variables substituted

        """
        # Simple variable substitution - replace {{VARIABLE_NAME}} with values
        for var_name, var_value in document_data.items():
            placeholder = f"{{{{{var_name}}}}}"
            if isinstance(var_value, str):
                content = content.replace(placeholder, var_value)
            else:
                content = content.replace(placeholder, str(var_value))
        
        return content
    
    def _copy_template_files(
        self,
        template_path: Path,
        temp_path: Path,
        include_assets: bool
    ) -> None:
        """Copy template files to temporary directory.
        
        Args:
            template_path: Source template directory
            temp_path: Destination temporary directory
            include_assets: Whether to include assets

        """
        import shutil
        
        # Copy all .tex files
        for tex_file in template_path.glob("*.tex"):
            shutil.copy2(tex_file, temp_path)
        
        # Copy sections directory
        sections_src = template_path / "sections"
        if sections_src.exists():
            sections_dst = temp_path / "sections"
            shutil.copytree(sections_src, sections_dst)
        
        # Copy assets if requested
        if include_assets:
            assets_src = template_path / "assets"
            if assets_src.exists():
                assets_dst = temp_path / "assets"
                shutil.copytree(assets_src, assets_dst)
    
    async def _compile_latex_document(
        self,
        temp_path: Path,
        compile_options: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Compile LaTeX document to PDF.
        
        Args:
            temp_path: Directory containing LaTeX files
            compile_options: Additional compilation options
        
        Returns:
            Compilation results

        """
        try:
            # Check if pdflatex is available
            result = subprocess.run(
                ["which", "pdflatex"],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                return {
                    "success": False,
                    "error": "pdflatex not found. Please install LaTeX distribution.",
                    "log": None
                }
            
            # Compile the document
            cmd = ["pdflatex", "-interaction=nonstopmode", "main_report.tex"]
            
            if compile_options:
                if compile_options.get("quiet", False):
                    cmd.append("-quiet")
                if compile_options.get("shell_escape", False):
                    cmd.append("-shell-escape")
            
            result = subprocess.run(
                cmd,
                cwd=temp_path,
                capture_output=True,
                text=True,
                timeout=60  # 60 second timeout
            )
            
            # Check if PDF was generated
            pdf_path = temp_path / "main_report.pdf"
            if pdf_path.exists():
                return {
                    "success": True,
                    "log": result.stdout + result.stderr,
                    "pdf_path": str(pdf_path)
                }
            else:
                return {
                    "success": False,
                    "error": "PDF generation failed",
                    "log": result.stdout + result.stderr
                }
                
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "LaTeX compilation timed out",
                "log": None
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"LaTeX compilation failed: {str(e)}",
                "log": None
            }
    
    def _copy_output_files(self, temp_path: Path, template_name: str) -> Dict[str, str]:
        """Copy output files to final location.
        
        Args:
            temp_path: Temporary directory with output files
            template_name: Name of the template
        
        Returns:
            Dictionary of output file paths

        """
        output_files = {}
        
        # Create output directory
        output_dir = Path("output") / template_name
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy PDF if it exists
        pdf_src = temp_path / "main_report.pdf"
        if pdf_src.exists():
            pdf_dst = output_dir / f"{template_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            import shutil
            shutil.copy2(pdf_src, pdf_dst)
            output_files["pdf"] = str(pdf_dst)
        
        # Copy source files
        tex_src = temp_path / "main_report.tex"
        if tex_src.exists():
            tex_dst = output_dir / f"{template_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.tex"
            import shutil
            shutil.copy2(tex_src, tex_dst)
            output_files["tex"] = str(tex_dst)
        
        return output_files
    
    def _infer_variable_types(self, template_config: Dict[str, Any]) -> Dict[str, str]:
        """Infer variable types from template configuration.
        
        Args:
            template_config: Template configuration
        
        Returns:
            Dictionary mapping variable names to inferred types

        """
        variable_types = {}
        required_vars = template_config.get("required_variables", {})
        
        for category, variables in required_vars.items():
            for var in variables:
                # Simple type inference based on variable name
                var_lower = var.lower()
                if any(keyword in var_lower for keyword in ["date", "time"]):
                    variable_types[var] = "datetime"
                elif any(keyword in var_lower for keyword in ["number", "count", "total"]):
                    variable_types[var] = "integer"
                elif any(keyword in var_lower for keyword in ["score", "confidence", "percentage"]):
                    variable_types[var] = "float"
                else:
                    variable_types[var] = "string"
        
        return variable_types
    
    def _get_section_descriptions(self, template_path: Path) -> Dict[str, str]:
        """Get descriptions for template sections.
        
        Args:
            template_path: Path to template directory
        
        Returns:
            Dictionary mapping section names to descriptions

        """
        descriptions = {
            "title_page": "Document title page with metadata",
            "executive_summary": "High-level executive summary",
            "campaign_overview": "Overview of the attack campaign",
            "attack_analysis": "Detailed attack analysis",
            "c2_infrastructure": "Command and control infrastructure analysis",
            "payload_analysis": "Malware and payload analysis",
            "mcp_capabilities": "MCP tool capabilities and usage",
            "iocs": "Indicators of compromise",
            "threat_assessment": "Threat assessment and risk analysis",
            "recommendations": "Security recommendations",
            "conclusion": "Document conclusion",
            "references": "References and citations"
        }
        
        return descriptions
    
    def _generate_example_data(self, template_config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate example data for template.
        
        Args:
            template_config: Template configuration
        
        Returns:
            Example data dictionary

        """
        example_data = {}
        required_vars = template_config.get("required_variables", {})
        
        for category, variables in required_vars.items():
            for var in variables:
                var_lower = var.lower()
                if "date" in var_lower:
                    example_data[var] = "2024-01-15"
                elif "time" in var_lower:
                    example_data[var] = "14:30:00"
                elif "number" in var_lower or "count" in var_lower:
                    example_data[var] = "42"
                elif "score" in var_lower or "confidence" in var_lower:
                    example_data[var] = "0.85"
                elif "name" in var_lower:
                    example_data[var] = "Example Name"
                elif "title" in var_lower:
                    example_data[var] = "Example Title"
                else:
                    example_data[var] = f"Example {var}"
        
        return example_data 