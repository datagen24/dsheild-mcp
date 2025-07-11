#!/usr/bin/env python3
"""Example usage of LaTeX Template Automation MCP Tools.

This example demonstrates how to use the LaTeX template automation
tools to generate complete and fully referenced documents.
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.latex_template_tools import LaTeXTemplateTools


async def example_list_templates() -> None:
    """Example: List available LaTeX templates."""
    print("=== Listing Available Templates ===")
    
    latex_tools = LaTeXTemplateTools()
    result = await latex_tools.list_available_templates()
    
    if result["success"]:
        print(f"Found {result['total_templates']} templates:")
        for template in result["templates"]:
            print(f"  - {template['name']}: {template['display_name']}")
            print(f"    Version: {template['version']}")
            print(f"    Description: {template['description']}")
            print(f"    Sections: {', '.join(template['sections'])}")
            print()
    else:
        print(f"Error: {result['error']}")


async def example_get_template_schema() -> None:
    """Example: Get schema for a specific template."""
    print("=== Getting Template Schema ===")
    
    latex_tools = LaTeXTemplateTools()
    result = await latex_tools.get_template_schema("Attack_Report")
    
    if result["success"]:
        schema = result["schema"]
        print(f"Template: {schema['template_name']}")
        print(f"Version: {schema['version']}")
        print(f"Description: {schema['description']}")
        print(f"Sections: {', '.join(schema['sections'])}")
        print("\nRequired Variables:")
        for category, variables in schema["required_variables"].items():
            print(f"  {category}:")
            for var in variables:
                var_type = schema["variable_types"].get(var, "string")
                print(f"    - {var} ({var_type})")
        print("\nExample Data:")
        for var, value in schema["example_data"].items():
            print(f"  {var}: {value}")
    else:
        print(f"Error: {result['error']}")


async def example_validate_document_data() -> None:
    """Example: Validate document data against template requirements."""
    print("=== Validating Document Data ===")
    
    latex_tools = LaTeXTemplateTools()
    
    # Valid document data
    valid_data = {
        "REPORT_NUMBER": "REP-2024-001",
        "REPORT_TITLE": "Advanced Persistent Threat Analysis",
        "AUTHOR_NAME": "Security Analyst",
        "REPORT_DATE": "2024-01-15",
        "CAMPAIGN_NAME": "APT-2024-001",
        "TOTAL_SESSIONS": "150",
        "MCP_VERSION": "1.0.0"
    }
    
    result = await latex_tools.validate_document_data("Attack_Report", valid_data)
    
    if result["success"]:
        validation = result["validation"]
        print(f"Valid: {validation['valid']}")
        print(f"Total variables: {validation['total_variables']}")
        print(f"Required variables: {validation['required_variables']}")
        
        if validation["errors"]:
            print("Errors:")
            for error in validation["errors"]:
                print(f"  - {error}")
        
        if validation["warnings"]:
            print("Warnings:")
            for warning in validation["warnings"]:
                print(f"  - {warning}")
    else:
        print(f"Error: {result['error']}")


async def example_generate_document() -> None:
    """Example: Generate a complete document from template."""
    print("=== Generating Document ===")
    
    latex_tools = LaTeXTemplateTools()
    
    # Document data
    document_data = {
        "REPORT_NUMBER": "REP-2024-001",
        "REPORT_TITLE": "Advanced Persistent Threat Analysis Report",
        "AUTHOR_NAME": "Security Analyst Team",
        "REPORT_DATE": datetime.now().strftime("%Y-%m-%d"),
        "CAMPAIGN_NAME": "APT-2024-001",
        "TOTAL_SESSIONS": "150",
        "MCP_VERSION": "1.0.0"
    }
    
    # Generate document in TEX format (no LaTeX compilation required)
    result = await latex_tools.generate_document(
        template_name="Attack_Report",
        document_data=document_data,
        output_format="tex",
        include_assets=True
    )
    
    if result["success"]:
        document = result["document"]
        print(f"Document generated successfully!")
        print(f"Template: {document['template_name']}")
        print(f"Output format: {document['output_format']}")
        print(f"Generated files: {len(document['generated_files'])}")
        print(f"Variables used: {document['metadata']['variables_used']}")
        print(f"Total sections: {document['metadata']['total_sections']}")
        print(f"Generated at: {document['metadata']['generated_at']}")
        
        print("\nGenerated files:")
        for file_path in document["generated_files"]:
            print(f"  - {file_path}")
    else:
        print(f"Error: {result['error']}")


async def example_generate_pdf_document() -> None:
    """Example: Generate a PDF document (requires LaTeX installation)."""
    print("=== Generating PDF Document ===")
    
    latex_tools = LaTeXTemplateTools()
    
    # Document data
    document_data = {
        "REPORT_NUMBER": "REP-2024-002",
        "REPORT_TITLE": "Malware Campaign Analysis Report",
        "AUTHOR_NAME": "Threat Intelligence Team",
        "REPORT_DATE": datetime.now().strftime("%Y-%m-%d"),
        "CAMPAIGN_NAME": "MALWARE-2024-001",
        "TOTAL_SESSIONS": "75",
        "MCP_VERSION": "1.0.0"
    }
    
    # Generate PDF document
    result = await latex_tools.generate_document(
        template_name="Attack_Report",
        document_data=document_data,
        output_format="pdf",
        include_assets=True,
        compile_options={
            "quiet": False,
            "shell_escape": False
        }
    )
    
    if result["success"]:
        document = result["document"]
        print(f"PDF document generated successfully!")
        print(f"Template: {document['template_name']}")
        print(f"Output format: {document['output_format']}")
        
        if "output_files" in document:
            print("\nOutput files:")
            for file_type, file_path in document["output_files"].items():
                print(f"  - {file_type}: {file_path}")
        
        if "compilation_log" in document:
            print(f"\nCompilation log length: {len(document['compilation_log'])} characters")
    else:
        print(f"Error: {result['error']}")
        print("Note: PDF generation requires LaTeX (pdflatex) to be installed.")


async def example_complete_workflow() -> None:
    """Example: Complete workflow from template discovery to document generation."""
    print("=== Complete Workflow Example ===")
    
    latex_tools = LaTeXTemplateTools()
    
    # Step 1: List available templates
    print("1. Discovering available templates...")
    templates_result = await latex_tools.list_available_templates()
    
    if not templates_result["success"]:
        print(f"Error listing templates: {templates_result['error']}")
        return
    
    template_name = templates_result["templates"][0]["name"]
    print(f"   Using template: {template_name}")
    
    # Step 2: Get template schema
    print("2. Getting template schema...")
    schema_result = await latex_tools.get_template_schema(template_name)
    
    if not schema_result["success"]:
        print(f"Error getting schema: {schema_result['error']}")
        return
    
    schema = schema_result["schema"]
    print(f"   Template: {schema['template_name']} v{schema['version']}")
    
    # Step 3: Prepare document data
    print("3. Preparing document data...")
    document_data = {}
    
    # Use example data as a starting point
    for var, value in schema["example_data"].items():
        if "REPORT" in var and "NUMBER" in var:
            document_data[var] = f"REP-{datetime.now().strftime('%Y%m%d')}-001"
        elif "REPORT" in var and "DATE" in var:
            document_data[var] = datetime.now().strftime("%Y-%m-%d")
        elif "AUTHOR" in var:
            document_data[var] = "AI-Assisted Security Analyst"
        elif "TITLE" in var:
            document_data[var] = "Automated Threat Analysis Report"
        else:
            document_data[var] = value
    
    print(f"   Prepared {len(document_data)} variables")
    
    # Step 4: Validate document data
    print("4. Validating document data...")
    validation_result = await latex_tools.validate_document_data(template_name, document_data)
    
    if not validation_result["success"]:
        print(f"Error validating data: {validation_result['error']}")
        return
    
    validation = validation_result["validation"]
    if not validation["valid"]:
        print("   Validation failed:")
        for error in validation["errors"]:
            print(f"     - {error}")
        return
    
    print("   Document data is valid!")
    
    # Step 5: Generate document
    print("5. Generating document...")
    generation_result = await latex_tools.generate_document(
        template_name=template_name,
        document_data=document_data,
        output_format="tex",  # Use TEX format for demo
        include_assets=True
    )
    
    if generation_result["success"]:
        document = generation_result["document"]
        print(f"   Document generated successfully!")
        print(f"   Template: {document['template_name']}")
        print(f"   Format: {document['output_format']}")
        print(f"   Files: {len(document['generated_files'])}")
        print(f"   Generated at: {document['metadata']['generated_at']}")
    else:
        print(f"Error generating document: {generation_result['error']}")


async def main() -> None:
    """Run all examples."""
    print("LaTeX Template Automation MCP Tools - Examples")
    print("=" * 50)
    
    try:
        await example_list_templates()
        print()
        
        await example_get_template_schema()
        print()
        
        await example_validate_document_data()
        print()
        
        await example_generate_document()
        print()
        
        # Uncomment to test PDF generation (requires LaTeX installation)
        # await example_generate_pdf_document()
        # print()
        
        await example_complete_workflow()
        print()
        
    except Exception as e:
        print(f"Error running examples: {e}")


if __name__ == "__main__":
    asyncio.run(main()) 