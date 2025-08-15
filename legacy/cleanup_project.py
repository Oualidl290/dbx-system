#!/usr/bin/env python3
"""
Project File Analysis Script - Interactive Cleanup
Lists duplicated and unused files, asks for individual confirmation before deletion
"""

import os
import shutil
import sys
from pathlib import Path

def get_file_size(file_path):
    """Get file size in human readable format"""
    try:
        size = os.path.getsize(file_path)
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    except:
        return "Unknown"

def get_file_info(file_path):
    """Get file information"""
    if os.path.exists(file_path):
        size = get_file_size(file_path)
        modified = os.path.getmtime(file_path)
        import datetime
        mod_time = datetime.datetime.fromtimestamp(modified).strftime('%Y-%m-%d %H:%M')
        return f"Size: {size}, Modified: {mod_time}"
    return "File not found"

def ask_delete_file(file_path, reason):
    """Ask user if they want to delete a specific file"""
    if not os.path.exists(file_path):
        print(f"⚠️ File not found: {file_path}")
        return False
    
    info = get_file_info(file_path)
    print(f"\n📄 File: {file_path}")
    print(f"   Info: {info}")
    print(f"   Reason: {reason}")
    
    while True:
        response = input(f"   Delete this file? (y/n/s=skip all): ").lower().strip()
        if response == 'y':
            try:
                os.remove(file_path)
                print(f"   ✅ Deleted: {file_path}")
                return True
            except Exception as e:
                print(f"   ❌ Error deleting: {e}")
                return False
        elif response == 'n':
            print(f"   ⏭️ Skipped: {file_path}")
            return False
        elif response == 's':
            print(f"   ⏭️ Skipping all remaining files...")
            return 'skip_all'
        else:
            print("   Please enter 'y' for yes, 'n' for no, or 's' to skip all")

def ask_delete_directory(dir_path, reason):
    """Ask user if they want to delete a directory"""
    if not os.path.exists(dir_path):
        print(f"⚠️ Directory not found: {dir_path}")
        return False
    
    try:
        # Count files in directory
        file_count = sum([len(files) for r, d, files in os.walk(dir_path)])
        dir_count = sum([len(dirs) for r, dirs, f in os.walk(dir_path)]) - 1  # Exclude root
        
        print(f"\n📁 Directory: {dir_path}")
        print(f"   Contains: {file_count} files, {dir_count} subdirectories")
        print(f"   Reason: {reason}")
        
        while True:
            response = input(f"   Delete this directory? (y/n): ").lower().strip()
            if response == 'y':
                try:
                    shutil.rmtree(dir_path)
                    print(f"   ✅ Deleted directory: {dir_path}")
                    return True
                except Exception as e:
                    print(f"   ❌ Error deleting directory: {e}")
                    return False
            elif response == 'n':
                print(f"   ⏭️ Skipped directory: {dir_path}")
                return False
            else:
                print("   Please enter 'y' for yes or 'n' for no")
    except Exception as e:
        print(f"   ❌ Error analyzing directory: {e}")
        return False

def main():
    print("🔍 DBX AI Project File Analysis")
    print("=" * 50)
    print("This script will analyze your project and ask about each duplicate/unused file individually.")
    print("You can choose to delete, keep, or skip each file.")
    
    input("\nPress Enter to start analysis...")
    
    # Track statistics
    deleted_files = 0
    deleted_dirs = 0
    skipped_files = 0
    skip_all = False
    
    # 1. Analyze duplicate build scripts
    print("\n" + "=" * 50)
    print("📦 DUPLICATE BUILD SCRIPTS")
    print("=" * 50)
    
    duplicate_build_scripts = [
        ("build_docker.sh", "Duplicate of build_docker.bat (Linux version, not needed on Windows)"),
        ("build_and_push.py", "Complex Python version, build_docker.bat is simpler and works")
    ]
    
    for script, reason in duplicate_build_scripts:
        if skip_all:
            break
        result = ask_delete_file(script, reason)
        if result == 'skip_all':
            skip_all = True
        elif result:
            deleted_files += 1
        else:
            skipped_files += 1
    
    # 2. Analyze duplicate push scripts
    if not skip_all:
        print("\n" + "=" * 50)
        print("📤 DUPLICATE PUSH SCRIPTS")
        print("=" * 50)
        
        duplicate_push_scripts = [
            ("push_docker_alt.bat", "Alternative version, push_docker.bat is the working one"),
            ("docker_hub_simple.bat", "Simple version, redundant with main push script"),
            ("create_and_push.bat", "Combined script, separate scripts are clearer"),
            ("fix_docker_hub.bat", "Troubleshooting script, no longer needed")
        ]
        
        for script, reason in duplicate_push_scripts:
            if skip_all:
                break
            result = ask_delete_file(script, reason)
            if result == 'skip_all':
                skip_all = True
            elif result:
                deleted_files += 1
            else:
                skipped_files += 1
    
    # 3. Analyze duplicate sharing scripts
    if not skip_all:
        print("\n" + "=" * 50)
        print("📋 DUPLICATE SHARING SCRIPTS")
        print("=" * 50)
        
        duplicate_sharing_scripts = [
            ("share_offline.bat", "Uses gzip which doesn't work on Windows, save_image_windows.bat works")
        ]
        
        for script, reason in duplicate_sharing_scripts:
            if skip_all:
                break
            result = ask_delete_file(script, reason)
            if result == 'skip_all':
                skip_all = True
            elif result:
                deleted_files += 1
            else:
                skipped_files += 1
    
    # 4. Analyze duplicate documentation
    if not skip_all:
        print("\n" + "=" * 50)
        print("📚 DUPLICATE DOCUMENTATION")
        print("=" * 50)
        
        duplicate_docs = [
            ("DOCKER_SHARING_GUIDE.md", "Content merged into SHARING_GUIDE_FINAL.md"),
            ("SHARE_WITH_FRIENDS.md", "Content merged into SHARING_GUIDE_FINAL.md"),
            ("FINAL_DOCKER_SUMMARY.md", "Content merged into README.md"),
            ("SECURITY_IMPROVEMENTS.md", "Content merged into SECURITY_GUIDE.md"),
            ("SETUP_GUIDE.md", "Content merged into README.md"),
            ("QUICK_START.txt", "Content merged into README.md"),
            ("CLEANUP_SUMMARY.md", "Temporary file, no longer needed")
        ]
        
        for doc, reason in duplicate_docs:
            if skip_all:
                break
            result = ask_delete_file(doc, reason)
            if result == 'skip_all':
                skip_all = True
            elif result:
                deleted_files += 1
            else:
                skipped_files += 1
    
    # 5. Analyze unused/obsolete files
    if not skip_all:
        print("\n" + "=" * 50)
        print("🗑️ UNUSED/OBSOLETE FILES")
        print("=" * 50)
        
        unused_files = [
            ("dbx-ai-system.tar.gz", "Failed compressed version (gzip doesn't work on Windows)"),
            ("cleanup_unused.py", "Old temporary cleanup script")
        ]
        
        for file, reason in unused_files:
            if skip_all:
                break
            result = ask_delete_file(file, reason)
            if result == 'skip_all':
                skip_all = True
            elif result:
                deleted_files += 1
            else:
                skipped_files += 1
    
    # 6. Analyze nested git repository
    if not skip_all:
        print("\n" + "=" * 50)
        print("📁 PROBLEMATIC DIRECTORIES")
        print("=" * 50)
        
        if ask_delete_directory("dbx_system", "Nested git repository causing conflicts, duplicate of main project"):
            deleted_dirs += 1
    
    # 7. Check for Python cache directories
    if not skip_all:
        print("\n" + "=" * 50)
        print("🐍 PYTHON CACHE DIRECTORIES")
        print("=" * 50)
        
        cache_dirs = []
        for root, dirs, files in os.walk("."):
            if "__pycache__" in dirs:
                cache_dirs.append(os.path.join(root, "__pycache__"))
        
        for cache_dir in cache_dirs:
            if ask_delete_directory(cache_dir, "Python cache directory, automatically regenerated"):
                deleted_dirs += 1
    
    # Final summary
    print("\n" + "=" * 60)
    print("🎉 ANALYSIS COMPLETE!")
    print("=" * 60)
    print(f"✅ Files deleted: {deleted_files}")
    print(f"📁 Directories deleted: {deleted_dirs}")
    print(f"⏭️ Files skipped: {skipped_files}")
    
    # Verify essential files still exist
    print("\n🔍 Verifying essential files are still present...")
    essential_files = [
        "README.md",
        "docker-compose.yml",
        "deploy.py", 
        "build_docker.bat",
        "push_docker.bat",
        "simple_evaluation.py",
        "dbx-ai-system.tar"
    ]
    
    missing_files = []
    for file in essential_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ MISSING: {file}")
            missing_files.append(file)
    
    if not missing_files:
        print("\n🎯 All essential files are safe!")
        print("📊 Your project structure is now cleaner!")
        
        if deleted_files > 0 or deleted_dirs > 0:
            print("\n💡 Recommended next steps:")
            print("1. Test key functionality: python deploy.py")
            print("2. Verify Docker build: .\\build_docker.bat")
            print("3. Check that all documentation links work")
            print("4. Commit changes: git add . && git commit -m 'Clean up duplicate and unused files'")
    else:
        print(f"\n⚠️ WARNING: {len(missing_files)} essential files are missing!")
        print("Please check what happened to these files.")
    
    # Show current project structure
    print(f"\n📁 Current project structure:")
    try:
        files = [f for f in os.listdir(".") if os.path.isfile(f) and not f.startswith('.')]
        dirs = [d for d in os.listdir(".") if os.path.isdir(d) and not d.startswith('.')]
        print(f"   Files: {len(files)}")
        print(f"   Directories: {len(dirs)}")
        
        if len(files) <= 20:  # Only show if not too many
            print(f"\n📄 Files in root directory:")
            for file in sorted(files):
                size = get_file_size(file)
                print(f"   • {file} ({size})")
    except Exception as e:
        print(f"   Error listing directory: {e}")

if __name__ == "__main__":
    main()