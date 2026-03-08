"""
Project Manager for LexiScholar
Handles project save/load operations.
"""

import json
import os
import shutil
import sqlite3
import re
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple
from __version__ import PROJECT_SCHEMA_VERSION

logger = logging.getLogger(__name__)


class ProjectManager:
    """Manages LexiScholar project files."""
    
    PROJECT_EXTENSION = ".lxs"
    PROJECT_VERSION = PROJECT_SCHEMA_VERSION  # From central __version__.py
    
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        
    def _get_projects_dir(self) -> Path:
        """Get the root projects directory."""
        import sys
        import os
        
        # Check if we are inside a frozen app (PyInstaller)
        if getattr(sys, 'frozen', False):
            # Prioritize AppData/LexiScholar/projects to match main.py
            appdata = os.environ.get('APPDATA')
            if appdata:
                return Path(appdata) / "LexiScholar" / "projects"
            return Path(sys.executable).parent / "projects"
        else:
            return Path(__file__).parent / "projects"

    def create_project(self, project_name: str, save_dir: Optional[str] = None) -> tuple[bool, str]:
        """
        Create a new project.
        
        Args:
            project_name: Name for the new project
            save_dir: Directory to save to (optional)
            
        Returns:
            Tuple of (success, message or new db path)
        """
        try:
            # Sanitize project name
            safe_name = re.sub(r'[^\w\s-]', '', project_name).strip()
            if not safe_name:
                return False, "Geçersiz proje adı."
            
            # Determine project directory with enhanced security
            if save_dir:
                base_path = Path(save_dir).resolve()
                
                # Enhanced path sanitization and validation
                try:
                    base_path_str = os.path.normcase(os.path.abspath(str(base_path)))
                    resolved_path_str = os.path.normcase(
                        os.path.abspath(os.path.join(str(base_path), safe_name))
                    )

                    if os.path.commonpath([base_path_str, resolved_path_str]) != base_path_str:
                        return False, "Güvenlik hatası: Klasör dışına çıkılamaz."

                    project_dir = Path(resolved_path_str)
                except (ValueError, OSError) as e:
                    return False, f"Geçersiz yol: {e}"
            else:
                projects_base = self._get_projects_dir()
                project_dir = projects_base / safe_name
                
                # Additional validation for default projects directory
                try:
                    base_path_str = os.path.normcase(os.path.abspath(str(projects_base.resolve())))
                    resolved_path_str = os.path.normcase(os.path.abspath(str(project_dir)))
                    if os.path.commonpath([base_path_str, resolved_path_str]) != base_path_str:
                        return False, "Güvenlik hatası: Proje dizini doğrulanamadı."
                except (ValueError, OSError):
                    return False, "Proje dizini oluşturulamadı."
            
            if project_dir.exists():
                return False, "Bu isimde bir proje zaten var."
            
            project_dir.mkdir(parents=True)
            
            # Initialize fresh database
            db_path = project_dir / "database.db"
            from database import init_db
            init_db(str(db_path))
            
            # Create project metadata
            metadata = {
                "version": self.PROJECT_VERSION,
                "name": project_name,
                "created": datetime.now().isoformat(),
                "last_modified": datetime.now().isoformat(),
                "stats": {"documents": 0, "codes": 0, "segments": 0}
            }
            
            metadata_path = project_dir / "project.json"
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            # Create marker file
            marker_path = project_dir / f"{project_name}{self.PROJECT_EXTENSION}"
            marker_path.touch()
            
            return True, str(db_path)
            
        except Exception as e:
            logger.error(f"Project creation failed: {e}")
            return False, f"Proje oluşturma hatası: {str(e)}"
    
    def create_snapshot(self) -> tuple[bool, str]:
        """
        Create a silent automated backup of the current database.
        Keeps only the last 5 snapshots to save space.
        """
        try:
            project_dir = self.db_path.parent
            backup_root = project_dir / "backups"
            backup_root.mkdir(exist_ok=True)
            
            # Timestamp for this snapshot
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            snapshot_path = backup_root / f"auto_snapshot_{ts}.db"
            
            # Backup using SQLite API
            source_conn = sqlite3.connect(str(self.db_path))
            dest_conn = sqlite3.connect(str(snapshot_path))
            source_conn.backup(dest_conn)
            dest_conn.close()
            source_conn.close()
            
            # Cleanup old snapshots (keep last 5)
            snapshots = sorted(list(backup_root.glob("auto_snapshot_*.db")))
            if len(snapshots) > 5:
                for old_snap in snapshots[:-5]:
                    old_snap.unlink()
            
            return True, str(snapshot_path)
        except Exception as e:
            logger.error(f"Snapshot creation failed: {e}")
            return False, str(e)

    def save_project(self, project_name: str, save_dir: Optional[str] = None) -> tuple[bool, str]:
        """
        Save the current project to a file.
        
        Args:
            project_name: Name for the project
            save_dir: Directory to save to (optional, uses current dir if not specified)
            
        Returns:
            Tuple of (success, message or file path)
        """
        try:
            # Sanitize project name
            safe_name = re.sub(r'[^\w\s-]', '', project_name).strip()
            if not safe_name:
                return False, "Geçersiz proje adı."

            # Create project directory
            if save_dir:
                try:
                    base_path_str = os.path.normcase(os.path.abspath(str(Path(save_dir).resolve())))
                    resolved_path_str = os.path.normcase(
                        os.path.abspath(os.path.join(base_path_str, safe_name))
                    )
                    if os.path.commonpath([base_path_str, resolved_path_str]) != base_path_str:
                        return False, "Güvenlik hatası: Klasör dışına çıkılamaz."
                    project_dir = Path(resolved_path_str)
                except (ValueError, OSError) as e:
                    return False, f"Geçersiz yol: {e}"
            else:
                projects_base = self._get_projects_dir()
                try:
                    base_path_str = os.path.normcase(os.path.abspath(str(projects_base.resolve())))
                    resolved_path_str = os.path.normcase(
                        os.path.abspath(os.path.join(base_path_str, safe_name))
                    )
                    if os.path.commonpath([base_path_str, resolved_path_str]) != base_path_str:
                        return False, "Güvenlik hatası: Proje dizini doğrulanamadı."
                    project_dir = Path(resolved_path_str)
                except (ValueError, OSError) as e:
                    return False, f"Geçersiz yol: {e}"
            
            project_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy database using SQLite backup API (avoids file lock on Windows)
            db_dest = project_dir / "database.db"
            
            # Skip copy if source and destination are the same file
            if self.db_path.resolve() != db_dest.resolve():
                source_conn = sqlite3.connect(str(self.db_path))
                dest_conn = sqlite3.connect(str(db_dest))
                source_conn.backup(dest_conn)
                dest_conn.close()
                source_conn.close()
            
            # Create project metadata
            metadata = {
                "version": self.PROJECT_VERSION,
                "name": project_name,
                "created": datetime.now().isoformat(),
                "last_modified": datetime.now().isoformat(),
                "stats": self._get_project_stats()
            }
            
            metadata_path = project_dir / "project.json"
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            # Create marker file
            marker_path = project_dir / f"{safe_name}{self.PROJECT_EXTENSION}"
            marker_path.touch()
            
            return True, str(project_dir)
            
        except Exception as e:
            logger.error(f"Save project failed: {e}")
            return False, f"Kaydetme hatası: {str(e)}"
    
    def load_project(self, project_path: str) -> tuple[bool, str]:
        """
        Load a project from a file.
        
        Args:
            project_path: Path to the project directory or .lxs file
            
        Returns:
            Tuple of (success, message or new db path)
        """
        try:
            project_path = Path(project_path)
            
            # Handle .lxs file or directory
            if project_path.suffix == self.PROJECT_EXTENSION:
                project_dir = project_path.parent
            else:
                project_dir = project_path
            
            # Check for database
            db_source = project_dir / "database.db"
            if not db_source.exists():
                return False, "Proje veritabanı bulunamadı."
            
            # Load metadata
            metadata_path = project_dir / "project.json"
            if metadata_path.exists():
                try:
                    with open(metadata_path, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                except (json.JSONDecodeError, ValueError) as e:
                    logger.error(f"Metadata file corrupted: {metadata_path} - {e}")
                    return False, f"Proje metadata dosyası bozuk: {e}"
            else:
                metadata = {"name": project_dir.name}
            
            # Run migrations on load to ensure schema is up-to-date
            try:
                from database import init_db
                init_db(str(db_source))
            except Exception as e:
                logger.error(f"Migration failed during load for {db_source}: {e}")

            # For load, we return the path directly to use instantly
            # We don't copy back to root db for now, we switch context
            return True, str(db_source)
            
        except Exception as e:
            logger.error(f"Load project failed: {e}")
            return False, f"Yükleme hatası: {str(e)}"
    
    def _get_project_stats(self) -> dict:
        """Get statistics about the current project."""
        try:
            from database.connection import get_db_connection
            with get_db_connection(str(self.db_path)) as conn:
                cursor = conn.cursor()

                stats = {}

                cursor.execute("SELECT COUNT(*) FROM documents")
                stats['documents'] = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM codes")
                stats['codes'] = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM coded_segments")
                stats['segments'] = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM memos")
                stats['memos'] = cursor.fetchone()[0]

            return stats

        except Exception as e:
            logger.warning(f"_get_project_stats failed: {e}")
            return {}
    
    def get_recent_projects(self, projects_dir: Optional[str] = None) -> list:
        """
        Get list of recent projects.
        
        Args:
            projects_dir: Directory to scan for projects
            
        Returns:
            List of project info dicts
        """
        if projects_dir:
            base_dir = Path(projects_dir)
        else:
            base_dir = self._get_projects_dir()
        
        if not base_dir.exists():
            return []
        
        projects = []
        
        for item in base_dir.iterdir():
            if item.is_dir():
                metadata_path = item / "project.json"
                if metadata_path.exists():
                    try:
                        with open(metadata_path, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                        
                        projects.append({
                            'path': str(item),
                            'name': metadata.get('name', item.name),
                            'last_modified': metadata.get('last_modified', ''),
                            'stats': metadata.get('stats', {})
                        })
                    except Exception:
                        continue
        
        # Sort by last modified, most recent first
        projects.sort(key=lambda x: x.get('last_modified', ''), reverse=True)
        
        return projects
    
    def export_project_backup(self, backup_path: str) -> tuple[bool, str]:
        """
        Create a ZIP backup of the current project.
        
        Args:
            backup_path: Path for the backup file
            
        Returns:
            Tuple of (success, message)
        """
        try:
            import zipfile
            
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                # Add database
                zf.write(self.db_path, "database.db")
                
                # Add metadata
                metadata = {
                    "version": self.PROJECT_VERSION,
                    "backup_date": datetime.now().isoformat(),
                    "stats": self._get_project_stats()
                }
                zf.writestr("backup_info.json", json.dumps(metadata, ensure_ascii=False, indent=2))
            
            return True, backup_path
            
        except Exception as e:
            logger.error(f"Backup export failed: {e}")
            return False, f"Yedekleme hatası: {str(e)}"
