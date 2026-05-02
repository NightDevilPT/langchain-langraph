# scripts/build_context.py
import os
import fnmatch
import argparse
from pathlib import Path
from typing import List, Set


def read_gitignore(root_dir: Path) -> Set[str]:
    """Read .gitignore file and return set of patterns"""
    gitignore_path = root_dir / ".gitignore"
    patterns = set()
    
    if gitignore_path.exists():
        with open(gitignore_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    patterns.add(line)
    
    # Add common patterns to ignore
    default_patterns = {
        '.venv', 'venv', 'env', '__pycache__', '*.pyc', '.pytest_cache',
        '.git', '.idea', '.vscode', '*.log', '*.tmp', '*.bak',
        '.DS_Store', 'Thumbs.db', 'dist', 'build', '*.egg-info', 'scripts'
    }
    patterns.update(default_patterns)
    
    return patterns


def should_ignore(file_path: Path, root_dir: Path, patterns: Set[str]) -> bool:
    """Check if file should be ignored based on gitignore patterns"""
    rel_path = file_path.relative_to(root_dir)
    path_str = str(rel_path).replace('\\', '/')
    
    for pattern in patterns:
        # Handle directory patterns ending with /
        if pattern.endswith('/'):
            if fnmatch.fnmatch(path_str, pattern) or fnmatch.fnmatch(path_str + '/', pattern):
                return True
            # Check if path is inside directory pattern
            if path_str.startswith(pattern.rstrip('/') + '/'):
                return True
        else:
            if fnmatch.fnmatch(path_str, pattern):
                return True
            # Handle ** pattern
            if pattern.startswith('**/'):
                if fnmatch.fnmatch(path_str, pattern[3:]):
                    return True
    
    # Check if any parent directory should be ignored
    for parent in rel_path.parents:
        parent_str = str(parent).replace('\\', '/')
        for pattern in patterns:
            if pattern.endswith('/') and parent_str == pattern.rstrip('/'):
                return True
    
    return False


def collect_files(root_dir: Path, patterns: Set[str]) -> List[Path]:
    """Collect all files from directory that shouldn't be ignored"""
    files = []
    
    for root, dirs, filenames in os.walk(root_dir):
        root_path = Path(root)
        
        # Filter out ignored directories
        dirs[:] = [d for d in dirs if not should_ignore(root_path / d, root_dir, patterns)]
        
        for filename in filenames:
            file_path = root_path / filename
            if not should_ignore(file_path, root_dir, patterns):
                files.append(file_path)
    
    return sorted(files)


def create_context_file(output_path: Path, root_dir: Path, files: List[Path]):
    """Create a single context file with all file contents"""
    
    with open(output_path, 'w', encoding='utf-8') as out_file:
        # Write header
        out_file.write("=" * 80 + "\n")
        out_file.write("PROJECT CONTEXT FILE\n")
        out_file.write(f"Generated: {Path(__file__).parent.name}\n")
        out_file.write("=" * 80 + "\n\n")
        
        # Write project structure
        out_file.write("PROJECT STRUCTURE\n")
        out_file.write("-" * 80 + "\n")
        
        for file_path in files:
            rel_path = file_path.relative_to(root_dir)
            out_file.write(f"  {rel_path}\n")
        
        out_file.write("\n" + "=" * 80 + "\n\n")
        
        # Write file contents
        for file_path in files:
            rel_path = file_path.relative_to(root_dir)
            
            out_file.write(f"FILE: {rel_path}\n")
            out_file.write("-" * 80 + "\n")
            
            try:
                with open(file_path, 'r', encoding='utf-8') as in_file:
                    content = in_file.read()
                    out_file.write(content)
            except Exception as e:
                out_file.write(f"[ERROR: Could not read file - {e}]\n")
            
            out_file.write("\n" + "-" * 80 + "\n\n")


def main():
    parser = argparse.ArgumentParser(description='Build project context file')
    parser.add_argument('--output', '-o', default='project_context.txt',
                       help='Output file name (default: project_context.txt)')
    parser.add_argument('--dir', '-d', default='.',
                       help='Root directory to scan (default: current directory)')
    
    args = parser.parse_args()
    
    root_dir = Path(args.dir).resolve()
    output_path = root_dir / args.output
    
    if not root_dir.exists():
        print(f"Error: Directory '{root_dir}' does not exist")
        return
    
    print(f"Scanning directory: {root_dir}")
    print(f"Reading .gitignore patterns...")
    
    patterns = read_gitignore(root_dir)
    print(f"Found {len(patterns)} ignore patterns")
    
    print(f"Collecting files...")
    files = collect_files(root_dir, patterns)
    print(f"Found {len(files)} files to include")
    
    print(f"Creating context file: {output_path}")
    create_context_file(output_path, root_dir, files)
    
    print(f"\n✅ Done! Context file created at: {output_path}")
    print(f"Total files included: {len(files)}")


if __name__ == "__main__":
    main()