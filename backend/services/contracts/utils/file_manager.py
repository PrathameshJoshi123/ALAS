"""
File Manager for Contract Service
Handles storage and retrieval of contract PDF files on disk
"""

import os
import logging
from typing import Optional, Tuple
from pathlib import Path
from uuid import UUID
import shutil

logger = logging.getLogger(__name__)


class ContractFileManager:
    """Manages contract file storage on disk in backend/files/ directory"""
    
    def __init__(self, base_path: str = None):
        """
        Initialize file manager
        
        Args:
            base_path: Base directory for contract storage (default: backend/files/)
        """
        if base_path is None:
            # Use files directory in backend
            base_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "files"
            )
        
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Initialized contract file manager with base path: {self.base_path}")
    
    def get_contract_directory(self, tenant_id: UUID, contract_id: UUID) -> Path:
        """
        Get or create contract-specific directory
        
        Args:
            tenant_id: Tenant UUID
            contract_id: Contract UUID
        
        Returns:
            Path object for the contract directory
        """
        contract_dir = self.base_path / str(tenant_id) / str(contract_id)
        contract_dir.mkdir(parents=True, exist_ok=True)
        return contract_dir
    
    def save_contract_file(
        self,
        tenant_id: UUID,
        contract_id: UUID,
        file_content: bytes,
        original_filename: str
    ) -> str:
        """
        Save uploaded contract PDF to disk
        
        Args:
            tenant_id: Tenant UUID
            contract_id: Contract UUID
            file_content: File bytes
            original_filename: Original filename from upload
        
        Returns:
            str: Relative path to saved file
        """
        try:
            contract_dir = self.get_contract_directory(tenant_id, contract_id)
            
            # Preserve original filename for reference
            file_path = contract_dir / original_filename
            
            # If file exists, append timestamp to avoid conflicts
            if file_path.exists():
                name, ext = os.path.splitext(original_filename)
                from datetime import datetime
                timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                file_path = contract_dir / f"{name}_{timestamp}{ext}"
            
            # Write file
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            # Return relative path from base
            relative_path = str(file_path.relative_to(self.base_path))
            
            logger.info(f"Saved contract file: {relative_path}")
            return relative_path
            
        except Exception as e:
            logger.error(f"Failed to save contract file: {str(e)}")
            raise
    
    def get_contract_file_path(self, relative_path: str) -> Path:
        """
        Get full path for a stored contract file
        
        Args:
            relative_path: Relative path (as returned by save_contract_file)
        
        Returns:
            Path: Full path to the file
        """
        full_path = self.base_path / relative_path
        
        if not full_path.exists():
            raise FileNotFoundError(f"Contract file not found: {relative_path}")
        
        return full_path
    
    def file_exists(self, relative_path: str) -> bool:
        """
        Check if a contract file exists
        
        Args:
            relative_path: Relative path to file
        
        Returns:
            bool: True if file exists
        """
        full_path = self.base_path / relative_path
        return full_path.exists()
    
    def read_contract_file(self, relative_path: str) -> bytes:
        """
        Read contract file content
        
        Args:
            relative_path: Relative path to file
        
        Returns:
            bytes: File content
        """
        try:
            full_path = self.get_contract_file_path(relative_path)
            
            with open(full_path, 'rb') as f:
                content = f.read()
            
            logger.info(f"Read contract file: {relative_path}")
            return content
            
        except Exception as e:
            logger.error(f"Failed to read contract file: {str(e)}")
            raise
    
    def delete_contract_files(self, tenant_id: UUID, contract_id: UUID) -> None:
        """
        Delete all files for a contract (when contract is deleted)
        
        Args:
            tenant_id: Tenant UUID
            contract_id: Contract UUID
        """
        try:
            contract_dir = self.base_path / str(tenant_id) / str(contract_id)
            
            if contract_dir.exists():
                shutil.rmtree(contract_dir)
                logger.info(f"Deleted contract files for {tenant_id}/{contract_id}")
            
        except Exception as e:
            logger.error(f"Failed to delete contract files: {str(e)}")
            raise
    
    def get_file_size(self, relative_path: str) -> int:
        """
        Get file size in bytes
        
        Args:
            relative_path: Relative path to file
        
        Returns:
            int: File size in bytes
        """
        try:
            full_path = self.get_contract_file_path(relative_path)
            return full_path.stat().st_size
            
        except Exception as e:
            logger.error(f"Failed to get file size: {str(e)}")
            raise


def get_file_manager(base_path: str = None) -> ContractFileManager:
    """
    Get or create file manager instance (singleton)
    
    Args:
        base_path: Optional base directory path
    
    Returns:
        ContractFileManager: Initialized manager
    """
    if not hasattr(get_file_manager, "_instance"):
        get_file_manager._instance = ContractFileManager(base_path)
    
    return get_file_manager._instance
