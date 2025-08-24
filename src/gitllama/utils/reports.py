"""
Enhanced Report Generator for GitLlama
Shows prompts with color-coded variables and side-by-side responses
"""

import logging
import webbrowser
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from ..utils.context_tracker import context_tracker
from .. import __version__

logger = logging.getLogger(__name__)

try:
    from jinja2 import Template
    REPORT_DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    REPORT_DEPENDENCIES_AVAILABLE = False
    logger.warning(f"Report generation dependencies not available: {e}")


class ReportGenerator:
    """Generates professional HTML reports with color-coded context visibility"""
    
    def __init__(self, repo_url: str, output_dir: str = "gitllama_reports"):
        self.repo_url = repo_url
        self.output_dir = Path(output_dir)
        self.start_time = datetime.now()
        self.timestamp = self.start_time.strftime("%Y%m%d_%H%M%S")
        
        # Basic tracking structures
        self.executive_summary = {}
        self.file_operations = []
        self.metrics = {}
        
        # Create output directory
        self.output_dir.mkdir(exist_ok=True)
        
        logger.info(f"ReportGenerator initialized for {repo_url}")
    
    def set_executive_summary(self, repo_path: str, branch: str, modified_files: List[str], 
                            commit_hash: str, success: bool, total_decisions: int):
        """Set the executive summary data"""
        total_workflow_time = (datetime.now() - self.start_time).total_seconds()
        
        self.executive_summary = {
            "repo_url": self.repo_url,
            "repo_path": repo_path,
            "branch_selected": branch,
            "files_modified": modified_files,
            "commit_hash": commit_hash,
            "success": success,
            "total_ai_decisions": total_decisions,
            "execution_time": total_workflow_time,
        }
        logger.debug("Set executive summary data")
    
    def set_model_info(self, model: str, context_window: int, total_tokens: int):
        """Set model information"""
        self.metrics["model_info"] = {
            "model": model,
            "context_window": context_window,
            "total_tokens": total_tokens
        }
    
    def _extract_congress_summary(self, context_data: Dict) -> Optional[Dict]:
        """Extract Congress voting summary from context tracking data"""
        congress_decisions = []
        
        # Look through all stages for congress data
        for stage in context_data.get('stages', []):
            # Check variables for congress data
            for var_name, var_data in stage.get('variables', {}).items():
                if 'congress' in var_name.lower():
                    try:
                        # Parse the congress data (it might be JSON string)
                        content = var_data.get('content', '')
                        if isinstance(content, str) and content.startswith('{'):
                            import json
                            congress_data = json.loads(content)
                        else:
                            congress_data = var_data.get('content', {})
                        
                        if isinstance(congress_data, dict) and congress_data.get('vote_details'):
                            congress_decisions.append(congress_data)
                    except Exception as e:
                        logger.debug(f"Could not parse congress data from {var_name}: {e}")
                        continue
            
            # Also check in prompt-response pairs for inline congress data
            for pair in stage.get('prompt_response_pairs', []):
                variables_used = pair.get('variables_used', {})
                for var_name, var_content in variables_used.items():
                    if 'congress' in var_name.lower() and isinstance(var_content, dict):
                        if var_content.get('vote_details'):
                            congress_decisions.append(var_content)
        
        if not congress_decisions:
            return None
        
        # Aggregate the congress data
        total_votes = len(congress_decisions)
        approved = sum(1 for d in congress_decisions if d.get('approved'))
        rejected = total_votes - approved
        unanimous_decisions = sum(1 for d in congress_decisions if d.get('unanimous'))
        unanimity_rate = unanimous_decisions / total_votes if total_votes > 0 else 0
        
        # Aggregate by representative
        rep_votes = {}
        for decision in congress_decisions:
            vote_details = decision.get('vote_details', [])
            for vote in vote_details:
                rep_name = vote.get('name', 'Unknown')
                if rep_name not in rep_votes:
                    rep_votes[rep_name] = {'yes': 0, 'no': 0}
                
                if vote.get('vote'):
                    rep_votes[rep_name]['yes'] += 1
                else:
                    rep_votes[rep_name]['no'] += 1
        
        return {
            "total_votes": total_votes,
            "approved": approved,
            "rejected": rejected,
            "unanimity_rate": unanimity_rate,
            "by_representative": rep_votes
        }
    
    def _generate_color_for_variable(self, var_name: str) -> str:
        """Generate a consistent color for a variable name"""
        # Use hash to generate consistent colors
        hash_val = hashlib.md5(var_name.encode()).hexdigest()
        
        # Define a palette of distinct colors
        colors = [
            '#e74c3c',  # Red
            '#3498db',  # Blue
            '#2ecc71',  # Green
            '#f39c12',  # Orange
            '#9b59b6',  # Purple
            '#1abc9c',  # Turquoise
            '#e67e22',  # Carrot
            '#16a085',  # Green Sea
            '#8e44ad',  # Wisteria
            '#d35400',  # Pumpkin
            '#27ae60',  # Nephritis
            '#2980b9',  # Belize Blue
            '#c0392b',  # Pomegranate
            '#7f8c8d',  # Asbestos
            '#34495e',  # Wet Asphalt
        ]
        
        # Pick color based on hash
        color_index = int(hash_val[:2], 16) % len(colors)
        return colors[color_index]
    
    def _format_prompt_with_variables(self, prompt: str, variables: Dict[str, str]) -> str:
        """Format a prompt with color-coded variable highlights"""
        if not variables:
            return self._escape_html(prompt)
        
        formatted = prompt
        replacements = []
        
        # Sort variables by length (longest first) to avoid partial replacements
        sorted_vars = sorted(variables.items(), key=lambda x: len(str(x[1])) if x[1] else 0, reverse=True)
        
        for var_name, var_content in sorted_vars:
            # Only process string variables that might be in the prompt
            if var_content and isinstance(var_content, str) and var_content in prompt:
                color = self._generate_color_for_variable(var_name)
                # Create a unique placeholder to avoid re-replacement
                placeholder = f"___VAR_{var_name}_{hash(var_content)}___"
                formatted = formatted.replace(var_content, placeholder)
                
                # Escape the content for HTML
                escaped_content = self._escape_html(var_content)
                
                # Create the colored span with tooltip
                replacement = f'''<span class="variable-highlight" 
                    style="background-color: {color}20; border-bottom: 2px solid {color}; 
                           padding: 2px 4px; border-radius: 3px; position: relative; cursor: help;"
                    data-variable="{var_name}"
                    title="{var_name}">
                    {escaped_content}
                    <span class="variable-label" style="position: absolute; top: -20px; left: 0; 
                          background: {color}; color: white; padding: 2px 6px; 
                          border-radius: 3px; font-size: 0.7rem; white-space: nowrap;
                          opacity: 0; transition: opacity 0.2s; pointer-events: none;">
                        {var_name}
                    </span>
                </span>'''
                
                replacements.append((placeholder, replacement))
        
        # Escape any remaining text
        formatted = self._escape_html(formatted)
        
        # Now replace all placeholders with formatted HTML
        for placeholder, replacement in replacements:
            formatted = formatted.replace(placeholder, replacement)
        
        return formatted
    
    def _escape_html(self, text: str) -> str:
        """Escape HTML characters"""
        return (text.replace('&', '&amp;')
                   .replace('<', '&lt;')
                   .replace('>', '&gt;')
                   .replace('"', '&quot;')
                   .replace("'", '&#x27;'))
    
    def generate_report(self, auto_open: bool = True) -> Path:
        """Generate the enhanced HTML report with color-coded variables"""
        if not REPORT_DEPENDENCIES_AVAILABLE:
            logger.error("Cannot generate report: missing dependencies (jinja2)")
            return self._generate_fallback_report()
        
        logger.info("Generating enhanced HTML report with color-coded variables...")
        
        # Get all tracked context data
        context_data = context_tracker.export_for_report()
        
        # Extract Congress summary from stored context data
        congress_summary = self._extract_congress_summary(context_data)
        
        # Prepare template data
        template_data = {
            "timestamp": self.timestamp,
            "generation_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "executive_summary": self.executive_summary,
            "context_tracking": context_data,
            "metrics": self.metrics,
            "congress_summary": congress_summary,
            "gitllama_version": __version__,
            "format_prompt": self._format_prompt_with_variables,
            "generate_color": self._generate_color_for_variable,
            "escape_html": self._escape_html
        }
        
        # Generate HTML
        html_content = self._render_enhanced_html_template(template_data)
        
        # Save HTML report
        html_filename = f"gitllama_report_{self.timestamp}.html"
        html_path = self.output_dir / html_filename
        
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Save as latest
        latest_path = self.output_dir / "latest.html"
        with open(latest_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"Report generated: {html_path}")
        
        # Auto-open in browser
        if auto_open:
            try:
                webbrowser.open(f'file://{html_path.absolute()}')
                logger.info("Report opened in browser")
            except Exception as e:
                logger.warning(f"Could not auto-open report: {e}")
        
        return html_path
    
    def _render_enhanced_html_template(self, data: Dict[str, Any]) -> str:
        """Render the enhanced HTML template"""
        template = Template(self._get_enhanced_html_template())
        return template.render(**data)
    
    def _get_enhanced_html_template(self) -> str:
        """Get the enhanced HTML template with color-coded variables"""
        return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GitLlama Context Report - {{ timestamp }}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6; color: #333; background: #f5f7fa;
        }
        .container { max-width: 1600px; margin: 0 auto; padding: 20px; }
        
        /* Header */
        .header { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; padding: 2rem; border-radius: 12px; margin-bottom: 2rem;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        }
        .header h1 { font-size: 2.5rem; margin-bottom: 0.5rem; }
        .header p { opacity: 0.9; font-size: 1.1rem; }
        
        /* Section styling */
        .section { 
            background: white; padding: 2rem; margin-bottom: 1.5rem; 
            border-radius: 12px; box-shadow: 0 4px 16px rgba(0,0,0,0.05);
        }
        .section h2 { 
            color: #2d3748; border-bottom: 3px solid #667eea; 
            padding-bottom: 0.5rem; margin-bottom: 1.5rem; font-size: 1.8rem;
        }
        
        /* Stats */
        .context-stats {
            display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 1rem; margin-bottom: 2rem;
        }
        .stat-card {
            background: #f8fafc; padding: 1rem; border-radius: 8px;
            border-left: 4px solid #667eea; text-align: center;
        }
        .stat-value { font-size: 1.8rem; font-weight: bold; color: #667eea; }
        .stat-label { color: #64748b; text-transform: uppercase; font-size: 0.8rem; }
        
        /* Stage navigation */
        .stage-nav {
            display: flex; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 2rem;
            padding: 1rem; background: #f8fafc; border-radius: 8px;
        }
        .stage-tab {
            padding: 0.5rem 1rem; background: white; border: 2px solid #e2e8f0;
            border-radius: 6px; cursor: pointer; transition: all 0.2s;
            font-weight: 600; color: #475569;
        }
        .stage-tab:hover { border-color: #667eea; background: #f0f4ff; }
        .stage-tab.active { 
            background: #667eea; color: white; border-color: #667eea;
        }
        
        /* Stage content */
        .stage-content {
            display: none; animation: fadeIn 0.3s;
        }
        .stage-content.active { display: block; }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        /* Prompt-Response Pairs */
        .prompt-response-pair {
            background: white; border: 1px solid #e2e8f0; border-radius: 12px;
            margin-bottom: 2rem; overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }
        .pair-header {
            background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
            padding: 1rem 1.5rem; border-bottom: 2px solid #e2e8f0;
            display: flex; justify-content: space-between; align-items: center;
        }
        .pair-number {
            font-weight: 700; color: #1a202c; font-size: 1.1rem;
        }
        .pair-meta {
            display: flex; gap: 1rem; align-items: center;
            font-size: 0.9rem; color: #64748b;
        }
        
        /* Congress vote in metrics bar */
        .congress-vote-summary {
            position: relative; cursor: help;
            padding: 0.25rem 0.5rem; border-radius: 4px;
            background: rgba(251, 191, 36, 0.1);
        }
        .vote-result.approved { color: #22c55e; font-weight: 600; }
        .vote-result.rejected { color: #ef4444; font-weight: 600; }
        .vote-details-tooltip {
            position: absolute; top: -10px; left: 50%;
            transform: translateX(-50%) translateY(-100%);
            background: #374151; color: white; padding: 1rem;
            border-radius: 8px; font-size: 0.85rem; white-space: nowrap;
            z-index: 1000; opacity: 0; visibility: hidden; 
            transition: opacity 0.2s, visibility 0.2s;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            min-width: 240px; white-space: normal;
        }
        .congress-vote-summary:hover .vote-details-tooltip {
            opacity: 1; visibility: visible;
        }
        .vote-details-tooltip::after {
            content: ''; position: absolute; top: 100%; left: 50%;
            transform: translateX(-50%); border: 8px solid transparent;
            border-top-color: #374151;
        }
        .vote-line {
            display: flex; justify-content: space-between; align-items: center;
            margin-bottom: 0.5rem; padding: 0.25rem 0;
        }
        .rep-name { font-weight: 500; }
        .vote-symbol-small {
            display: inline-block; width: 16px; height: 16px;
            border-radius: 50%; text-align: center; line-height: 16px;
            font-size: 0.7rem; font-weight: bold; margin: 0 0.5rem;
        }
        .vote-symbol-small.vote-yes { background: #22c55e; color: white; }
        .vote-symbol-small.vote-no { background: #ef4444; color: white; }
        .confidence { color: #9ca3af; font-size: 0.8rem; }
        .verdict { 
            margin-top: 0.75rem; padding-top: 0.5rem; 
            border-top: 1px solid #4b5563; text-align: center; 
        }
        
        /* Variable legend */
        .variable-legend {
            background: #f8fafc; padding: 1rem; border-radius: 8px;
            margin-bottom: 1rem; border: 1px solid #e2e8f0;
        }
        .variable-legend h4 {
            margin-bottom: 0.5rem; color: #374151; font-size: 0.9rem;
            text-transform: uppercase; letter-spacing: 0.5px;
        }
        .legend-items {
            display: flex; flex-wrap: wrap; gap: 0.75rem;
        }
        .legend-item {
            display: flex; align-items: center; gap: 0.5rem;
            padding: 0.25rem 0.75rem; background: white;
            border-radius: 20px; font-size: 0.85rem;
            border: 1px solid #e2e8f0;
        }
        .legend-color {
            width: 16px; height: 16px; border-radius: 3px;
            border: 1px solid rgba(0,0,0,0.1);
        }
        
        /* Prompt and Response containers */
        .pair-content {
            display: grid; grid-template-columns: 1fr 1fr; gap: 0;
        }
        
        .prompt-container, .response-container {
            padding: 1.5rem; position: relative;
        }
        
        .prompt-container {
            background: linear-gradient(135deg, #f0f4ff 0%, #e8ecff 100%);
            border-right: 2px solid #e2e8f0;
        }
        
        .response-container {
            background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
        }
        
        .container-header {
            font-weight: 700; color: #374151; margin-bottom: 1rem;
            display: flex; align-items: center; gap: 0.5rem;
            font-size: 1rem; text-transform: uppercase; letter-spacing: 0.5px;
        }
        
        .prompt-content, .response-content {
            background: white; padding: 1rem; border-radius: 8px;
            font-family: 'Monaco', 'Menlo', monospace; font-size: 0.85rem;
            line-height: 1.6; white-space: pre-wrap; word-wrap: break-word;
            max-height: 600px; overflow-y: auto;
            border: 1px solid rgba(0,0,0,0.05);
            box-shadow: inset 0 1px 3px rgba(0,0,0,0.05);
        }
        
        /* Variable highlighting */
        .variable-highlight {
            position: relative; display: inline-block;
            transition: all 0.2s;
        }
        .variable-highlight:hover {
            transform: translateY(-1px);
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .variable-highlight:hover .variable-label {
            opacity: 1 !important;
        }
        
        /* Expand/Collapse buttons */
        .expand-btn {
            position: absolute; top: 1rem; right: 1rem;
            background: rgba(255,255,255,0.8); border: 1px solid #e2e8f0;
            padding: 0.25rem 0.5rem; border-radius: 4px;
            cursor: pointer; font-size: 0.75rem; font-weight: 600;
            color: #4b5563; transition: all 0.2s;
        }
        .expand-btn:hover {
            background: white; border-color: #667eea; color: #667eea;
        }
        
        /* Copy button */
        .copy-btn {
            position: absolute; bottom: 1rem; right: 1rem;
            background: rgba(255,255,255,0.9); border: 1px solid #e2e8f0;
            padding: 0.25rem 0.75rem; border-radius: 4px;
            cursor: pointer; font-size: 0.75rem; font-weight: 600;
            color: #4b5563; transition: all 0.2s;
        }
        .copy-btn:hover {
            background: white; border-color: #667eea; color: #667eea;
        }
        .copy-btn.copied {
            background: #10b981; color: white; border-color: #10b981;
        }
        
        /* Congress voting section */
        .congress-inline {
            display: inline-flex; align-items: center; gap: 0.5rem;
            margin-left: 1rem; padding: 0.25rem 0.5rem;
            background: rgba(251, 191, 36, 0.1); border-radius: 4px;
            border: 1px solid #fbbf24;
        }
        .congress-votes-inline {
            display: flex; gap: 0.25rem;
        }
        .vote-symbol {
            display: inline-block; width: 20px; height: 20px;
            border-radius: 50%; text-align: center; line-height: 20px;
            font-size: 0.8rem; font-weight: bold; cursor: help;
            position: relative;
        }
        .vote-yes {
            background: #22c55e; color: white;
        }
        .vote-no {
            background: #ef4444; color: white;
        }
        .vote-tooltip {
            position: absolute; bottom: 25px; left: 50%;
            transform: translateX(-50%); background: #374151;
            color: white; padding: 0.75rem; border-radius: 6px;
            font-size: 0.75rem; white-space: nowrap; z-index: 1000;
            opacity: 0; visibility: hidden; transition: all 0.2s;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            max-width: 300px; white-space: normal;
        }
        .vote-symbol:hover .vote-tooltip {
            opacity: 1; visibility: visible;
        }
        .vote-tooltip::after {
            content: ''; position: absolute; top: 100%; left: 50%;
            transform: translateX(-50%); border: 5px solid transparent;
            border-top-color: #374151;
        }
        .congress-verdict-inline {
            font-size: 0.85rem; font-weight: 600;
            padding: 0.125rem 0.5rem; border-radius: 3px;
        }
        .verdict-approved {
            background: #dcfce7; color: #166534;
        }
        .verdict-rejected {
            background: #fee2e2; color: #991b1b;
        }
        
        /* Footer */
        .footer { 
            text-align: center; padding: 2rem; color: #64748b; 
            margin-top: 3rem;
        }
        
        /* Scrollbar styling */
        .prompt-content::-webkit-scrollbar,
        .response-content::-webkit-scrollbar {
            width: 8px; height: 8px;
        }
        .prompt-content::-webkit-scrollbar-track,
        .response-content::-webkit-scrollbar-track {
            background: #f1f5f9; border-radius: 4px;
        }
        .prompt-content::-webkit-scrollbar-thumb,
        .response-content::-webkit-scrollbar-thumb {
            background: #cbd5e1; border-radius: 4px;
        }
        .prompt-content::-webkit-scrollbar-thumb:hover,
        .response-content::-webkit-scrollbar-thumb:hover {
            background: #94a3b8;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🦙 GitLlama Context Report</h1>
            <p>AI Prompts with Color-Coded Variables • {{ generation_time }}</p>
            <p>Repository: {{ executive_summary.repo_url }}</p>
            <div style="margin-top: 0.5rem; opacity: 0.8; font-size: 0.9rem;">
                <span style="background: rgba(255,255,255,0.2); padding: 0.25rem 0.5rem; border-radius: 4px;">
                    Version {{ gitllama_version }}
                </span>
            </div>
        </div>

        <!-- Executive Summary -->
        <div class="section">
            <h2>📊 Executive Summary</h2>
            <div class="context-stats">
                <div class="stat-card">
                    <div class="stat-value">{{ context_tracking.stats.num_stages }}</div>
                    <div class="stat-label">Stages</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{{ context_tracking.stats.total_variables }}</div>
                    <div class="stat-label">Variables</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{{ context_tracking.stats.total_pairs }}</div>
                    <div class="stat-label">AI Exchanges</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{{ (context_tracking.stats.total_data_size / 1024)|round(1) }}KB</div>
                    <div class="stat-label">Data Size</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{{ executive_summary.execution_time|round(1) }}s</div>
                    <div class="stat-label">Runtime</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{% if executive_summary.success %}✅{% else %}❌{% endif %}</div>
                    <div class="stat-label">Status</div>
                </div>
            </div>
        </div>
        
        <!-- Congress Summary (if available) -->
        {% if congress_summary %}
        <div class="section">
            <h2>🏛️ Congressional Oversight Summary</h2>
            <div class="context-stats">
                <div class="stat-card">
                    <div class="stat-value">{{ congress_summary.total_votes }}</div>
                    <div class="stat-label">Total Votes</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{{ congress_summary.approved }}</div>
                    <div class="stat-label">Approved</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{{ congress_summary.rejected }}</div>
                    <div class="stat-label">Rejected</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{{ (congress_summary.unanimity_rate * 100)|round(0) }}%</div>
                    <div class="stat-label">Unanimity</div>
                </div>
            </div>
            {% if congress_summary.by_representative %}
            <div style="margin-top: 1rem;">
                <h3 style="color: #374151; font-size: 1.2rem; margin-bottom: 0.75rem;">Representative Voting Patterns</h3>
                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem;">
                    {% for rep_name, votes in congress_summary.by_representative.items() %}
                    <div style="background: #f8fafc; padding: 1rem; border-radius: 6px; border-left: 4px solid #f59e0b;">
                        <div style="font-weight: 600; color: #374151;">{{ rep_name }}</div>
                        <div style="font-size: 0.9rem; color: #6b7280; margin-top: 0.25rem;">
                            ✅ {{ votes.yes }} Yes • ❌ {{ votes.no }} No
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>
            {% endif %}
        </div>
        {% endif %}

        <!-- AI Context Exchanges -->
        <div class="section">
            <h2>🧠 AI Context Exchanges</h2>
            
            <!-- Stage Navigation -->
            <div class="stage-nav">
                {% for stage in context_tracking.stages %}
                <div class="stage-tab {% if loop.first %}active{% endif %}" 
                     onclick="showStage('{{ stage.stage_name }}', this)">
                    {{ stage.stage_name }}
                    <span style="background: rgba(102,126,234,0.2); padding: 2px 6px; border-radius: 4px; margin-left: 4px; font-size: 0.8rem;">
                        {{ stage.num_pairs }}
                    </span>
                </div>
                {% endfor %}
            </div>
            
            <!-- Stage Contents -->
            {% for stage in context_tracking.stages %}
            <div class="stage-content {% if loop.first %}active{% endif %}" id="stage-{{ stage.stage_name }}">
                <h3 style="margin-bottom: 1.5rem; color: #374151;">
                    📍 Stage: {{ stage.stage_name }}
                    <span style="font-size: 0.9rem; color: #6b7280; font-weight: normal; margin-left: 1rem;">
                        {{ stage.num_pairs }} exchanges • {{ stage.num_variables }} variables
                    </span>
                </h3>
                
                <!-- Variable Legend for this stage -->
                {% if stage.variables %}
                <div class="variable-legend">
                    <h4>📦 Variables Used in This Stage</h4>
                    <div class="legend-items">
                        {% for var_name, var_data in stage.variables.items() %}
                        <div class="legend-item">
                            <div class="legend-color" style="background: {{ generate_color(var_name) }};"></div>
                            <span style="font-weight: 600;">{{ var_name }}</span>
                            <span style="color: #6b7280;">({{ var_data.size }} chars)</span>
                        </div>
                        {% endfor %}
                    </div>
                </div>
                {% endif %}
                
                <!-- Prompt-Response Pairs -->
                {% for pair in stage.prompt_response_pairs %}
                <!-- Find Congress variable for this pair -->
                {% set ns = namespace(congress_var=None) %}
                {% for var_name, var_data in pair.variables_used.items() %}
                    {% if var_name.endswith('_congress') and var_data.get('vote_details') and ns.congress_var is none %}
                        {% set ns.congress_var = var_data %}
                    {% endif %}
                {% endfor %}
                {% set congress_var = ns.congress_var %}
                <div class="prompt-response-pair">
                    <div class="pair-header">
                        <div class="pair-number">
                            Exchange #{{ loop.index }}
                            <!-- Congress Voting Inline -->
                            {% if congress_var %}
                            <div class="congress-inline">
                                <span>🏛️</span>
                                <div class="congress-votes-inline">
                                    {% for vote_detail in congress_var.get('vote_details', []) %}
                                    <div class="vote-symbol {% if vote_detail.get('vote') %}vote-yes{% else %}vote-no{% endif %}">
                                        {% if vote_detail.get('vote') %}✓{% else %}✗{% endif %}
                                        <div class="vote-tooltip">
                                            <strong>{{ vote_detail.get('name', 'Unknown') }}</strong><br>
                                            {{ vote_detail.get('title', 'Representative') }}<br><br>
                                            <strong>Vote:</strong> {% if vote_detail.get('vote') %}YES{% else %}NO{% endif %}<br>
                                            <strong>Confidence:</strong> {{ (vote_detail.get('confidence', 0) * 100)|round }}%<br>
                                            <strong>Reasoning:</strong> {{ vote_detail.get('reasoning', 'No reason provided') }}
                                        </div>
                                    </div>
                                    {% endfor %}
                                </div>
                                <span class="congress-verdict-inline {% if congress_var.get('approved') %}verdict-approved{% else %}verdict-rejected{% endif %}">
                                    {{ congress_var.get('votes', '0-0') }}
                                </span>
                            </div>
                            {% endif %}
                        </div>
                        <div class="pair-meta">
                            <span>⏱️ {% if pair.timestamp %}{{ pair.timestamp.split('T')[1].split('.')[0] if 'T' in pair.timestamp else pair.timestamp }}{% else %}--:--:--{% endif %}</span>
                            <span>📝 {{ pair.prompt_size }} chars prompt</span>
                            <span>💬 {{ pair.response_size }} chars response</span>
                            {% if congress_var %}
                            <span class="congress-vote-summary" title="Congressional Vote Results">
                                🏛️ <span class="vote-result {% if congress_var.get('approved') %}approved{% else %}rejected{% endif %}">
                                    {{ congress_var.get('votes', '0-0') }}
                                </span>
                                <div class="vote-details-tooltip">
                                    <strong>Congressional Votes:</strong><br>
                                    {% for vote_detail in congress_var.get('vote_details', []) %}
                                    <div class="vote-line">
                                        <span class="rep-name">{{ vote_detail.get('name', 'Unknown') }}:</span>
                                        <span class="vote-symbol-small {% if vote_detail.get('vote') %}vote-yes{% else %}vote-no{% endif %}">
                                            {% if vote_detail.get('vote') %}✓{% else %}✗{% endif %}
                                        </span>
                                        <span class="confidence">({{ (vote_detail.get('confidence', 0) * 100)|round }}%)</span>
                                    </div>
                                    {% endfor %}
                                    <div class="verdict">
                                        <strong>Result: {% if congress_var.get('approved') %}APPROVED{% else %}REJECTED{% endif %}</strong>
                                    </div>
                                </div>
                            </span>
                            {% endif %}
                        </div>
                    </div>
                    
                    <div class="pair-content">
                        <!-- Prompt Side -->
                        <div class="prompt-container">
                            <div class="container-header">
                                <span>🤖</span> PROMPT TO AI
                            </div>
                            <div class="prompt-content" id="prompt-{{ stage.stage_name }}-{{ loop.index }}">{{ format_prompt(pair.prompt, pair.variables_used)|safe }}</div>
                            <button class="copy-btn" onclick="copyText('prompt-{{ stage.stage_name }}-{{ loop.index }}', this)">
                                📋 Copy
                            </button>
                        </div>
                        
                        <!-- Response Side -->
                        <div class="response-container">
                            <div class="container-header">
                                <span>✨</span> AI RESPONSE
                            </div>
                            <div class="response-content" id="response-{{ stage.stage_name }}-{{ loop.index }}">{{ escape_html(pair.response) }}</div>
                            <button class="copy-btn" onclick="copyText('response-{{ stage.stage_name }}-{{ loop.index }}', this)">
                                📋 Copy
                            </button>
                        </div>
                    </div>
                    
                </div>
                {% endfor %}
                
                <!-- Fallback for stages without pairs -->
                {% if not stage.prompt_response_pairs %}
                <div style="padding: 2rem; text-align: center; color: #6b7280;">
                    <p>No prompt-response pairs recorded for this stage.</p>
                    {% if stage.prompts %}
                    <p style="margin-top: 0.5rem;">{{ stage.num_prompts }} prompts and {{ stage.num_responses }} responses were recorded separately.</p>
                    {% endif %}
                </div>
                {% endif %}
            </div>
            {% endfor %}
        </div>

        <div class="footer">
            <p>Generated by GitLlama v{{ gitllama_version }} • {{ generation_time }}</p>
            <p>🦙 Complete Context Transparency with Color-Coded Variables</p>
        </div>
    </div>

    <script>
        function showStage(stageName, tabElement) {
            // Hide all stages
            document.querySelectorAll('.stage-content').forEach(content => {
                content.classList.remove('active');
            });
            
            // Remove active from all tabs
            document.querySelectorAll('.stage-tab').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // Show selected stage
            document.getElementById('stage-' + stageName).classList.add('active');
            tabElement.classList.add('active');
        }
        
        function copyText(elementId, button) {
            const element = document.getElementById(elementId);
            const text = element.innerText || element.textContent;
            
            navigator.clipboard.writeText(text).then(() => {
                // Change button to show success
                const originalText = button.innerHTML;
                button.innerHTML = '✅ Copied!';
                button.classList.add('copied');
                
                // Reset after 2 seconds
                setTimeout(() => {
                    button.innerHTML = originalText;
                    button.classList.remove('copied');
                }, 2000);
            }).catch(err => {
                console.error('Failed to copy:', err);
            });
        }
        
        function toggleExpand(elementId, button) {
            const element = document.getElementById(elementId);
            if (element.style.maxHeight === 'none') {
                element.style.maxHeight = '600px';
                button.textContent = 'Expand';
            } else {
                element.style.maxHeight = 'none';
                button.textContent = 'Collapse';
            }
        }
    </script>
</body>
</html>'''
    
    def _generate_fallback_report(self) -> Path:
        """Generate simple text report when dependencies are missing"""
        lines = [
            "GitLlama Context Report",
            "=" * 50,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "Install jinja2 for full HTML report: pip install jinja2",
        ]
        
        txt_path = self.output_dir / f"report_{self.timestamp}.txt"
        with open(txt_path, 'w') as f:
            f.write('\n'.join(lines))
        
        return txt_path