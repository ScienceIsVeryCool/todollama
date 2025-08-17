"""
Report Generator for GitLlama
Professional HTML report system for AI decision transparency
"""

import logging
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

try:
    from jinja2 import Template
    from pygments import highlight
    from pygments.lexers import get_lexer_by_name, guess_lexer
    from pygments.formatters import HtmlFormatter
    from pygments.util import ClassNotFound
    REPORT_DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    REPORT_DEPENDENCIES_AVAILABLE = False
    Template = None
    highlight = None
    get_lexer_by_name = None
    guess_lexer = None
    HtmlFormatter = None
    ClassNotFound = Exception  # Fallback
    logger = logging.getLogger(__name__)
    logger.warning(f"Report generation dependencies not available: {e}. Install with: pip install jinja2 pygments")

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generates professional HTML reports for GitLlama execution"""
    
    def __init__(self, repo_url: str, output_dir: str = "gitllama_reports"):
        """Initialize the report generator.
        
        Args:
            repo_url: URL of the repository being analyzed
            output_dir: Directory to save reports in
        """
        self.repo_url = repo_url
        self.output_dir = Path(output_dir)
        self.start_time = datetime.now()
        self.timestamp = self.start_time.strftime("%Y%m%d_%H%M%S")
        
        # Data collection structures
        self.executive_summary = {}
        self.repository_analysis = {
            "phases": [],
            "timeline": []
        }
        self.ai_decisions = []
        self.guided_questions = []
        self.branch_analysis = {
            "discovered_branches": [],
            "evaluation_scores": {},
            "selection_reasoning": "",
            "final_selection": ""
        }
        self.file_operations = []
        self.metrics = {
            "processing_times": {},
            "token_usage": {},
            "ai_calls": 0,
            "model_info": {}
        }
        
        # Create output directory
        self.output_dir.mkdir(exist_ok=True)
        
        logger.info(f"ReportGenerator initialized for {repo_url}")
    
    def start_phase(self, phase_name: str, description: str):
        """Start tracking a new phase of execution."""
        phase_data = {
            "name": phase_name,
            "description": description,
            "start_time": datetime.now(),
            "end_time": None,
            "duration": None,
            "details": []
        }
        self.repository_analysis["phases"].append(phase_data)
        logger.debug(f"Started phase: {phase_name}")
    
    def end_phase(self, phase_name: str):
        """End tracking of the current phase."""
        for phase in reversed(self.repository_analysis["phases"]):
            if phase["name"] == phase_name and phase["end_time"] is None:
                phase["end_time"] = datetime.now()
                phase["duration"] = (phase["end_time"] - phase["start_time"]).total_seconds()
                self.metrics["processing_times"][phase_name] = phase["duration"]
                logger.debug(f"Ended phase: {phase_name} ({phase['duration']:.2f}s)")
                break
    
    def add_phase_detail(self, phase_name: str, detail: str):
        """Add a detail to the current phase."""
        for phase in reversed(self.repository_analysis["phases"]):
            if phase["name"] == phase_name:
                phase["details"].append({
                    "timestamp": datetime.now(),
                    "detail": detail
                })
                break
    
    def add_guided_question(self, question: str, context: str, answer: str, confidence: Optional[float] = None):
        """Add a guided question and answer to the report."""
        qa_data = {
            "timestamp": datetime.now(),
            "question": question,
            "context": context[:200] + "..." if len(context) > 200 else context,
            "answer": answer,
            "confidence": confidence,
            "type": "guided_question"
        }
        self.guided_questions.append(qa_data)
        logger.debug(f"Added guided Q&A: {question[:50]}...")
    
    def add_ai_decision(self, context: str, question: str, options: List[str], 
                       selected: str, confidence: float, reasoning: str = ""):
        """Add an AI decision to the report."""
        decision_data = {
            "timestamp": datetime.now(),
            "context": context[:200] + "..." if len(context) > 200 else context,
            "question": question,
            "options": options,
            "selected": selected,
            "confidence": confidence,
            "reasoning": reasoning,
            "type": "single_word_decision"
        }
        self.ai_decisions.append(decision_data)
        self.metrics["ai_calls"] += 1
        logger.debug(f"Added AI decision: {question[:50]}... -> {selected}")
    
    def add_branch_discovery(self, branches: List[str]):
        """Add discovered branches to the report."""
        self.branch_analysis["discovered_branches"] = branches
        logger.debug(f"Added {len(branches)} discovered branches")
    
    def add_branch_evaluation(self, branch_name: str, score: int, reasons: List[str]):
        """Add branch evaluation scoring."""
        self.branch_analysis["evaluation_scores"][branch_name] = {
            "score": score,
            "reasons": reasons
        }
        logger.debug(f"Added branch evaluation for {branch_name}: {score}")
    
    def set_branch_selection(self, selected_branch: str, reasoning: str, action: str):
        """Set the final branch selection."""
        self.branch_analysis["final_selection"] = selected_branch
        self.branch_analysis["selection_reasoning"] = reasoning
        self.branch_analysis["action"] = action
        logger.debug(f"Set branch selection: {selected_branch} ({action})")
    
    def add_file_operation(self, operation: str, file_path: str, reason: str, 
                          content: str = "", diff: str = ""):
        """Add a file operation to the report."""
        operation_data = {
            "timestamp": datetime.now(),
            "operation": operation,
            "file_path": file_path,
            "reason": reason,
            "content_preview": content[:2000] if content else "",
            "diff": diff,
            "highlighted_content": self._highlight_code(content, file_path) if content else ""
        }
        self.file_operations.append(operation_data)
        logger.debug(f"Added file operation: {operation} {file_path}")
    
    def set_executive_summary(self, repo_path: str, branch: str, modified_files: List[str], 
                            commit_hash: str, success: bool, total_decisions: int):
        """Set the executive summary data."""
        self.executive_summary = {
            "repo_url": self.repo_url,
            "repo_path": repo_path,
            "branch_selected": branch,
            "files_modified": modified_files,
            "commit_hash": commit_hash,
            "success": success,
            "total_ai_decisions": total_decisions,
            "total_guided_questions": len(self.guided_questions),
            "total_file_operations": len(self.file_operations),
            "execution_time": (datetime.now() - self.start_time).total_seconds()
        }
        logger.debug("Set executive summary data")
    
    def set_model_info(self, model: str, context_window: int, total_tokens: int):
        """Set model and token usage information."""
        self.metrics["model_info"] = {
            "model": model,
            "context_window": context_window,
            "total_tokens": total_tokens
        }
        self.metrics["token_usage"]["total"] = total_tokens
        logger.debug(f"Set model info: {model} ({total_tokens} tokens)")
    
    def _highlight_code(self, content: str, file_path: str) -> str:
        """Apply syntax highlighting to code content."""
        try:
            if file_path:
                lexer = get_lexer_by_name(Path(file_path).suffix[1:] if Path(file_path).suffix else 'text')
            else:
                lexer = guess_lexer(content)
            
            formatter = HtmlFormatter(style='github', cssclass='highlight', noclasses=True)
            return highlight(content, lexer, formatter)
        except ClassNotFound:
            # Fallback to plain text with HTML escaping
            return f'<pre style="background: #f8f8f8; padding: 10px; border-radius: 4px;">{self._escape_html(content)}</pre>'
        except Exception as e:
            logger.debug(f"Syntax highlighting failed: {e}")
            return f'<pre style="background: #f8f8f8; padding: 10px; border-radius: 4px;">{self._escape_html(content)}</pre>'
    
    def _escape_html(self, text: str) -> str:
        """Escape HTML characters."""
        return (text.replace('&', '&amp;')
                   .replace('<', '&lt;')
                   .replace('>', '&gt;')
                   .replace('"', '&quot;')
                   .replace("'", '&#x27;'))
    
    def generate_report(self, auto_open: bool = True) -> Path:
        """Generate the final HTML report."""
        if not REPORT_DEPENDENCIES_AVAILABLE:
            logger.error("Cannot generate report: missing dependencies (jinja2, pygments)")
            logger.info("Install with: pip install jinja2 pygments")
            
            # Generate a simple fallback report
            return self._generate_fallback_report()
        
        logger.info("Generating HTML report...")
        
        # Prepare template data
        template_data = {
            "timestamp": self.timestamp,
            "generation_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "executive_summary": self.executive_summary,
            "repository_analysis": self.repository_analysis,
            "guided_questions": self.guided_questions,
            "ai_decisions": self.ai_decisions,
            "branch_analysis": self.branch_analysis,
            "file_operations": self.file_operations,
            "metrics": self.metrics
        }
        
        # Generate HTML
        html_content = self._render_html_template(template_data)
        
        # Save HTML report
        html_filename = f"gitllama_report_{self.timestamp}.html"
        html_path = self.output_dir / html_filename
        
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Generate companion Markdown report
        md_content = self._render_markdown_template(template_data)
        md_filename = f"gitllama_report_{self.timestamp}.md"
        md_path = self.output_dir / md_filename
        
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        logger.info(f"Reports generated: {html_path}")
        
        # Auto-open in browser
        if auto_open:
            try:
                webbrowser.open(f'file://{html_path.absolute()}')
                logger.info("Report opened in browser")
            except Exception as e:
                logger.warning(f"Could not auto-open report: {e}")
        
        return html_path
    
    def _render_html_template(self, data: Dict[str, Any]) -> str:
        """Render the HTML template with data."""
        template = Template(self._get_html_template())
        return template.render(**data)
    
    def _render_markdown_template(self, data: Dict[str, Any]) -> str:
        """Render the Markdown template with data."""
        template = Template(self._get_markdown_template())
        return template.render(**data)
    
    def _get_html_template(self) -> str:
        """Get the HTML template string."""
        return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GitLlama Report - {{ timestamp }}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6; color: #333; background: #f5f7fa;
        }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; padding: 2rem; border-radius: 12px; margin-bottom: 2rem;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        }
        .header h1 { font-size: 2.5rem; margin-bottom: 0.5rem; }
        .header p { opacity: 0.9; font-size: 1.1rem; }
        .section { 
            background: white; padding: 2rem; margin-bottom: 1.5rem; 
            border-radius: 12px; box-shadow: 0 4px 16px rgba(0,0,0,0.05);
        }
        .section h2 { 
            color: #2d3748; border-bottom: 3px solid #667eea; 
            padding-bottom: 0.5rem; margin-bottom: 1.5rem; font-size: 1.8rem;
        }
        .executive-grid { 
            display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); 
            gap: 1.5rem; margin-bottom: 2rem;
        }
        .metric-card { 
            background: #f8fafc; padding: 1.5rem; border-radius: 8px; 
            border-left: 4px solid #667eea; text-align: center;
        }
        .metric-value { font-size: 2rem; font-weight: bold; color: #667eea; }
        .metric-label { color: #64748b; text-transform: uppercase; font-size: 0.85rem; }
        .timeline { position: relative; padding: 1rem 0; }
        .timeline-item { 
            position: relative; padding: 1rem 0 1rem 3rem; 
            border-left: 2px solid #e2e8f0; margin-bottom: 1rem;
        }
        .timeline-item:before { 
            content: ''; position: absolute; left: -6px; top: 1.5rem;
            width: 12px; height: 12px; border-radius: 50%; background: #667eea;
        }
        .timeline-item:last-child { border-left: none; }
        .decision-table { width: 100%; border-collapse: collapse; margin: 1rem 0; }
        .decision-table th, .decision-table td { 
            padding: 0.75rem; text-align: left; border-bottom: 1px solid #e2e8f0;
        }
        .decision-table th { background: #f8fafc; font-weight: 600; }
        .decision-table tr:hover { background: #f8fafc; }
        .confidence { 
            padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.85rem;
            font-weight: 600; text-align: center; min-width: 60px;
        }
        .confidence-high { background: #dcfce7; color: #166534; }
        .confidence-medium { background: #fef3c7; color: #92400e; }
        .confidence-low { background: #fee2e2; color: #991b1b; }
        .file-op { 
            border: 1px solid #e2e8f0; border-radius: 8px; 
            margin-bottom: 1rem; overflow: hidden;
        }
        .file-op-header { 
            background: #f8fafc; padding: 1rem; border-bottom: 1px solid #e2e8f0;
            display: flex; justify-content: space-between; align-items: center;
        }
        .file-op-content { padding: 1rem; }
        .operation-badge { 
            padding: 0.25rem 0.75rem; border-radius: 20px; font-size: 0.8rem;
            font-weight: 600; text-transform: uppercase;
        }
        .op-create { background: #dcfce7; color: #166534; }
        .op-modify { background: #dbeafe; color: #1e40af; }
        .op-delete { background: #fee2e2; color: #991b1b; }
        .collapsible { cursor: pointer; user-select: none; }
        .collapsible:hover { background: #f8fafc; }
        .collapsible-content { display: none; padding: 1rem; background: #f8fafc; }
        .collapsible.active + .collapsible-content { display: block; }
        .section-header { 
            cursor: pointer; user-select: none; 
            border-radius: 8px; transition: background 0.2s;
        }
        .section-header:hover { background: #f1f5f9; }
        .section-content { 
            display: block; overflow: hidden; 
            transition: max-height 0.3s ease-out;
        }
        .section-content.collapsed { 
            max-height: 0; 
            padding: 0 2rem; 
        }
        .collapse-indicator { 
            float: right; margin-right: 1rem; 
            transition: transform 0.3s ease;
        }
        .collapse-indicator.rotated { transform: rotate(180deg); }
        .highlight pre { margin: 0; font-size: 0.9rem; }
        .branch-flow { display: flex; flex-wrap: wrap; gap: 1rem; align-items: center; margin: 1rem 0; }
        .branch-node { 
            padding: 0.5rem 1rem; background: #f1f5f9; border-radius: 6px;
            border: 2px solid #cbd5e1; position: relative;
        }
        .branch-selected { background: #dcfce7; border-color: #22c55e; }
        .arrow { margin: 0 0.5rem; color: #64748b; }
        .footer { text-align: center; padding: 2rem; color: #64748b; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🦙 GitLlama Report</h1>
            <p>AI-Powered Repository Analysis • {{ generation_time }}</p>
            <p>Repository: {{ executive_summary.repo_url }}</p>
        </div>

        <!-- Executive Summary -->
        <div class="section">
            <h2 class="section-header" onclick="toggleSection(this)">
                📊 Executive Summary
                <span class="collapse-indicator">▼</span>
            </h2>
            <div class="section-content">
            <div class="executive-grid">
                <div class="metric-card">
                    <div class="metric-value">{{ executive_summary.total_ai_decisions or 0 }}</div>
                    <div class="metric-label">AI Decisions</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{{ executive_summary.files_modified|length }}</div>
                    <div class="metric-label">Files Modified</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{{ "%.1f"|format(executive_summary.execution_time or 0) }}s</div>
                    <div class="metric-label">Execution Time</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{% if executive_summary.success %}✅{% else %}❌{% endif %}</div>
                    <div class="metric-label">Status</div>
                </div>
            </div>
            <p><strong>Branch Selected:</strong> {{ executive_summary.branch_selected or 'N/A' }}</p>
            <p><strong>Commit:</strong> {{ executive_summary.commit_hash or 'N/A' }}</p>
            {% if executive_summary.files_modified %}
            <p><strong>Modified Files:</strong> {{ executive_summary.files_modified|join(', ') }}</p>
            {% endif %}
            </div>
        </div>

        <!-- Repository Analysis Timeline -->
        <div class="section">
            <h2 class="section-header" onclick="toggleSection(this)">
                🔍 Repository Analysis Timeline
                <span class="collapse-indicator">▼</span>
            </h2>
            <div class="section-content">
            <div class="timeline">
                {% for phase in repository_analysis.phases %}
                <div class="timeline-item">
                    <h3>{{ phase.name }}</h3>
                    <p>{{ phase.description }}</p>
                    {% if phase.duration %}
                    <small style="color: #64748b;">Duration: {{ "%.2f"|format(phase.duration) }}s</small>
                    {% endif %}
                    {% if phase.details %}
                    <div class="collapsible" onclick="toggleCollapsible(this)">
                        <small>📋 View Details ({{ phase.details|length }} items)</small>
                    </div>
                    <div class="collapsible-content">
                        {% for detail in phase.details %}
                        <p><small>• {{ detail.detail }}</small></p>
                        {% endfor %}
                    </div>
                    {% endif %}
                </div>
                {% endfor %}
            </div>
            </div>
        </div>

        <!-- AI Decision Log -->
        <div class="section">
            <h2 class="section-header" onclick="toggleSection(this)">
                🤖 AI Decision Log
                <span class="collapse-indicator">▼</span>
            </h2>
            <div class="section-content">
            {% if guided_questions or ai_decisions %}
            <table class="decision-table">
                <thead>
                    <tr>
                        <th>Time</th>
                        <th>Type</th>
                        <th>Question</th>
                        <th>Answer/Decision</th>
                        <th>Confidence</th>
                    </tr>
                </thead>
                <tbody>
                    {% for qa in guided_questions %}
                    <tr>
                        <td>{{ qa.timestamp.strftime('%H:%M:%S') }}</td>
                        <td>Guided Q&A</td>
                        <td>{{ qa.question }}</td>
                        <td>{{ qa.answer[:100] }}{% if qa.answer|length > 100 %}...{% endif %}</td>
                        <td>
                            {% if qa.confidence %}
                            <span class="confidence confidence-{% if qa.confidence > 0.8 %}high{% elif qa.confidence > 0.6 %}medium{% else %}low{% endif %}">
                                {{ "%.0f"|format(qa.confidence * 100) }}%
                            </span>
                            {% else %}-{% endif %}
                        </td>
                    </tr>
                    {% endfor %}
                    {% for decision in ai_decisions %}
                    <tr>
                        <td>{{ decision.timestamp.strftime('%H:%M:%S') }}</td>
                        <td>Single-Word</td>
                        <td>{{ decision.question }}</td>
                        <td><strong>{{ decision.selected }}</strong> (from: {{ decision.options|join(', ') }})</td>
                        <td>
                            <span class="confidence confidence-{% if decision.confidence > 0.8 %}high{% elif decision.confidence > 0.6 %}medium{% else %}low{% endif %}">
                                {{ "%.0f"|format(decision.confidence * 100) }}%
                            </span>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% else %}
            <p>No AI decisions recorded.</p>
            {% endif %}
            </div>
        </div>

        <!-- Branch Selection Journey -->
        <div class="section">
            <h2 class="section-header" onclick="toggleSection(this)">
                🌿 Branch Selection Journey
                <span class="collapse-indicator">▼</span>
            </h2>
            <div class="section-content">
            {% if branch_analysis.discovered_branches %}
            <h3>Discovered Branches</h3>
            <div class="branch-flow">
                {% for branch in branch_analysis.discovered_branches %}
                <div class="branch-node {% if branch == branch_analysis.final_selection %}branch-selected{% endif %}">
                    {{ branch }}
                    {% if branch_analysis.evaluation_scores[branch] %}
                    <br><small>Score: {{ branch_analysis.evaluation_scores[branch].score }}</small>
                    {% endif %}
                </div>
                {% if not loop.last %}<span class="arrow">→</span>{% endif %}
                {% endfor %}
            </div>
            {% endif %}
            
            {% if branch_analysis.final_selection %}
            <h3>Final Selection</h3>
            <p><strong>Selected:</strong> {{ branch_analysis.final_selection }}</p>
            <p><strong>Action:</strong> {{ branch_analysis.action or 'Unknown' }}</p>
            <p><strong>Reasoning:</strong> {{ branch_analysis.selection_reasoning }}</p>
            {% endif %}
            </div>
        </div>

        <!-- File Operations Report -->
        <div class="section">
            <h2 class="section-header" onclick="toggleSection(this)">
                📝 File Operations Report
                <span class="collapse-indicator">▼</span>
            </h2>
            <div class="section-content">
            {% if file_operations %}
            {% for op in file_operations %}
            <div class="file-op">
                <div class="file-op-header">
                    <div>
                        <span class="operation-badge op-{{ op.operation.lower() }}">{{ op.operation }}</span>
                        <strong>{{ op.file_path }}</strong>
                    </div>
                    <small>{{ op.timestamp.strftime('%H:%M:%S') }}</small>
                </div>
                <div class="file-op-content">
                    <p><strong>Reason:</strong> {{ op.reason }}</p>
                    {% if op.content_preview %}
                    <div class="collapsible" onclick="toggleCollapsible(this)">
                        <strong>📄 Content Preview</strong>
                    </div>
                    <div class="collapsible-content">
                        {{ op.highlighted_content|safe }}
                    </div>
                    {% endif %}
                </div>
            </div>
            {% endfor %}
            {% else %}
            <p>No file operations recorded.</p>
            {% endif %}
            </div>
        </div>

        <!-- Metrics Dashboard -->
        <div class="section">
            <h2 class="section-header" onclick="toggleSection(this)">
                📈 Metrics Dashboard
                <span class="collapse-indicator">▼</span>
            </h2>
            <div class="section-content">
            <div class="executive-grid">
                <div class="metric-card">
                    <div class="metric-value">{{ metrics.ai_calls or 0 }}</div>
                    <div class="metric-label">AI API Calls</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{{ metrics.token_usage.total or 0 }}</div>
                    <div class="metric-label">Total Tokens</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{{ metrics.model_info.model or 'N/A' }}</div>
                    <div class="metric-label">Model Used</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{{ metrics.model_info.context_window or 'N/A' }}</div>
                    <div class="metric-label">Context Window</div>
                </div>
            </div>
            
            {% if metrics.processing_times %}
            <h3>Processing Times</h3>
            <table class="decision-table">
                <thead>
                    <tr><th>Phase</th><th>Duration</th></tr>
                </thead>
                <tbody>
                    {% for phase, duration in metrics.processing_times.items() %}
                    <tr>
                        <td>{{ phase }}</td>
                        <td>{{ "%.2f"|format(duration) }}s</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% endif %}
            </div>
        </div>

        <div class="footer">
            <p>Generated by GitLlama v0.4.0 • {{ generation_time }}</p>
            <p>🦙 Transparent AI-powered git automation</p>
        </div>
    </div>

    <script>
        function toggleCollapsible(element) {
            element.classList.toggle('active');
        }
        
        function toggleSection(header) {
            const content = header.nextElementSibling;
            const indicator = header.querySelector('.collapse-indicator');
            
            if (content.classList.contains('collapsed')) {
                content.classList.remove('collapsed');
                content.style.maxHeight = content.scrollHeight + 'px';
                indicator.classList.remove('rotated');
                indicator.textContent = '▼';
            } else {
                content.style.maxHeight = content.scrollHeight + 'px';
                setTimeout(() => {
                    content.classList.add('collapsed');
                    content.style.maxHeight = '0px';
                }, 10);
                indicator.classList.add('rotated');
                indicator.textContent = '▲';
            }
        }
        
        // Initialize all sections as expanded by default
        document.addEventListener('DOMContentLoaded', function() {
            const contents = document.querySelectorAll('.section-content');
            contents.forEach(content => {
                content.style.maxHeight = content.scrollHeight + 'px';
            });
        });
    </script>
</body>
</html>'''
    
    def _get_markdown_template(self) -> str:
        """Get the Markdown template string."""
        return '''# 🦙 GitLlama Report - {{ timestamp }}

**Generated:** {{ generation_time }}  
**Repository:** {{ executive_summary.repo_url }}

## 📊 Executive Summary

- **AI Decisions Made:** {{ executive_summary.total_ai_decisions or 0 }}
- **Files Modified:** {{ executive_summary.files_modified|length }}
- **Execution Time:** {{ "%.1f"|format(executive_summary.execution_time or 0) }}s
- **Status:** {% if executive_summary.success %}✅ Success{% else %}❌ Failed{% endif %}
- **Branch Selected:** {{ executive_summary.branch_selected or 'N/A' }}
- **Commit:** {{ executive_summary.commit_hash or 'N/A' }}

{% if executive_summary.files_modified %}
**Modified Files:**
{% for file in executive_summary.files_modified %}
- {{ file }}
{% endfor %}
{% endif %}

## 🔍 Repository Analysis Timeline

{% for phase in repository_analysis.phases %}
### {{ phase.name }}
{{ phase.description }}
{% if phase.duration %}
**Duration:** {{ "%.2f"|format(phase.duration) }}s
{% endif %}

{% if phase.details %}
**Details:**
{% for detail in phase.details %}
- {{ detail.detail }}
{% endfor %}
{% endif %}

{% endfor %}

## 🤖 AI Decision Log

{% if guided_questions or ai_decisions %}
| Time | Type | Question | Answer/Decision | Confidence |
|------|------|----------|-----------------|------------|
{% for qa in guided_questions %}
| {{ qa.timestamp.strftime('%H:%M:%S') }} | Guided Q&A | {{ qa.question }} | {{ qa.answer[:50] }}{% if qa.answer|length > 50 %}...{% endif %} | {% if qa.confidence %}{{ "%.0f"|format(qa.confidence * 100) }}%{% else %}-{% endif %} |
{% endfor %}
{% for decision in ai_decisions %}
| {{ decision.timestamp.strftime('%H:%M:%S') }} | Single-Word | {{ decision.question }} | **{{ decision.selected }}** | {{ "%.0f"|format(decision.confidence * 100) }}% |
{% endfor %}
{% else %}
No AI decisions recorded.
{% endif %}

## 🌿 Branch Selection Journey

{% if branch_analysis.discovered_branches %}
**Discovered Branches:** {{ branch_analysis.discovered_branches|join(', ') }}

{% if branch_analysis.final_selection %}
**Final Selection:** {{ branch_analysis.final_selection }}  
**Action:** {{ branch_analysis.action or 'Unknown' }}  
**Reasoning:** {{ branch_analysis.selection_reasoning }}
{% endif %}
{% endif %}

## 📝 File Operations Report

{% if file_operations %}
{% for op in file_operations %}
### {{ op.operation }}: {{ op.file_path }}
**Time:** {{ op.timestamp.strftime('%H:%M:%S') }}  
**Reason:** {{ op.reason }}

{% if op.content_preview %}
**Content Preview:**
```
{{ op.content_preview }}
```
{% endif %}

{% endfor %}
{% else %}
No file operations recorded.
{% endif %}

## 📈 Metrics Dashboard

- **AI API Calls:** {{ metrics.ai_calls or 0 }}
- **Total Tokens:** {{ metrics.token_usage.total or 0 }}
- **Model Used:** {{ metrics.model_info.model or 'N/A' }}
- **Context Window:** {{ metrics.model_info.context_window or 'N/A' }}

{% if metrics.processing_times %}
**Processing Times:**
{% for phase, duration in metrics.processing_times.items() %}
- {{ phase }}: {{ "%.2f"|format(duration) }}s
{% endfor %}
{% endif %}

---
*Generated by GitLlama v0.4.0 • {{ generation_time }}*  
*🦙 Transparent AI-powered git automation*
'''
    
    def _generate_fallback_report(self) -> Path:
        """Generate a simple text-based fallback report when dependencies are missing."""
        logger.info("Generating fallback text report...")
        
        # Generate simple text report
        lines = [
            "GitLlama Execution Report",
            "=" * 50,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Repository: {self.repo_url}",
            "",
            "Executive Summary:",
            f"  Branch: {self.executive_summary.get('branch_selected', 'Unknown')}",
            f"  Files Modified: {len(self.executive_summary.get('files_modified', []))}",
            f"  Success: {self.executive_summary.get('success', False)}",
            f"  AI Decisions: {self.executive_summary.get('total_ai_decisions', 0)}",
            "",
            "AI Decisions Made:",
        ]
        
        for i, decision in enumerate(self.ai_decisions, 1):
            lines.append(f"  {i}. {decision['question']}")
            lines.append(f"     Selected: {decision['selected']} (confidence: {decision['confidence']:.0%})")
        
        if self.guided_questions:
            lines.extend([
                "",
                "Guided Questions:",
            ])
            for i, qa in enumerate(self.guided_questions, 1):
                lines.append(f"  {i}. Q: {qa['question']}")
                lines.append(f"     A: {qa['answer'][:100]}{'...' if len(qa['answer']) > 100 else ''}")
        
        if self.file_operations:
            lines.extend([
                "",
                "File Operations:",
            ])
            for op in self.file_operations:
                lines.append(f"  {op['operation']}: {op['file_path']}")
        
        lines.extend([
            "",
            "Note: This is a simplified report. For full HTML report with styling,",
            "install dependencies: pip install jinja2 pygments",
            ""
        ])
        
        # Save to file
        txt_filename = f"gitllama_report_{self.timestamp}.txt"
        txt_path = self.output_dir / txt_filename
        
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        logger.info(f"Fallback report generated: {txt_path}")
        return txt_path