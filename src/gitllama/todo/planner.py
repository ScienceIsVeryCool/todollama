"""
TODO-driven Planning Module for GitLlama
Creates actionable plans based on TODO analysis
"""

import logging
from pathlib import Path
from typing import Dict, List, Tuple
from ..ai import OllamaClient, AIQuery

logger = logging.getLogger(__name__)


class TodoPlanner:
    """Creates actionable plans from TODO analysis"""
    
    def __init__(self, client: OllamaClient, model: str = "gemma3:4b"):
        self.client = client
        self.model = model
        self.ai = AIQuery(client, model)
        self.project_root = None
    
    def set_project_root(self, project_root: Path):
        """Set the project root directory for tree generation"""
        self.project_root = Path(project_root)
    
    def _generate_project_tree(self) -> str:
        """Generate a comprehensive project tree showing all files and directories"""
        if not self.project_root or not self.project_root.exists():
            return "Project tree not available"
        
        tree_lines = []
        
        def add_to_tree(path: Path, prefix: str = "", is_last: bool = True):
            """Recursively build tree structure"""
            # Skip hidden files and common ignore patterns
            if path.name.startswith('.') or path.name in ['__pycache__', 'node_modules', '.git', 'venv', 'env']:
                return
            
            # Add current item
            connector = "└── " if is_last else "├── "
            tree_lines.append(f"{prefix}{connector}{path.name}")
            
            # If it's a directory, recurse into it
            if path.is_dir():
                try:
                    children = sorted([p for p in path.iterdir() 
                                     if not p.name.startswith('.') 
                                     and p.name not in ['__pycache__', 'node_modules', '.git', 'venv', 'env']])
                    
                    for i, child in enumerate(children):
                        is_child_last = (i == len(children) - 1)
                        extension = "    " if is_last else "│   "
                        add_to_tree(child, prefix + extension, is_child_last)
                except PermissionError:
                    pass
        
        tree_lines.append(f"{self.project_root.name}/")
        try:
            children = sorted([p for p in self.project_root.iterdir() 
                             if not p.name.startswith('.') 
                             and p.name not in ['__pycache__', 'node_modules', '.git', 'venv', 'env']])
            
            for i, child in enumerate(children):
                is_last = (i == len(children) - 1)
                add_to_tree(child, "", is_last)
        except PermissionError:
            tree_lines.append("Permission denied reading directory")
        
        return "\n".join(tree_lines)
    
    def _get_all_file_paths(self) -> List[str]:
        """Get a simple list of all file paths in the project"""
        if not self.project_root or not self.project_root.exists():
            return []
        
        file_paths = []
        text_extensions = {'.py', '.js', '.tsx', '.jsx', '.md', '.txt', '.json', 
                          '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf',
                          '.sh', '.bash', '.java', '.c', '.cpp', '.go', '.rs',
                          '.html', '.css', '.scss', '.sql', '.xml'}
        
        try:
            for file_path in self.project_root.rglob("*"):
                # Skip hidden directories and files
                if any(part.startswith('.') for part in file_path.parts):
                    continue
                # Skip common ignore patterns
                if any(ignore in str(file_path) for ignore in ['__pycache__', 'node_modules', '.git', 'venv', 'env']):
                    continue
                
                if file_path.is_file() and (file_path.suffix in text_extensions or file_path.suffix == ''):
                    relative_path = str(file_path.relative_to(self.project_root))
                    file_paths.append(relative_path)
        except Exception as e:
            logger.debug(f"Error scanning project files: {e}")
        
        return sorted(file_paths)

    def create_action_plan(self, analysis: Dict) -> Dict:
        """Create detailed action plan from TODO analysis"""
        logger.info("Creating action plan from TODO analysis")
        
        # Build comprehensive context
        context = self._build_planning_context(analysis)
        
        # Step 1: Create detailed plan
        plan = self._generate_detailed_plan(context, analysis['todo_content'])
        
        # Step 2: Extract branch name from plan
        branch_name = self._extract_branch_name(plan)
        
        # Step 3: Extract file list from plan  
        planned_files = self._extract_file_list_from_plan(plan)
        
        # Step 4: Collect concrete file paths based on the plan
        files_to_modify = self._collect_files_with_context(plan, planned_files)
        
        return {
            "plan": plan,
            "branch_name": branch_name,
            "files_to_modify": files_to_modify,
            "todo_excerpt": analysis['todo_content'][:500]
        }
    
    def _build_planning_context(self, analysis: Dict) -> str:
        """Build context from all analysis components with project tree"""
        parts = [
            "=== TODO CONTENTS ===",
            analysis['todo_content'][:2000],
            "",
            "=== SUMMARY OF CODE ANALYSIS ===",
            analysis['summary'],
            "",
            "=== CURRENT PROJECT STRUCTURE ===",
        ]
        
        # Add comprehensive project tree
        project_tree = self._generate_project_tree()
        parts.append(project_tree)
        parts.append("")
        parts.append("=== ALL AVAILABLE FILES ===")
        
        # Add list of all file paths
        all_files = self._get_all_file_paths()
        if all_files:
            parts.append(f"Total files: {len(all_files)}")
            # Show first 50 files to avoid overwhelming context
            for file_path in all_files[:50]:
                parts.append(f"  {file_path}")
            if len(all_files) > 50:
                parts.append(f"  ... and {len(all_files) - 50} more files")
        else:
            parts.append("No files found")
        
        parts.append("")
        parts.append("=== KEY INSIGHTS FROM CHUNKS ===")
        
        # Add first few chunk responses
        for i, response in enumerate(analysis['chunk_responses'][:3], 1):
            parts.append(f"Chunk {i}: {response[:500]}...")
        
        return "\n".join(parts)
    
    def _generate_detailed_plan(self, context: str, todo_content: str) -> str:
        """Generate detailed implementation plan"""
        prompt = """Based on the TODO and code analysis, create a COMPREHENSIVE action plan to complete ALL tasks in the TODO file.

CRITICAL INSTRUCTIONS:
1. You MUST attempt to complete the ENTIRE TODO file, not just one task
2. Analyze EVERY item in the TODO and determine what files are needed for COMPLETE implementation
3. List ALL files that need to be created/modified/deleted to accomplish EVERYTHING in the TODO
4. For each file, describe the specific changes needed to fulfill ALL related TODO requirements
5. Create a holistic strategy that addresses ALL interconnected TODO items simultaneously
6. Define success criteria that encompasses COMPLETION of the ENTIRE TODO list
7. Suggest a branch name that reflects the comprehensive nature of ALL changes

Be exhaustive and thorough. Name EVERY file needed across the ENTIRE codebase to complete ALL TODO items.
Think systematically about dependencies - if TODO item A requires changes to files X, Y, Z, and TODO item B requires changes to files Y, Z, W, then your plan must include ALL files: X, Y, Z, W.

Your goal is TOTAL COMPLETION of the TODO file. Do not leave any TODO item unaddressed."""
        
        result = self.ai.open(
            prompt=prompt,
            context=context,
            context_name="action_planning"
        )
        
        return result.content
    
    def _extract_branch_name(self, plan: str) -> str:
        """Extract or generate branch name from plan"""
        prompt = """Based on this COMPREHENSIVE plan to complete the ENTIRE TODO, suggest a git branch name.

Rules:
- Use format: type/description (e.g., feat/complete-todo, feat/implement-all-features)
- Lowercase with hyphens
- Max 30 characters
- Reflect that this implements MULTIPLE TODO items comprehensively
- Avoid overly specific names since this covers the ENTIRE TODO

Respond with ONLY the branch name, no explanation."""
        
        result = self.ai.single_word(
            question=prompt,
            context=f"Plan excerpt: {plan[:1000]}",
            context_name="branch_naming"
        )
        
        branch = result.word.strip().lower().replace(' ', '-')
        
        # Validate and sanitize
        if '/' not in branch:
            branch = f"feat/{branch}"
        
        return branch[:30]  # Enforce max length
    
    def _extract_file_list_from_plan(self, plan: str) -> List[str]:
        """Extract a list of files that need to be worked on from the detailed plan"""
        prompt = """Based on this COMPREHENSIVE action plan, list EVERY SINGLE FILE that needs to be modified, created, or deleted to COMPLETELY fulfill ALL tasks in the TODO.

CRITICAL EXTRACTION INSTRUCTIONS:
- You MUST list EVERY file mentioned or implied in the plan
- Include ALL files needed for COMPLETE implementation of ALL TODO items
- List each file on a separate line
- Use relative paths from the project root (e.g., src/main.py, not ./src/main.py)
- Include ALL existing files to modify AND ALL new files to create
- If a file needs to be deleted, prefix it with "DELETE: "
- If a file needs to be created, prefix it with "CREATE: "
- If a file needs to be modified, just list the path normally
- Be EXHAUSTIVE - do not skip any files that are needed
- Include test files, configuration files, documentation files if mentioned
- Think about ALL dependencies and related files needed for full implementation

Remember: The goal is COMPLETE implementation of the ENTIRE TODO.
If the plan mentions 20 files, list ALL 20 files.
If the plan implies additional helper files are needed, list those too.

Format each line as:
filename.ext
or
CREATE: new_file.py  
or
DELETE: old_file.js

List ALL the files:"""

        result = self.ai.open(
            prompt=prompt,
            context=f"Action Plan:\n{plan}",
            context_name="file_list_extraction"
        )
        
        # Parse the file list from the response
        file_lines = []
        for line in result.content.strip().split('\n'):
            line = line.strip()
            if line and not line.startswith('#') and not line.lower().startswith('list'):
                # Clean up any bullet points or numbering
                line = line.lstrip('- *123456789. ')
                if line:
                    file_lines.append(line)
        
        logger.info(f"Extracted {len(file_lines)} files from plan: {file_lines}")
        return file_lines
    
    def _collect_files_with_context(self, plan: str, planned_files: List[str]) -> List[Dict]:
        """Collect concrete file paths using multiple choice validation for each file"""
        logger.info(f"Collecting concrete file paths from {len(planned_files)} planned files")
        
        all_available_files = self._get_all_file_paths()
        project_tree = self._generate_project_tree()
        
        # Step 1: Process and clean planned files
        processed_files = []
        for planned_file in planned_files:
            logger.info(f"Processing planned file: {planned_file}")
            
            # Determine operation type
            operation = "EDIT"
            clean_file_path = planned_file
            
            if planned_file.startswith("DELETE: "):
                operation = "DELETE"
                clean_file_path = planned_file[8:].strip()
            elif planned_file.startswith("CREATE: "):
                operation = "CREATE"
                clean_file_path = planned_file[8:].strip()
            
            # For existing files, resolve the path
            if operation == "EDIT":
                actual_file_path = self._resolve_file_path_with_ai(
                    clean_file_path, all_available_files, project_tree, plan
                )
            else:
                # For CREATE/DELETE, use the path as specified
                actual_file_path = clean_file_path
            
            if actual_file_path and actual_file_path != "SKIP":
                # Validate that this is not a directory path
                if self._is_likely_directory_path(actual_file_path):
                    logger.warning(f"Skipping likely directory path: {actual_file_path}")
                    continue
                
                processed_files.append({
                    "path": actual_file_path,
                    "operation": operation,
                    "original": planned_file
                })
        
        # Step 2: Filter out files with spaces in their paths
        logger.info(f"Filtering out files with spaces from {len(processed_files)} files")
        valid_files = []
        filtered_out = []
        
        for file_info in processed_files:
            if ' ' in file_info['path']:
                filtered_out.append(file_info['path'])
                logger.warning(f"Filtered out file with spaces: {file_info['path']}")
            else:
                valid_files.append(file_info)
        
        if filtered_out:
            logger.info(f"Filtered out {len(filtered_out)} files with spaces: {filtered_out}")
        
        logger.info(f"Proceeding with {len(valid_files)} space-free files for validation")
        
        # Step 3: Validate each file individually with multiple choice
        verified_files = self._validate_files_individually(valid_files, plan, all_available_files, project_tree)
        
        # Step 4: Still allow AI to add additional files with the "DONE" loop
        final_files = self._collect_additional_files(plan, verified_files, all_available_files, project_tree)
        
        return final_files
    
    def _validate_files_individually(self, candidate_files: List[Dict], plan: str, 
                                   all_available_files: List[str], project_tree: str) -> List[Dict]:
        """Validate each file individually with yes/no multiple choice"""
        logger.info(f"Validating {len(candidate_files)} files individually with AI")
        
        verified_files = []
        
        for i, file_info in enumerate(candidate_files, 1):
            file_path = file_info['path']
            operation = file_info['operation']
            original = file_info['original']
            
            logger.info(f"Validating file {i}/{len(candidate_files)}: {file_path}")
            
            # Build comprehensive context for this specific file validation
            context_parts = [
                f"VALIDATING FILE: {file_path}",
                f"OPERATION: {operation}",
                f"ORIGINAL FROM PLAN: {original}",
                "",
                "=== ACTION PLAN ===",
                plan[:1500],
                "",
                "=== PROJECT STRUCTURE ===",
                project_tree[:1000],
                "",
                "=== ALL AVAILABLE FILES (sample) ===",
                "\n".join(f"  {f}" for f in all_available_files[:20])
            ]
            
            if len(all_available_files) > 20:
                context_parts.append(f"  ... and {len(all_available_files) - 20} more files")
            
            validation_context = "\n".join(context_parts)
            
            # Ask yes/no validation question with bias toward inclusion for comprehensive TODO completion
            question = f"Should {file_path} be included to ensure COMPLETE TODO implementation? (When in doubt, include it)"
            
            result = self.ai.multiple_choice(
                question=question,
                options=["YES - Include for comprehensive TODO completion", "NO - Not needed for TODO"],
                context=validation_context,
                context_name=f"validate_file_{i}"
            )
            
            if "YES" in result.value:
                verified_files.append({
                    "path": file_path,
                    "operation": operation,
                    "reason": f"AI validated: {original}"
                })
                logger.info(f"✅ File validated: {file_path} ({operation})")
            else:
                logger.info(f"❌ File rejected: {file_path} ({operation})")
        
        logger.info(f"File validation complete: {len(verified_files)}/{len(candidate_files)} files approved")
        return verified_files
    
    def _resolve_file_path_with_ai(self, intended_path: str, all_files: List[str], _project_tree: str, plan: str) -> str:
        """Use AI to resolve the intended file path to an actual existing file"""
        # Check if the path exists as-is
        if intended_path in all_files:
            return intended_path
        
        # Find similar files
        similar_files = []
        intended_lower = intended_path.lower()
        for file_path in all_files:
            if intended_lower in file_path.lower() or file_path.lower() in intended_lower:
                similar_files.append(file_path)
        
        # If we found exact or very similar matches, present them to AI
        if similar_files:
            # Limit to top 10 matches to avoid overwhelming the context
            similar_files = similar_files[:10]
            
            question = f"What is the exact path for '{intended_path}'? If none match, respond with 'SKIP'."
            
            files_list = '\n'.join(f'  {f}' for f in similar_files)
            context_text = f"""Intended file from plan: {intended_path}

Available similar files:
{files_list}

Plan context: {plan[:500]}...

Choose the EXACT file path from the list above, or type 'SKIP' if none are suitable."""
            
            result = self.ai.single_word(
                question=question,
                context=context_text,
                context_name="file_path_resolution"
            )
            
            selected_path = result.word
            
            # Validate the selection
            if selected_path in similar_files:
                return selected_path
            elif selected_path.upper() == "SKIP":
                logger.warning(f"AI chose to skip file: {intended_path}")
                return "SKIP"
        
        # If no similar files, ask AI if this should be a new file
        logger.warning(f"No existing file matches {intended_path}")
        return intended_path  # Treat as new file to create
    
    def _collect_additional_files(self, plan: str, current_files: List[Dict], 
                                  all_files: List[str], project_tree: str) -> List[Dict]:
        """Interactive loop for collecting any additional files beyond the plan"""
        logger.info("Checking if additional files are needed beyond the plan")
        
        files = current_files.copy()
        max_iterations = 20  # Increased limit for comprehensive TODO completion
        
        for i in range(max_iterations):
            selected_files = [f['path'] for f in files]
            
            # Build comprehensive context
            selected_files_text = '\n'.join(f'  {f} ({files[j]["operation"]})' for j, f in enumerate(selected_files)) if selected_files else '  None yet'
            available_files_text = '\n'.join(f'  {f}' for f in all_files[:50])  # Show more files
            more_files_text = f'  ... and {len(all_files) - 50} more files' if len(all_files) > 50 else ''
            
            context = f"""COMPREHENSIVE ACTION PLAN FOR ENTIRE TODO:
{plan}

FILES ALREADY SELECTED ({len(files)} files):
{selected_files_text}

PROJECT STRUCTURE:
{project_tree}

AVAILABLE FILES (first 50):
{available_files_text}
{more_files_text}

CRITICAL: We need to complete the ENTIRE TODO file. Review the plan carefully.
Are there ANY additional files needed to FULLY complete ALL TODO items?
Think about:
- Test files for new functionality
- Configuration files that need updates
- Helper/utility files that support the main changes
- Documentation files if mentioned in TODO
- Any dependency files

Respond with the exact relative file path (e.g., 'src/utils.py') or 'DONE' ONLY if you are ABSOLUTELY CERTAIN all files needed for COMPLETE TODO implementation are selected."""
            
            result = self.ai.single_word(
                question="Additional file needed or DONE?",
                context=context,
                context_name=f"additional_file_{i+1}"
            )
            
            response = result.word.strip()
            
            if response.upper() == "DONE":
                logger.info("AI indicated no more files needed")
                break
            
            # Validate and add the file (with space filtering)
            if response and response not in selected_files:
                # Resolve the file path
                actual_path = self._resolve_file_path_with_ai(response, all_files, project_tree, plan)
                
                if actual_path and actual_path != "SKIP" and actual_path not in selected_files:
                    # Filter out files with spaces
                    if ' ' in actual_path:
                        logger.warning(f"Rejected additional file with spaces: {actual_path}")
                        continue
                    
                    operation = self._determine_operation(actual_path, plan)
                    files.append({
                        "path": actual_path,
                        "operation": operation,
                        "reason": f"Additional file requested in iteration {i+1}"
                    })
                    logger.info(f"Added additional file: {actual_path} ({operation})")
            else:
                logger.warning(f"Skipping invalid or duplicate file: {response}")
        
        return files
    
    def _is_likely_directory_path(self, path: str) -> bool:
        """Check if a path is likely a directory (no extension, common directory names)"""
        import os.path
        
        # Check if it has no extension and is a common directory name
        common_dirs = {'src', 'lib', 'test', 'tests', 'docs', 'config', 'scripts', 'bin', 'data', 'assets'}
        
        # If it's just a directory name with no extension
        if '.' not in os.path.basename(path) and os.path.basename(path).lower() in common_dirs:
            return True
        
        # If it ends with a slash, it's definitely a directory
        if path.endswith('/') or path.endswith('\\'):
            return True
        
        # If it's a single word that's a common directory name
        if '/' not in path and '\\' not in path and path.lower() in common_dirs:
            return True
        
        return False
    
    def _parse_file_path(self, ai_response: str) -> str:
        """Parse file path from AI response"""
        # Remove common prefixes and clean up
        path = ai_response.strip()
        
        # Remove option markers if present
        for prefix in ["src/", "docs/", "config/", "tests/", "lib/"]:
            if prefix in path:
                # Extract everything after the first occurrence
                idx = path.find(prefix)
                path = path[idx:]
                break
        
        # Clean up the path
        path = path.replace(" ", "_").replace("(", "").replace(")", "")
        
        # Ensure it has an extension
        if '.' not in path.split('/')[-1]:
            # Guess extension based on directory
            if 'test' in path:
                path += '.py'
            elif 'doc' in path:
                path += '.md'
            elif 'config' in path or 'settings' in path:
                path += '.json'
            else:
                path += '.py'  # Default
        
        return path
    
    def _is_duplicate_file(self, file_path: str, existing_files: List[Dict]) -> bool:
        """Check if file path is already in the list of selected files"""
        existing_paths = [f['path'] for f in existing_files]
        
        # Check exact match
        if file_path in existing_paths:
            return True
        
        # Check normalized paths (remove leading/trailing slashes, case insensitive)
        normalized_new = file_path.strip('/').lower()
        for existing_path in existing_paths:
            normalized_existing = existing_path.strip('/').lower()
            if normalized_new == normalized_existing:
                return True
        
        return False
    
    def _determine_operation(self, file_path: str, plan: str) -> str:
        """Determine if file should be edited or deleted"""
        result = self.ai.multiple_choice(
            question=f"What operation for {file_path}?",
            options=["EDIT", "DELETE"],
            context=f"Based on plan: {plan[:500]}\n\nEDIT = Create new file or completely rewrite existing file\nDELETE = Remove the file"
        )
        
        return result.value