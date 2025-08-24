"""
Enhanced Report Generator for GitLlama
Displays all tracked context variables beautifully
"""

import logging
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from ..utils.context_tracker import context_tracker
from .. import __version__

try:
    from jinja2 import Template
    from pygments import highlight
    from pygments.lexers import get_lexer_by_name, guess_lexer, JsonLexer, PythonLexer, TextLexer
    from pygments.formatters import HtmlFormatter
    from pygments.util import ClassNotFound
    REPORT_DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    REPORT_DEPENDENCIES_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning(f"Report generation dependencies not available: {e}")

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generates professional HTML reports with full context visibility"""
    
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
    
    def add_file_operation(self, operation: str, file_path: str, reason: str, content: str = ""):
        """Add a file operation"""
        self.file_operations.append({
            "timestamp": datetime.now(),
            "operation": operation,
            "file_path": file_path,
            "reason": reason,
            "content": content
        })
    
    def _highlight_variable_content(self, content: str, var_type: str = "text") -> str:
        """Apply syntax highlighting to variable content based on type"""
        if not REPORT_DEPENDENCIES_AVAILABLE:
            return f'<pre style="background: #f8f8f8; padding: 10px; border-radius: 4px;">{self._escape_html(content)}</pre>'
        
        try:
            # Determine lexer based on content type
            if var_type == "dict" or var_type == "list" or content.strip().startswith('{') or content.strip().startswith('['):
                lexer = JsonLexer()
            elif var_type == "python" or '.py' in content[:100]:
                lexer = PythonLexer()
            else:
                lexer = TextLexer()
            
            formatter = HtmlFormatter(style='github', cssclass='highlight', noclasses=True)
            return highlight(content, lexer, formatter)
        except Exception as e:
            logger.debug(f"Syntax highlighting failed: {e}")
            return f'<pre style="background: #f8f8f8; padding: 10px; border-radius: 4px;">{self._escape_html(content)}</pre>'
    
    def _escape_html(self, text: str) -> str:
        """Escape HTML characters"""
        return (text.replace('&', '&amp;')
                   .replace('<', '&lt;')
                   .replace('>', '&gt;')
                   .replace('"', '&quot;')
                   .replace("'", '&#x27;'))
    
    def generate_report(self, auto_open: bool = True) -> Path:
        """Generate the enhanced HTML report with context tracking"""
        if not REPORT_DEPENDENCIES_AVAILABLE:
            logger.error("Cannot generate report: missing dependencies (jinja2, pygments)")
            return self._generate_fallback_report()
        
        logger.info("Generating enhanced HTML report with context tracking...")
        
        # Get all tracked context data
        context_data = context_tracker.export_for_report()
        
        # Prepare template data
        template_data = {
            "timestamp": self.timestamp,
            "generation_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "executive_summary": self.executive_summary,
            "context_tracking": context_data,
            "file_operations": self.file_operations,
            "metrics": self.metrics,
            "gitllama_version": __version__
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
        """Render the enhanced HTML template with context tracking"""
        template = Template(self._get_enhanced_html_template())
        
        # Add highlighting function to template context
        data['highlight_content'] = self._highlight_variable_content
        
        return template.render(**data)
    
    def _get_enhanced_html_template(self) -> str:
        """Get the enhanced HTML template with beautiful context display"""
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
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        
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
        
        /* Context tracking stats */
        .context-stats {
            display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1.5rem; margin-bottom: 2rem;
        }
        .stat-card {
            background: #f8fafc; padding: 1.5rem; border-radius: 8px;
            border-left: 4px solid #667eea; text-align: center;
        }
        .stat-value { font-size: 2rem; font-weight: bold; color: #667eea; }
        .stat-label { color: #64748b; text-transform: uppercase; font-size: 0.85rem; }
        
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
        
        /* Variable display */
        .variable-card {
            background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px;
            margin-bottom: 1.5rem; overflow: hidden;
        }
        .variable-header {
            background: white; padding: 1rem 1.5rem; border-bottom: 1px solid #e2e8f0;
            display: flex; justify-content: space-between; align-items: center;
        }
        .variable-name {
            font-weight: 700; color: #1a202c; font-size: 1.1rem;
            font-family: 'Monaco', monospace;
        }
        .variable-meta {
            display: flex; gap: 1rem; align-items: center;
        }
        .variable-type {
            background: #dbeafe; color: #1e40af; padding: 0.25rem 0.75rem;
            border-radius: 20px; font-size: 0.8rem; font-weight: 600;
        }
        .variable-size {
            color: #64748b; font-size: 0.9rem;
        }
        .variable-description {
            padding: 0.75rem 1.5rem; background: #f1f5f9; color: #475569;
            font-style: italic; font-size: 0.95rem;
        }
        .variable-content {
            padding: 1.5rem; max-height: 500px; overflow-y: auto;
            background: white;
        }
        .variable-content pre {
            margin: 0; font-size: 0.9rem; line-height: 1.5;
            background: #f8f8f8; padding: 1rem; border-radius: 6px;
            overflow-x: auto;
        }
        
        /* Prompt display */
        .prompt-card {
            background: linear-gradient(135deg, #f0f4ff 0%, #e8ecff 100%);
            border: 1px solid #c7d2fe; border-radius: 8px;
            margin-bottom: 1rem; padding: 1.5rem;
        }
        .prompt-header {
            font-weight: 600; color: #4338ca; margin-bottom: 0.5rem;
            display: flex; align-items: center; gap: 0.5rem;
        }
        .prompt-content {
            background: white; padding: 1rem; border-radius: 6px;
            font-family: 'Monaco', monospace; font-size: 0.9rem;
            white-space: pre-wrap; word-wrap: break-word;
            max-height: 300px; overflow-y: auto;
        }
        
        /* Response display */
        .response-card {
            background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
            border: 1px solid #86efac; border-radius: 8px;
            margin-bottom: 1rem; padding: 1.5rem;
        }
        .response-header {
            font-weight: 600; color: #166534; margin-bottom: 0.5rem;
            display: flex; align-items: center; gap: 0.5rem;
        }
        .response-content {
            background: white; padding: 1rem; border-radius: 6px;
            font-family: 'Monaco', monospace; font-size: 0.9rem;
            white-space: pre-wrap; word-wrap: break-word;
            max-height: 300px; overflow-y: auto;
        }
        
        /* Toggle buttons */
        .toggle-btn {
            background: #667eea; color: white; border: none;
            padding: 0.5rem 1rem; border-radius: 6px; cursor: pointer;
            font-weight: 600; transition: background 0.2s;
        }
        .toggle-btn:hover { background: #5a67d8; }
        
        /* Footer */
        .footer { 
            text-align: center; padding: 2rem; color: #64748b; 
            margin-top: 3rem;
        }
        
        /* Syntax highlighting overrides */
        .highlight { background: transparent !important; }
        .highlight pre { 
            background: #f8f8f8 !important; 
            padding: 1rem !important;
            border-radius: 6px !important;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🦙 GitLlama Context Report</h1>
            <p>Complete AI Context Tracking • {{ generation_time }}</p>
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
                    <div class="stat-label">Execution Stages</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{{ context_tracking.stats.total_variables }}</div>
                    <div class="stat-label">Context Variables</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{{ context_tracking.stats.total_prompts }}</div>
                    <div class="stat-label">AI Prompts</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{{ context_tracking.stats.total_responses }}</div>
                    <div class="stat-label">AI Responses</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{{ (context_tracking.stats.total_data_size / 1024)|round(1) }}KB</div>
                    <div class="stat-label">Total Data Size</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{{ executive_summary.execution_time|round(1) }}s</div>
                    <div class="stat-label">Execution Time</div>
                </div>
            </div>
            
            <p><strong>Branch:</strong> {{ executive_summary.branch_selected }}</p>
            <p><strong>Files Modified:</strong> {{ executive_summary.files_modified|length }}</p>
            <p><strong>Status:</strong> {% if executive_summary.success %}✅ Success{% else %}❌ Failed{% endif %}</p>
        </div>

        <!-- Context Tracking Details -->
        <div class="section">
            <h2>🧠 AI Context Tracking</h2>
            
            <!-- Stage Navigation -->
            <div class="stage-nav">
                {% for stage in context_tracking.stages %}
                <div class="stage-tab {% if loop.first %}active{% endif %}" 
                     onclick="showStage('{{ stage.stage_name }}', this)">
                    {{ stage.stage_name }}
                    <span style="background: rgba(102,126,234,0.2); padding: 2px 6px; border-radius: 4px; margin-left: 4px; font-size: 0.8rem;">
                        {{ stage.num_variables }}
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
                        {{ stage.timestamp }}
                    </span>
                </h3>
                
                <!-- Variables in this stage -->
                {% if stage.variables %}
                <h4 style="margin: 1.5rem 0 1rem 0; color: #4b5563;">📦 Context Variables ({{ stage.num_variables }})</h4>
                {% for var_name, var_data in stage.variables.items() %}
                <div class="variable-card">
                    <div class="variable-header">
                        <div class="variable-name">{{ var_name }}</div>
                        <div class="variable-meta">
                            <span class="variable-type">{{ var_data.type }}</span>
                            <span class="variable-size">{{ var_data.size }} chars</span>
                        </div>
                    </div>
                    {% if var_data.description %}
                    <div class="variable-description">{{ var_data.description }}</div>
                    {% endif %}
                    <div class="variable-content">
                        {{ highlight_content(var_data.content, var_data.type)|safe }}
                    </div>
                </div>
                {% endfor %}
                {% endif %}
                
                <!-- Prompts in this stage -->
                {% if stage.prompts %}
                <h4 style="margin: 2rem 0 1rem 0; color: #4b5563;">📝 AI Prompts ({{ stage.num_prompts }})</h4>
                {% for prompt in stage.prompts %}
                <div class="prompt-card">
                    <div class="prompt-header">
                        <span>🤖</span>
                        Prompt #{{ loop.index }}
                        <span style="margin-left: auto; font-size: 0.9rem; color: #6b7280;">
                            {{ prompt.combined_size }} chars
                        </span>
                    </div>
                    <div class="prompt-content">{{ prompt.prompt|truncate(2000) }}</div>
                    {% if prompt.context %}
                    <details style="margin-top: 0.5rem;">
                        <summary style="cursor: pointer; color: #4338ca; font-weight: 600;">
                            View Context ({{ prompt.context|length }} chars)
                        </summary>
                        <div class="prompt-content" style="margin-top: 0.5rem;">{{ prompt.context|truncate(2000) }}</div>
                    </details>
                    {% endif %}
                </div>
                {% endfor %}
                {% endif %}
                
                <!-- Responses in this stage -->
                {% if stage.responses %}
                <h4 style="margin: 2rem 0 1rem 0; color: #4b5563;">💬 AI Responses ({{ stage.num_responses }})</h4>
                {% for response in stage.responses %}
                <div class="response-card">
                    <div class="response-header">
                        <span>✨</span>
                        Response #{{ loop.index }} ({{ response.type }})
                        <span style="margin-left: auto; font-size: 0.9rem; color: #6b7280;">
                            {{ response.size }} chars
                        </span>
                    </div>
                    <div class="response-content">{{ response.response|truncate(2000) }}</div>
                </div>
                {% endfor %}
                {% endif %}
            </div>
            {% endfor %}
        </div>

        <div class="footer">
            <p>Generated by GitLlama v{{ gitllama_version }} • {{ generation_time }}</p>
            <p>🦙 Complete Context Transparency</p>
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
    </script>
</body>
</html>'''
    
    def _generate_fallback_report(self) -> Path:
        """Generate simple text report when dependencies are missing"""
        lines = [
            "GitLlama Context Tracking Report",
            "=" * 50,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Repository: {self.repo_url}",
            "",
            "Context Tracking Summary:",
        ]
        
        # Add context tracking data
        context_data = context_tracker.export_for_report()
        for stage in context_data['stages']:
            lines.append(f"\nStage: {stage['stage_name']}")
            lines.append(f"  Variables: {stage['num_variables']}")
            lines.append(f"  Prompts: {stage['num_prompts']}")
            lines.append(f"  Responses: {stage['num_responses']}")
        
        lines.append("\nInstall jinja2 and pygments for full HTML report")
        
        txt_path = self.output_dir / f"report_{self.timestamp}.txt"
        with open(txt_path, 'w') as f:
            f.write('\n'.join(lines))
        
        return txt_path