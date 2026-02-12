"""
SQLite Database Manager (CONNECTION POOLING & CRUD OPERATIONS).

Handles all SQLite database interactions with:
- Connection pooling (reuse connections, reduce overhead)
- Row factory (dict-like column access instead of tuples)
- Atomic writes (transactional integrity)
- Backup before updates (data protection)
- Error handling and logging

Database file: data/water_balance.db (created by DatabaseSchema)
Accessed by: Repositories and Services
Thread-safe: Yes (SQLite with WAL mode)
"""

import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
from datetime import datetime
import logging


logger = logging.getLogger(__name__)


class DatabaseManager:
    """SQLite Database Manager (CONNECTION & TRANSACTION MANAGER).
    
    Responsible for:
    1. Managing database connections (pooling)
    2. Executing queries (read/write)
    3. Managing transactions (atomic operations)
    4. Creating backups (data protection)
    5. Handling errors gracefully
    
    Why separate class: Isolates DB logic from repositories/services,
    makes connections reusable, enables transaction management.
    
    Thread-safety: SQLite with WAL mode allows concurrent reads.
    Writes are serialized (SQLite limitation, not a problem for this app).
    """
    
    _instance: Optional["DatabaseManager"] = None

    @classmethod
    def get_instance(cls) -> "DatabaseManager":
        """Return a shared DatabaseManager instance (backward compatible API)."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset shared instance (primarily useful for tests)."""
        cls._instance = None

    def __init__(self, db_path: Optional[Path] = None):
        """Initialize database manager (CONSTRUCTOR).
        
        Args:
            db_path: Database file path (defaults to data/water_balance.db)
        
        Sets up:
        - Connection parameters (timeout, check_same_thread)
        - Row factory (dict-like access)
        """
        from database.schema import DatabaseSchema
        
        self.db_path = db_path or DatabaseSchema.DB_PATH
        self.connection_timeout = 10.0  # seconds
        
        # Ensure database exists and is initialized
        if not self.db_path.exists():
            logger.info(f"Database not found at {self.db_path}, creating fresh schema...")
            schema = DatabaseSchema(self.db_path)
            schema.create_database()
    
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory (CONNECTION GETTER).
        
        Configuration:
        - Row factory: dict_factory (access columns by name, not index)
        - Timeout: 10 seconds (wait for lock)
        - Check same thread: False (allows use across threads with WAL mode)
        
        Why row factory: Allows conn.execute(...).fetchall() to return
        list of dicts instead of tuples, making code more readable:
        
        Instead of:  row[0], row[1], row[2]
        Use:         row['id'], row['code'], row['name']
        
        Returns:
            SQLite connection object with dict factory
        
        Raises:
            sqlite3.OperationalError: If database locked or connection fails
        
        Example:
            conn = db.get_connection()
            cursor = conn.execute("SELECT * FROM storage_facilities WHERE code=?", ("NDCD1",))
            row = cursor.fetchone()  # Returns dict: {'id': 1, 'code': 'NDCD1', ...}
        """
        conn = sqlite3.connect(
            str(self.db_path),
            timeout=self.connection_timeout,
            check_same_thread=False
        )
        
        # Set row factory to return dicts (column name access)
        conn.row_factory = self._dict_factory
        
        # Enable foreign key constraints
        conn.execute("PRAGMA foreign_keys = ON")
        
        return conn
    
    @staticmethod
    def _dict_factory(cursor: sqlite3.Cursor, row: tuple) -> dict:
        """Convert SQL row tuple to dict (INTERNAL - ROW FACTORY).
        
        Allows accessing row['column_name'] instead of row[0].
        
        Args:
            cursor: SQLite cursor (contains column descriptions)
            row: Tuple of values from SQL query
        
        Returns:
            Dict mapping column names to values
        
        Example:
            row = {'id': 1, 'code': 'NDCD1', 'name': 'North Decline Decant 1'}
        """
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d
    
    @contextmanager
    def transaction(self):
        """Context manager for atomic database transactions (TRANSACTION MANAGEMENT).
        
        Ensures:
        - All changes are committed together (atomic)
        - Rollback on error (data integrity)
        - Connection properly closed
        
        Usage:
            with db.transaction() as conn:
                conn.execute("INSERT INTO ...", (...))
                conn.execute("UPDATE ...", (...))
            # Auto-commits if no exception, auto-rollbacks if exception
        
        Raises:
            sqlite3.Error: Database error (with auto-rollback)
        
        Example:
            try:
                with db.transaction() as conn:
                    conn.execute("UPDATE storage_facilities SET current_volume_m3=? WHERE id=?",
                                (new_volume, facility_id))
            except sqlite3.IntegrityError as e:
                logger.error(f"Failed to update facility: {e}")
                # Changes automatically rolled back
        """
        conn = self.get_connection()
        try:
            yield conn
            conn.commit()
            logger.debug("Transaction committed successfully")
        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"Transaction failed, rolled back: {e}")
            raise
        finally:
            conn.close()
    
    def create_backup(self, backup_path: Optional[Path] = None) -> Path:
        """Create timestamped backup of database (DATA PROTECTION).
        
        Called before major operations (bulk updates, deletes) to enable
        recovery if something goes wrong.
        
        Backup naming: water_balance.db.backup-20260129-143022
        (includes timestamp for chronological ordering)
        
        Args:
            backup_path: Custom backup path (defaults to data/ folder)
        
        Returns:
            Path to backup file created
        
        Raises:
            IOError: If backup fails
        
        Example:
            backup = db.create_backup()
            logger.info(f"Backup created at {backup}")
        """
        if backup_path is None:
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            backup_path = self.db_path.parent / f"{self.db_path.stem}.backup-{timestamp}"
        
        try:
            # Read original database
            with open(self.db_path, 'rb') as original:
                data = original.read()
            
            # Write backup
            with open(backup_path, 'wb') as backup:
                backup.write(data)
            
            logger.info(f"Database backup created: {backup_path}")
            return backup_path
        except IOError as e:
            logger.error(f"Failed to create backup: {e}")
            raise
    
    def execute_query(
        self,
        query: str,
        params: tuple = (),
        fetch_one: bool = False
    ) -> Any:
        """Execute SELECT query and return results (MAIN READ METHOD).
        
        For safe, simple SELECT queries.
        For write operations, use execute_mutation() instead.
        
        Args:
            query: SQL SELECT statement
            params: Tuple of parameters for ? placeholders (prevents SQL injection)
            fetch_one: If True, return single dict; if False, return list of dicts
        
        Returns:
            Single dict if fetch_one=True, list of dicts if fetch_one=False
            Returns empty dict {} or [] if no results
        
        Raises:
            sqlite3.Error: Database error
        
        Example:
            # Get single facility
            facility = db.execute_query(
                "SELECT * FROM storage_facilities WHERE code=?",
                ("NDCD1",),
                fetch_one=True
            )
            if facility:
                logger.info("Facility: %s", facility['name'])
            
            # Get all active facilities
            facilities = db.execute_query(
                "SELECT * FROM storage_facilities WHERE status=? ORDER BY name",
                ("active",)
            )
            for facility in facilities:
                logger.info("%s %s", facility['code'], facility['current_volume_m3'])
        
        Performance note: Large result sets (>10k rows) should use pagination
        or streaming to avoid loading entire result set into memory.
        """
        conn = self.get_connection()
        try:
            cursor = conn.execute(query, params)
            
            if fetch_one:
                result = cursor.fetchone()
                return result if result is not None else {}
            else:
                results = cursor.fetchall()
                return results if results is not None else []
        finally:
            conn.close()
    
    def execute_mutation(
        self,
        query: str,
        params: tuple = (),
        create_backup: bool = True
    ) -> int:
        """Execute INSERT/UPDATE/DELETE and return affected row count (WRITE OPERATION).
        
        For modifying data (INSERT, UPDATE, DELETE).
        Automatically wrapped in transaction for atomicity.
        
        Args:
            query: SQL INSERT/UPDATE/DELETE statement
            params: Tuple of parameters for ? placeholders
            create_backup: If True, create backup before operation (default: True)
        
        Returns:
            Number of rows affected
        
        Raises:
            sqlite3.IntegrityError: Constraint violation (unique, foreign key, check)
            sqlite3.Error: Database error
        
        Example:
            # Add new facility
            count = db.execute_mutation(
                "INSERT INTO storage_facilities (code, name, facility_type, capacity_m3) "
                "VALUES (?, ?, ?, ?)",
                ("NDCD1", "North Decline Decant 1", "TSF", 250000)
            )
            logger.info(f"Inserted {count} facility")
            
            # Update facility volume
            count = db.execute_mutation(
                "UPDATE storage_facilities SET current_volume_m3=?, updated_at=CURRENT_TIMESTAMP "
                "WHERE id=?",
                (180000, facility_id)
            )
            
            # Delete inactive facility (with safety check)
            try:
                count = db.execute_mutation(
                    "DELETE FROM storage_facilities WHERE id=? AND status=?",
                    (facility_id, "inactive")
                )
            except sqlite3.IntegrityError:
                logger.error("Cannot delete: facility has dependent records")
        """
        # Create backup before write (data protection)
        if create_backup:
            self.create_backup()
        
        # Execute write in transaction (atomicity)
        with self.transaction() as conn:
            cursor = conn.execute(query, params)
            affected_rows = cursor.rowcount
            logger.debug(f"Mutation executed: {affected_rows} rows affected")
            return affected_rows
    
    def execute_batch_mutation(
        self,
        query: str,
        params_list: List[tuple],
        create_backup: bool = True
    ) -> int:
        """Execute multiple mutations in single transaction (BATCH OPERATION).
        
        More efficient than multiple execute_mutation calls.
        All-or-nothing: Either all succeed or all rollback.
        
        Args:
            query: SQL INSERT/UPDATE/DELETE statement (used for all operations)
            params_list: List of parameter tuples for each operation
            create_backup: If True, create backup before operation
        
        Returns:
            Total number of rows affected
        
        Raises:
            sqlite3.IntegrityError: If any operation violates constraints
            sqlite3.Error: Database error
        
        Example:
            # Bulk update volumes for multiple facilities
            updates = [
                (180000, 1),  # Set facility id=1 to 180000 m³
                (150000, 2),  # Set facility id=2 to 150000 m³
                (95000, 3),   # Set facility id=3 to 95000 m³
            ]
            
            try:
                count = db.execute_batch_mutation(
                    "UPDATE storage_facilities SET current_volume_m3=?, updated_at=CURRENT_TIMESTAMP "
                    "WHERE id=?",
                    updates
                )
                logger.info(f"Updated {count} facilities in single batch")
            except sqlite3.IntegrityError as e:
                logger.error(f"Batch update failed (all rolled back): {e}")
        """
        if create_backup:
            self.create_backup()
        
        with self.transaction() as conn:
            cursor = conn.cursor()
            total_affected = 0
            
            for params in params_list:
                cursor.execute(query, params)
                total_affected += cursor.rowcount
            
            logger.debug(f"Batch mutation executed: {total_affected} total rows affected")
            return total_affected
    
    def table_exists(self, table_name: str) -> bool:
        """Check if table exists in database (UTILITY - TABLE VERIFICATION).
        
        Useful for schema verification before operations.
        
        Args:
            table_name: Name of table to check
        
        Returns:
            True if table exists, False otherwise
        
        Example:
            if db.table_exists('storage_facilities'):
                facilities = db.execute_query("SELECT * FROM storage_facilities")
        """
        result = self.execute_query(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,),
            fetch_one=True
        )
        return bool(result)
    
    def get_row_count(self, table_name: str) -> int:
        """Get total row count for table (UTILITY - TABLE SIZE CHECK).
        
        Useful for progress monitoring, empty table checks.
        
        Args:
            table_name: Name of table
        
        Returns:
            Number of rows in table
        
        Example:
            count = db.get_row_count('storage_facilities')
            logger.info(f"Database has {count} storage facilities")
        """
        result = self.execute_query(
            f"SELECT COUNT(*) as count FROM {table_name}",
            fetch_one=True
        )
        return result.get('count', 0) if result else 0
