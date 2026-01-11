"""
MODFLOW Groundwater Model Importer
Parses MODFLOW .lst output files and imports groundwater inflow data to the database.
"""

import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import re
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from database.db_manager import db
from utils.app_logger import logger


class MODFLOWImporter:
    """Import groundwater inflow data from MODFLOW .lst files."""
    
    def __init__(self):
        """Initialize the importer."""
        pass
    
    def parse_lst_file(self, file_path: str) -> List[Dict]:
        """
        Parse a MODFLOW .lst file and extract groundwater inflow data.
        
        Args:
            file_path: Path to the .lst file
            
        Returns:
            List of dictionaries containing inflow data:
            [{
                'well_id': str,
                'date': datetime,
                'inflow_m3': float,
                'confidence_level': str
            }, ...]
        """
        results = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            logger.info(f"Parsing MODFLOW file: {file_path}")
            
            # Extract scenario name from file header or path
            scenario_name = self._extract_scenario_name(file_path, content)
            
            # Parse inflow data
            # MODFLOW .lst files typically have sections like:
            # WELL NO.    LAYER   ROW   COL   STRESS RATE
            # Format may vary, this is a generic pattern
            
            # Look for well data patterns
            well_pattern = r'WELL\s+(\w+).*?RATE\s*[=:]?\s*([\d.eE+-]+)'
            matches = re.finditer(well_pattern, content, re.IGNORECASE | re.MULTILINE)
            
            for match in matches:
                well_id = match.group(1)
                rate = float(match.group(2))
                
                # Convert rate to m³ (assuming rate is in m³/day)
                # Multiply by 30 to get monthly volume
                inflow_m3 = abs(rate) * 30.0  # Take absolute value for inflows
                
                # Parse date from filename or content
                date_obj = self._extract_date(file_path, content)
                
                # Determine confidence level based on model convergence
                confidence = self._determine_confidence(content)
                
                results.append({
                    'well_id': well_id,
                    'date': date_obj,
                    'inflow_m3': inflow_m3,
                    'scenario_name': scenario_name,
                    'confidence_level': confidence
                })
            
            logger.info(f"Parsed {len(results)} well records from {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to parse MODFLOW file {file_path}: {e}", exc_info=True)
            raise
        
        return results
    
    def _extract_scenario_name(self, file_path: str, content: str) -> str:
        """Extract scenario name from file path or content."""
        # Try to extract from filename (e.g., scenario_2024_01.lst -> scenario_2024_01)
        filename = Path(file_path).stem
        
        # Look for scenario in content
        scenario_match = re.search(r'SCENARIO[:\s]+([^\n]+)', content, re.IGNORECASE)
        if scenario_match:
            return scenario_match.group(1).strip()
        
        return filename
    
    def _extract_date(self, file_path: str, content: str) -> datetime:
        """Extract date from filename or content."""
        # Try to extract date from filename (e.g., results_2024_01.lst)
        date_match = re.search(r'(\d{4})[_-](\d{2})', str(file_path))
        if date_match:
            year = int(date_match.group(1))
            month = int(date_match.group(2))
            return datetime(year, month, 1)
        
        # Try to extract from content
        content_date_match = re.search(r'DATE[:\s]+(\d{4})[/-](\d{2})', content, re.IGNORECASE)
        if content_date_match:
            year = int(content_date_match.group(1))
            month = int(content_date_match.group(2))
            return datetime(year, month, 1)
        
        # Default to current month
        logger.warning(f"Could not extract date from {file_path}, using current month")
        return datetime.now().replace(day=1)
    
    def _determine_confidence(self, content: str) -> str:
        """Determine confidence level based on model convergence."""
        # Look for convergence indicators
        if 'NORMAL TERMINATION' in content or 'CONVERGED' in content:
            return 'high'
        elif 'WARNING' in content:
            return 'medium'
        else:
            return 'low'
    
    def map_well_to_source(self, well_id: str) -> Optional[int]:
        """
        Map a MODFLOW well ID to a water source ID in the database.
        
        Args:
            well_id: MODFLOW well identifier
            
        Returns:
            Source ID from water_sources table, or None if not found
        """
        # Query water sources for matching well
        # This assumes source_code in water_sources matches well_id
        sources = db.execute_query(
            "SELECT source_id FROM water_sources WHERE source_code = ? OR source_name LIKE ?",
            (well_id, f'%{well_id}%')
        )
        
        if sources and len(sources) > 0:
            return sources[0]['source_id']
        
        # If not found, log warning and create new source
        logger.warning(f"Well {well_id} not found in water_sources, creating new entry")
        
        try:
            db.execute_update(
                """
                INSERT INTO water_sources (source_code, source_name, type_id, area_id)
                VALUES (?, ?, ?, ?)
                """,
                (well_id, f'MODFLOW Well {well_id}', 1, 1)  # Default to type 1, area 1
            )
            
            # Retrieve the newly created source_id
            sources = db.execute_query(
                "SELECT source_id FROM water_sources WHERE source_code = ?",
                (well_id,)
            )
            
            if sources:
                return sources[0]['source_id']
        
        except Exception as e:
            logger.error(f"Failed to create water source for well {well_id}: {e}")
        
        return None
    
    def import_to_database(self, inflow_data: List[Dict]) -> Tuple[int, int]:
        """
        Import MODFLOW inflow data to the groundwater_inflow_monthly table.
        
        Args:
            inflow_data: List of inflow records from parse_lst_file()
            
        Returns:
            Tuple of (successful_imports, failed_imports)
        """
        successful = 0
        failed = 0
        
        for record in inflow_data:
            try:
                # Map well to source
                source_id = self.map_well_to_source(record['well_id'])
                
                if source_id is None:
                    logger.error(f"Could not map well {record['well_id']} to source")
                    failed += 1
                    continue
                
                # Extract month and year from date
                month = record['date'].month
                year = record['date'].year
                
                # Insert or update groundwater inflow
                db.execute_update(
                    """
                    INSERT OR REPLACE INTO groundwater_inflow_monthly 
                    (source_id, month, year, inflow_m3, modflow_scenario_name, confidence_level, model_run_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (source_id, month, year, record['inflow_m3'], 
                     record['scenario_name'], record['confidence_level'], 
                     datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                )
                
                successful += 1
                logger.debug(f"Imported: Well {record['well_id']} -> Source {source_id}, {record['inflow_m3']:.2f} m³")
                
            except Exception as e:
                logger.error(f"Failed to import record {record}: {e}")
                failed += 1
        
        logger.info(f"MODFLOW import complete: {successful} successful, {failed} failed")
        return successful, failed
    
    def import_file(self, file_path: str) -> Tuple[int, int]:
        """
        Parse and import a MODFLOW .lst file in one step.
        
        Args:
            file_path: Path to the .lst file
            
        Returns:
            Tuple of (successful_imports, failed_imports)
        """
        inflow_data = self.parse_lst_file(file_path)
        return self.import_to_database(inflow_data)
    
    def import_directory(self, directory_path: str, pattern: str = '*.lst') -> Dict:
        """
        Import all MODFLOW .lst files from a directory.
        
        Args:
            directory_path: Path to directory containing .lst files
            pattern: File pattern to match (default: '*.lst')
            
        Returns:
            Dictionary with import statistics:
            {
                'files_processed': int,
                'total_successful': int,
                'total_failed': int,
                'files': [{
                    'filename': str,
                    'successful': int,
                    'failed': int
                }, ...]
            }
        """
        directory = Path(directory_path)
        lst_files = list(directory.glob(pattern))
        
        stats = {
            'files_processed': 0,
            'total_successful': 0,
            'total_failed': 0,
            'files': []
        }
        
        logger.info(f"Importing MODFLOW files from {directory_path} (pattern: {pattern})")
        
        for file_path in lst_files:
            try:
                logger.info(f"Processing file: {file_path.name}")
                successful, failed = self.import_file(str(file_path))
                
                stats['files_processed'] += 1
                stats['total_successful'] += successful
                stats['total_failed'] += failed
                stats['files'].append({
                    'filename': file_path.name,
                    'successful': successful,
                    'failed': failed
                })
                
            except Exception as e:
                logger.error(f"Failed to process file {file_path.name}: {e}")
                stats['files'].append({
                    'filename': file_path.name,
                    'successful': 0,
                    'failed': 0,
                    'error': str(e)
                })
        
        logger.info(f"Directory import complete: {stats['files_processed']} files, "
                   f"{stats['total_successful']} successful, {stats['total_failed']} failed")
        
        return stats


# Singleton instance
_modflow_importer = None

def get_modflow_importer() -> MODFLOWImporter:
    """Get singleton instance of MODFLOW importer."""
    global _modflow_importer
    if _modflow_importer is None:
        _modflow_importer = MODFLOWImporter()
    return _modflow_importer


def reset_modflow_importer():
    """Reset singleton instance (useful for testing)."""
    global _modflow_importer
    _modflow_importer = None


if __name__ == '__main__':
    """Command-line interface for importing MODFLOW files."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Import MODFLOW groundwater data')
    parser.add_argument('path', help='Path to .lst file or directory')
    parser.add_argument('--pattern', default='*.lst', help='File pattern for directory import')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel('DEBUG')
    
    importer = get_modflow_importer()
    path = Path(args.path)
    
    if path.is_file():
        print(f"Importing file: {path}")
        successful, failed = importer.import_file(str(path))
        print(f"Import complete: {successful} successful, {failed} failed")
    
    elif path.is_dir():
        print(f"Importing directory: {path} (pattern: {args.pattern})")
        stats = importer.import_directory(str(path), args.pattern)
        print(f"\nImport Summary:")
        print(f"  Files processed: {stats['files_processed']}")
        print(f"  Total successful: {stats['total_successful']}")
        print(f"  Total failed: {stats['total_failed']}")
        print(f"\nPer-file results:")
        for file_stat in stats['files']:
            status = f"{file_stat['successful']} ok, {file_stat['failed']} failed"
            if 'error' in file_stat:
                status += f" (ERROR: {file_stat['error']})"
            print(f"  {file_stat['filename']}: {status}")
    
    else:
        print(f"Error: {path} is not a valid file or directory")
        sys.exit(1)
