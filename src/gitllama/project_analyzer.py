"""
Project Analyzer for GitLlama
Hierarchical AI-powered repository analysis with clearly defined steps
"""

import json
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from .ollama_client import OllamaClient

logger = logging.getLogger(__name__)


class ProjectAnalyzer:
    """Analyzes repositories using hierarchical summarization"""
    
    def __init__(self, client: OllamaClient, model: str = "llama3.2:3b"):
        """Initialize the Project Analyzer.
        
        Args:
            client: OllamaClient instance
            model: Model name to use for analysis
        """
        self.client = client
        self.model = model
        
        # Get model's context size
        self.max_context_size = self.client.get_model_context_size(model)
        # Reserve space for prompt and response (use 70% of context)
        self.usable_context_size = int(self.max_context_size * 0.7)
        
        logger.info(f"ProjectAnalyzer initialized with model: {model}")
        logger.info(f"Context window size: {self.max_context_size} tokens")
        logger.info(f"Usable context size: {self.usable_context_size} tokens")
    
    def analyze_all_branches(self, repo_path: Path) -> Tuple[str, Dict[str, Dict]]:
        """Analyze all branches in the repository.
        
        This method analyzes the current branch and all other branches.
        
        Args:
            repo_path: Path to the repository
            
        Returns:
            Tuple of (current_branch_name, dict of branch_name -> analysis)
        """
        logger.info("=" * 60)
        logger.info("ANALYZING ALL REPOSITORY BRANCHES")
        logger.info("=" * 60)
        
        # Get current branch
        current_branch = self._get_current_branch(repo_path)
        logger.info(f"Current branch: {current_branch}")
        
        # Get all branches
        all_branches = self._get_all_branches(repo_path)
        logger.info(f"Found {len(all_branches)} total branches")
        
        # Analyze each branch
        branch_analyses = {}
        
        for i, branch in enumerate(all_branches, 1):
            logger.info(f"\n{'=' * 60}")
            logger.info(f"ANALYZING BRANCH {i}/{len(all_branches)}: {branch}")
            logger.info(f"{'=' * 60}")
            
            # Checkout the branch
            if branch != current_branch:
                self._checkout_branch(repo_path, branch)
            
            # Analyze the branch
            analysis = self.analyze_repository(repo_path, branch_context=branch)
            branch_analyses[branch] = analysis
            
            logger.info(f"Branch '{branch}' analysis complete")
        
        # Return to original branch
        if current_branch in all_branches:
            self._checkout_branch(repo_path, current_branch)
        
        logger.info(f"\n{'=' * 60}")
        logger.info(f"ALL BRANCHES ANALYZED SUCCESSFULLY")
        logger.info(f"{'=' * 60}\n")
        
        return current_branch, branch_analyses
    
    def _get_current_branch(self, repo_path: Path) -> str:
        """Get the current branch name."""
        try:
            result = subprocess.run(
                ['git', 'branch', '--show-current'],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get current branch: {e}")
            return "unknown"
    
    def _get_all_branches(self, repo_path: Path) -> List[str]:
        """Get all local branches."""
        try:
            result = subprocess.run(
                ['git', 'branch', '--format=%(refname:short)'],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            branches = [b.strip() for b in result.stdout.split('\n') if b.strip()]
            return branches
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get branches: {e}")
            return []
    
    def _checkout_branch(self, repo_path: Path, branch: str) -> bool:
        """Checkout a specific branch."""
        try:
            subprocess.run(
                ['git', 'checkout', branch],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            logger.info(f"  Checked out branch: {branch}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"  Failed to checkout branch {branch}: {e}")
            return False
    
    def analyze_repository(self, repo_path: Path, branch_context: Optional[str] = None) -> Dict:
        """Main entry point for repository analysis.
        
        This method orchestrates the entire analysis pipeline.
        Each step is clearly separated for easy extension.
        
        Args:
            repo_path: Path to the repository
            branch_context: Optional branch name for context in prompts
            
        Returns:
            Complete analysis dictionary
        """
        logger.info(f"Starting hierarchical repository analysis")
        if branch_context:
            logger.info(f"Branch context: {branch_context}")
        logger.info("=" * 60)
        
        # ============================================================
        # STEP 1: DATA GATHERING
        # Collect all relevant files from the repository
        # ============================================================
        logger.info("STEP 1: DATA GATHERING")
        all_files, total_tokens = self._step1_gather_repository_data(repo_path)
        
        if not all_files:
            logger.warning("No analyzable files found in repository")
            return {
                "project_type": "empty",
                "technologies": [],
                "state": "No analyzable files found",
                "analysis_metadata": {
                    "total_files": 0,
                    "total_tokens": 0,
                    "chunks_created": 0,
                    "branch": branch_context
                }
            }
        
        # ============================================================
        # STEP 2: CHUNKING
        # Organize files into context-window-sized chunks
        # ============================================================
        logger.info("STEP 2: CHUNKING")
        chunks = self._step2_create_chunks(all_files)
        
        # ============================================================
        # STEP 3: CHUNK ANALYSIS
        # Analyze each chunk independently
        # ============================================================
        logger.info("STEP 3: CHUNK ANALYSIS")
        chunk_summaries = self._step3_analyze_chunks(chunks, branch_context)
        
        # ============================================================
        # STEP 4: HIERARCHICAL MERGING
        # Merge all chunk summaries into final analysis
        # ============================================================
        logger.info("STEP 4: HIERARCHICAL MERGING")
        final_summary = self._step4_merge_summaries(chunk_summaries)
        
        # ============================================================
        # STEP 5: FORMAT RESULTS
        # Format the final analysis for consumption
        # ============================================================
        logger.info("STEP 5: FORMAT RESULTS")
        result = self._step5_format_results(final_summary, all_files, chunks)
        
        # Add branch context to result
        if branch_context:
            result["branch"] = branch_context
            result["analysis_metadata"]["branch"] = branch_context
        
        logger.info("=" * 60)
        logger.info("Repository analysis complete!")
        
        return result
    
    # ============================================================
    # STEP 1: DATA GATHERING
    # ============================================================
    
    def _step1_gather_repository_data(self, repo_path: Path) -> Tuple[List[Dict], int]:
        """STEP 1: Gather all repository data for analysis.
        
        This step scans the repository and collects all relevant files.
        Future enhancements could include:
        - Git history analysis
        - Branch information gathering
        - Dependency file parsing
        - Binary file metadata extraction
        
        Returns:
            Tuple of (list of file data dicts, total token count)
        """
        logger.info(f"  Gathering repository data from {repo_path}")
        
        all_files = []
        total_tokens = 0
        
        # Define file extensions to analyze
        text_extensions = {'.py', '.js', '.tsx', '.jsx', '.md', '.txt', '.json', 
                          '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf',
                          '.sh', '.bash', '.zsh', '.fish', '.bat', '.cmd',
                          '.java', '.c', '.cpp', '.h', '.hpp', '.cs', '.go',
                          '.rs', '.rb', '.php', '.swift', '.kt', '.scala',
                          '.html', '.css', '.scss', '.less', '.xml', '.vue',
                          '.Dockerfile', '.dockerignore', '.gitignore',
                          '.env.example', 'Makefile', 'CMakeLists.txt'}
        
        # Also check for files without extensions
        special_files = {'Dockerfile', 'Makefile', 'README', 'LICENSE', 
                        'CHANGELOG', 'AUTHORS', 'CONTRIBUTORS'}
        
        for file_path in repo_path.rglob("*"):
            # Skip hidden directories and files
            if any(part.startswith('.') for part in file_path.parts[:-1]):
                continue
            
            # Check if file should be analyzed
            should_analyze = (
                file_path.is_file() and 
                (file_path.suffix in text_extensions or 
                 file_path.name in special_files)
            )
            
            if should_analyze:
                try:
                    # Check file size first
                    file_size = file_path.stat().st_size
                    if file_size > 100000:  # Skip files larger than 100KB
                        logger.debug(f"  Skipping large file: {file_path}")
                        continue
                    
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    relative_path = file_path.relative_to(repo_path)
                    file_tokens = self.client.count_tokens(content)
                    
                    all_files.append({
                        'path': str(relative_path),
                        'content': content,
                        'tokens': file_tokens,
                        'extension': file_path.suffix,
                        'size_bytes': file_size
                    })
                    total_tokens += file_tokens
                    
                except Exception as e:
                    logger.debug(f"  Could not read {file_path}: {e}")
        
        logger.info(f"  Found {len(all_files)} files with {total_tokens} total tokens")
        return all_files, total_tokens
    
    # ============================================================
    # STEP 2: CHUNKING
    # ============================================================
    
    def _step2_create_chunks(self, files: List[Dict]) -> List[List[Dict]]:
        """STEP 2: Organize files into chunks that fit within context window.
        
        This step groups files intelligently to maximize context usage.
        Future enhancements could include:
        - Semantic grouping (keep related files together)
        - Priority-based chunking (important files first)
        - Language-specific chunking strategies
        
        Args:
            files: List of file data dictionaries
            
        Returns:
            List of file chunks
        """
        logger.info(f"  Creating chunks (max {self.usable_context_size} tokens each)")
        
        # Reserve space for prompt (roughly 500 tokens)
        chunk_size = self.usable_context_size - 500
        
        chunks = []
        current_chunk = []
        current_tokens = 0
        
        # Sort files by path for better organization
        sorted_files = sorted(files, key=lambda x: x['path'])
        
        for file_data in sorted_files:
            file_tokens = file_data['tokens']
            
            # If single file is too large, split it
            if file_tokens > chunk_size:
                # Save current chunk if it has content
                if current_chunk:
                    chunks.append(current_chunk)
                    current_chunk = []
                    current_tokens = 0
                
                # Split the large file
                content_chunks = self.client.split_into_chunks(
                    file_data['content'], 
                    chunk_size
                )
                for i, content_chunk in enumerate(content_chunks):
                    chunks.append([{
                        'path': f"{file_data['path']} (part {i+1}/{len(content_chunks)})",
                        'content': content_chunk,
                        'tokens': self.client.count_tokens(content_chunk),
                        'extension': file_data['extension']
                    }])
            
            # If adding this file would exceed chunk size, start new chunk
            elif current_tokens + file_tokens > chunk_size:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = [file_data]
                current_tokens = file_tokens
            
            # Add file to current chunk
            else:
                current_chunk.append(file_data)
                current_tokens += file_tokens
        
        # Add remaining chunk
        if current_chunk:
            chunks.append(current_chunk)
        
        logger.info(f"  Created {len(chunks)} chunks for analysis")
        for i, chunk in enumerate(chunks, 1):
            chunk_tokens = sum(f['tokens'] for f in chunk)
            logger.info(f"    Chunk {i}: {len(chunk)} files, {chunk_tokens} tokens")
        
        return chunks
    
    # ============================================================
    # STEP 3: CHUNK ANALYSIS
    # ============================================================
    
    def _step3_analyze_chunks(self, chunks: List[List[Dict]], branch_context: Optional[str] = None) -> List[Dict]:
        """STEP 3: Analyze each chunk independently.
        
        This step performs AI analysis on each chunk.
        Future enhancements could include:
        - Parallel chunk processing
        - Different analysis strategies per file type
        - Code quality metrics extraction
        - Security vulnerability scanning
        
        Args:
            chunks: List of file chunks
            branch_context: Optional branch name for context
            
        Returns:
            List of chunk analysis summaries
        """
        logger.info(f"  Analyzing {len(chunks)} chunks")
        
        chunk_summaries = []
        for i, chunk in enumerate(chunks, 1):
            logger.info(f"    Processing chunk {i}/{len(chunks)}...")
            summary = self._analyze_single_chunk(chunk, i, len(chunks), branch_context)
            chunk_summaries.append(summary)
            logger.info(f"    Chunk {i} analysis complete")
        
        return chunk_summaries
    
    def _analyze_single_chunk(self, chunk: List[Dict], chunk_index: int, total_chunks: int, 
                             branch_context: Optional[str] = None) -> Dict:
        """Analyze a single chunk of files."""
        
        # Build context from chunk
        context_parts = []
        for file_data in chunk:
            context_parts.append(f"=== File: {file_data['path']} ===")
            # Limit content preview to save tokens for analysis
            content_preview = file_data['content'][:2000]
            if len(file_data['content']) > 2000:
                content_preview += "\n... [content truncated]"
            context_parts.append(content_preview)
            context_parts.append("")
        
        context = "\n".join(context_parts)
        
        # Calculate actual tokens for logging
        context_tokens = self.client.count_tokens(context)
        logger.debug(f"      Chunk {chunk_index} context: {context_tokens} tokens")
        
        # Adjust prompt based on branch context
        branch_note = f" (Branch: {branch_context})" if branch_context else ""
        
        prompt = f"""Analyze this portion of a code repository{branch_note} (chunk {chunk_index} of {total_chunks}):

{context}

Provide a comprehensive analysis including:
1. Main purpose/functionality of these files
2. Technologies and frameworks used
3. Code quality observations
4. Key patterns or architectural decisions
5. Notable features or issues
{f"6. How this branch '{branch_context}' differs from main (if apparent)" if branch_context and branch_context not in ['main', 'master'] else ""}

Response in JSON format:
{{
    "chunk_index": {chunk_index},
    "file_count": {len(chunk)},
    "main_purpose": "",
    "technologies": [],
    "patterns": [],
    "quality_notes": "",
    "key_features": [],
    {f'"branch_context": "{branch_context}",' if branch_context else ''}
    {'"branch_differences": "",' if branch_context and branch_context not in ['main', 'master'] else ''}
    "analysis_focus": ""
}}"""
        
        messages = [{"role": "user", "content": prompt}]
        response = ""
        
        for chunk_text in self.client.chat_stream(self.model, messages):
            response += chunk_text
        
        try:
            analysis = json.loads(response)
            return analysis
        except json.JSONDecodeError:
            logger.warning(f"      Chunk {chunk_index} JSON parse failed, using raw response")
            return {
                "chunk_index": chunk_index,
                "file_count": len(chunk),
                "raw_analysis": response[:500]
            }
    
    # ============================================================
    # STEP 4: HIERARCHICAL MERGING
    # ============================================================
    
    def _step4_merge_summaries(self, summaries: List[Dict]) -> Dict:
        """STEP 4: Hierarchically merge all summaries.
        
        This step combines chunk summaries using a merge-sort approach.
        Future enhancements could include:
        - Weighted merging based on file importance
        - Cross-reference detection between chunks
        - Dependency graph construction
        
        Args:
            summaries: List of chunk summaries
            
        Returns:
            Final merged summary
        """
        logger.info(f"  Starting hierarchical merge of {len(summaries)} summaries")
        
        def merge_recursive(summaries_to_merge: List[Dict], level: int = 1) -> Dict:
            """Recursively merge summaries."""
            
            if len(summaries_to_merge) == 1:
                return summaries_to_merge[0]
            
            # Build context from summaries
            context_parts = []
            for i, summary in enumerate(summaries_to_merge, 1):
                context_parts.append(f"=== Summary {i} ===")
                context_parts.append(json.dumps(summary, indent=2))
                context_parts.append("")
            
            context = "\n".join(context_parts)
            context_tokens = self.client.count_tokens(context)
            
            # If context is too large, recursively merge in smaller groups
            if context_tokens > self.usable_context_size:
                logger.info(f"    Level {level}: Context too large ({context_tokens} tokens), splitting")
                mid = len(summaries_to_merge) // 2
                left_summary = merge_recursive(summaries_to_merge[:mid], level)
                right_summary = merge_recursive(summaries_to_merge[mid:], level)
                return merge_recursive([left_summary, right_summary], level + 1)
            
            logger.info(f"    Level {level}: Merging {len(summaries_to_merge)} summaries ({context_tokens} tokens)")
            
            prompt = f"""Merge these {len(summaries_to_merge)} analyses into a unified summary:

{context}

Create a comprehensive merged analysis that:
1. Identifies the overall project type and purpose
2. Lists all technologies used across the codebase
3. Describes the project architecture and structure
4. Highlights key features and patterns
5. Assesses overall code quality and state

Response in JSON format:
{{
    "merge_level": {level},
    "summaries_merged": {len(summaries_to_merge)},
    "project_type": "",
    "overall_purpose": "",
    "all_technologies": [],
    "architecture": "",
    "key_patterns": [],
    "overall_quality": "",
    "state": ""
}}"""
            
            messages = [{"role": "user", "content": prompt}]
            response = ""
            
            for chunk in self.client.chat_stream(self.model, messages):
                response += chunk
            
            try:
                merged = json.loads(response)
                logger.info(f"    Level {level} merge complete")
                return merged
            except json.JSONDecodeError:
                logger.warning(f"    Level {level} merge JSON parse failed")
                return {
                    "merge_level": level,
                    "summaries_merged": len(summaries_to_merge),
                    "raw_analysis": response[:500]
                }
        
        final_summary = merge_recursive(summaries)
        logger.info(f"  Hierarchical merge complete")
        return final_summary
    
    # ============================================================
    # STEP 5: FORMAT RESULTS
    # ============================================================
    
    def _step5_format_results(self, final_summary: Dict, all_files: List[Dict], 
                             chunks: List[List[Dict]]) -> Dict:
        """STEP 5: Format the final analysis results.
        
        This step creates the final output format.
        Future enhancements could include:
        - Confidence scores
        - Suggested improvements
        - Technical debt assessment
        - README generation
        
        Args:
            final_summary: The merged analysis
            all_files: Original file list
            chunks: The chunks that were created
            
        Returns:
            Formatted analysis results
        """
        logger.info(f"  Formatting final results")
        
        total_tokens = sum(f['tokens'] for f in all_files)
        
        result = {
            "project_type": final_summary.get("project_type", "unknown"),
            "technologies": final_summary.get("all_technologies", []),
            "state": final_summary.get("state", final_summary.get("overall_purpose", "analyzed")),
            "architecture": final_summary.get("architecture", ""),
            "quality": final_summary.get("overall_quality", ""),
            "patterns": final_summary.get("key_patterns", []),
            "analysis_metadata": {
                "total_files": len(all_files),
                "total_tokens": total_tokens,
                "chunks_created": len(chunks),
                "context_window": self.max_context_size,
                "model": self.model
            },
            "detailed_analysis": final_summary
        }
        
        logger.info(f"  Results formatted successfully")
        return result