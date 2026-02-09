"""
Supabase Client Wrapper

Provides a simple REST API client for communicating with Supabase.
Handles authentication, retries, and error handling.

(IMPORTS)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import logging
import os
import urllib.request
import urllib.error
import urllib.parse
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


# (CONFIGURATION)

def _load_config_values():
    """Load Supabase config from app_config.yaml."""
    try:
        from core.config_manager import ConfigManager
        config = ConfigManager()
        url = config.get('supabase.url', '')
        key = config.get('supabase.anon_key', '')
        return url, key
    except Exception:
        return '', ''

# Supabase configuration - loaded from environment, config, or runtime
_config_url, _config_key = '', ''
try:
    _config_url, _config_key = _load_config_values()
except Exception:
    pass

SUPABASE_URL = os.environ.get('SUPABASE_URL', '') or _config_url
SUPABASE_ANON_KEY = os.environ.get('SUPABASE_ANON_KEY', '') or _config_key

# Request timeout in seconds
REQUEST_TIMEOUT = 30


# (EXCEPTIONS)

class SupabaseError(Exception):
    """Base exception for Supabase errors."""
    pass


class SupabaseConnectionError(SupabaseError):
    """Raised when unable to connect to Supabase."""
    pass


class SupabaseAPIError(SupabaseError):
    """Raised when Supabase API returns an error."""
    def __init__(self, message: str, status_code: int = 0, details: str = ""):
        super().__init__(message)
        self.status_code = status_code
        self.details = details


# (SUPABASE CLIENT)

class SupabaseClient:
    """
    Lightweight Supabase REST API client.
    
    Uses only standard library (urllib) to avoid external dependencies.
    Supports basic CRUD operations on Supabase tables.
    """
    
    def __init__(
        self,
        url: Optional[str] = None,
        anon_key: Optional[str] = None
    ):
        """
        Initialize Supabase client.
        
        Args:
            url: Supabase project URL. Falls back to SUPABASE_URL env var.
            anon_key: Supabase anon key. Falls back to SUPABASE_ANON_KEY env var.
        """
        self.url = (url or SUPABASE_URL).rstrip('/')
        self.anon_key = anon_key or SUPABASE_ANON_KEY
        
        if not self.url:
            logger.warning("Supabase URL not configured")
        if not self.anon_key:
            logger.warning("Supabase anon key not configured")
    
    @property
    def is_configured(self) -> bool:
        """Check if Supabase credentials are configured."""
        return bool(self.url and self.anon_key)
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication."""
        return {
            "apikey": self.anon_key,
            "Authorization": f"Bearer {self.anon_key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict[str, str]] = None
    ) -> Any:
        """
        Make an HTTP request to Supabase.
        
        Args:
            method: HTTP method (GET, POST, PATCH, DELETE).
            endpoint: API endpoint path.
            data: Request body data (for POST/PATCH).
            params: Query parameters.
            
        Returns:
            Parsed JSON response.
            
        Raises:
            SupabaseConnectionError: If unable to connect.
            SupabaseAPIError: If API returns an error.
        """
        if not self.is_configured:
            raise SupabaseConnectionError("Supabase not configured")
        
        # Build URL
        url = f"{self.url}/rest/v1/{endpoint}"
        if params:
            query_string = urllib.parse.urlencode(params)
            url = f"{url}?{query_string}"
        
        # Prepare request
        headers = self._get_headers()
        body = json.dumps(data).encode('utf-8') if data else None
        
        request = urllib.request.Request(
            url,
            data=body,
            headers=headers,
            method=method
        )
        
        try:
            with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:
                response_data = response.read().decode('utf-8')
                if response_data:
                    return json.loads(response_data)
                return None
                
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8') if e.fp else ""
            logger.error(f"Supabase API error: {e.code} - {error_body}")
            raise SupabaseAPIError(
                f"API error: {e.reason}",
                status_code=e.code,
                details=error_body
            )
        except urllib.error.URLError as e:
            logger.error(f"Supabase connection error: {e.reason}")
            raise SupabaseConnectionError(f"Connection failed: {e.reason}")
        except Exception as e:
            logger.error(f"Supabase request failed: {e}")
            raise SupabaseError(f"Request failed: {e}")

    def invoke_function(self, function_name: str, payload: Dict[str, Any]) -> Any:
        """Invoke a Supabase Edge Function with a JSON payload."""
        if not self.is_configured:
            raise SupabaseConnectionError("Supabase not configured")

        url = f"{self.url}/functions/v1/{function_name}"
        headers = {
            "apikey": self.anon_key,
            "Authorization": f"Bearer {self.anon_key}",
            "Content-Type": "application/json",
        }
        body = json.dumps(payload).encode("utf-8")

        request = urllib.request.Request(
            url,
            data=body,
            headers=headers,
            method="POST"
        )

        try:
            with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:
                response_data = response.read().decode("utf-8")
                return json.loads(response_data) if response_data else None
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8") if e.fp else ""
            logger.error(f"Supabase function error: {e.code} - {error_body}")
            raise SupabaseAPIError(
                f"Function error: {e.reason}",
                status_code=e.code,
                details=error_body
            )
        except urllib.error.URLError as e:
            logger.error(f"Supabase function connection error: {e.reason}")
            raise SupabaseConnectionError(f"Connection failed: {e.reason}")
        except Exception as e:
            logger.error(f"Supabase function request failed: {e}")
            raise SupabaseError(f"Request failed: {e}")
    
    # (TABLE OPERATIONS)
    
    def select(
        self,
        table: str,
        columns: str = "*",
        filters: Optional[Dict[str, Any]] = None,
        order: Optional[str] = None,
        limit: Optional[int] = None,
        single: bool = False
    ) -> List[Dict] | Dict | None:
        """
        Select rows from a table.
        
        Args:
            table: Table name.
            columns: Columns to select (default "*").
            filters: Filter conditions (column=value pairs).
            order: Order by clause (e.g., "created_at.desc").
            limit: Maximum rows to return.
            single: If True, return single row or None.
            
        Returns:
            List of rows, single row, or None.
        """
        params = {"select": columns}
        
        # Add filters as query params (PostgREST format)
        if filters:
            for col, value in filters.items():
                if isinstance(value, bool):
                    params[col] = f"eq.{str(value).lower()}"
                elif value is None:
                    params[col] = "is.null"
                else:
                    params[col] = f"eq.{value}"
        
        if order:
            params["order"] = order
        if limit:
            params["limit"] = str(limit)
        
        result = self._make_request("GET", table, params=params)
        
        if single:
            return result[0] if result else None
        return result or []
    
    def insert(self, table: str, data: Dict | List[Dict]) -> List[Dict]:
        """
        Insert row(s) into a table.
        
        Args:
            table: Table name.
            data: Row data or list of rows.
            
        Returns:
            Inserted row(s).
        """
        if isinstance(data, dict):
            data = [data]
        
        result = self._make_request("POST", table, data=data)
        return result or []
    
    def update(
        self,
        table: str,
        data: Dict,
        filters: Dict[str, Any]
    ) -> List[Dict]:
        """
        Update rows in a table.
        
        Args:
            table: Table name.
            data: Update data.
            filters: Filter conditions to identify rows.
            
        Returns:
            Updated row(s).
        """
        params = {}
        for col, value in filters.items():
            if isinstance(value, bool):
                params[col] = f"eq.{str(value).lower()}"
            else:
                params[col] = f"eq.{value}"
        
        result = self._make_request("PATCH", table, data=data, params=params)
        return result or []
    
    def delete(self, table: str, filters: Dict[str, Any]) -> List[Dict]:
        """
        Delete rows from a table.
        
        Args:
            table: Table name.
            filters: Filter conditions to identify rows.
            
        Returns:
            Deleted row(s).
        """
        params = {}
        for col, value in filters.items():
            params[col] = f"eq.{value}"
        
        result = self._make_request("DELETE", table, params=params)
        return result or []
    
    def rpc(self, function: str, params: Optional[Dict] = None) -> Any:
        """
        Call a Supabase RPC function.
        
        Args:
            function: Function name.
            params: Function parameters.
            
        Returns:
            Function result.
        """
        endpoint = f"rpc/{function}"
        return self._make_request("POST", endpoint, data=params or {})
    
    # (CONVENIENCE METHODS)
    
    def select_contains(
        self,
        table: str,
        column: str,
        values: List[str],
        other_filters: Optional[Dict[str, Any]] = None,
        order: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """
        Select rows where array column contains specified values.
        
        Used for querying notifications by target_tiers.
        
        Args:
            table: Table name.
            column: Array column name.
            values: Values that should be contained in the array.
            other_filters: Additional filter conditions.
            order: Order by clause (e.g., "created_at.desc").
            limit: Maximum rows to return.
            
        Returns:
            Matching rows.
        """
        params = {"select": "*"}
        
        # PostgREST array contains operator
        params[column] = f"cs.{{{','.join(values)}}}"
        
        if other_filters:
            for col, value in other_filters.items():
                params[col] = f"eq.{value}"
        
        if order:
            params["order"] = order
        if limit:
            params["limit"] = str(limit)
        
        return self._make_request("GET", table, params=params) or []
    
    def health_check(self) -> bool:
        """
        Check if Supabase connection is working.
        
        Returns:
            True if connected, False otherwise.
        """
        try:
            self.select("licenses", columns="id", limit=1)
            return True
        except Exception as e:
            logger.debug(f"Health check failed: {e}")
            return False


# (SINGLETON INSTANCE)

_client_instance: Optional[SupabaseClient] = None


def get_supabase_client() -> SupabaseClient:
    """
    Get the singleton Supabase client instance.
    
    Returns:
        SupabaseClient instance.
    """
    global _client_instance
    if _client_instance is None:
        _client_instance = SupabaseClient()
    return _client_instance


def configure_supabase(url: str, anon_key: str) -> None:
    """
    Configure Supabase credentials at runtime.
    
    Args:
        url: Supabase project URL.
        anon_key: Supabase anon key.
    """
    global _client_instance
    _client_instance = SupabaseClient(url=url, anon_key=anon_key)
    logger.info("Supabase client configured")


# (MODULE TEST)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logger.info("Supabase Client Test")
    logger.info("=" * 50)
    
    client = get_supabase_client()
    
    if client.is_configured:
        logger.info("URL: %s", client.url)
        logger.info("Configured: ✓")
        
        logger.info("\nTesting health check...")
        if client.health_check():
            logger.info("Health check: ✓ Connected")
        else:
            logger.info("Health check: ✗ Failed")
    else:
        logger.info("Supabase not configured.")
        logger.info("Set SUPABASE_URL and SUPABASE_ANON_KEY environment variables.")
