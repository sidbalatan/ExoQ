"""
Integrity Tracker Module

Tracks which coordinates have passed which modules to ensure
pipeline integrity and prevent skipping prerequisite modules.
"""

import pandas as pd
from typing import Dict, Any, List
from datetime import datetime


class IntegrityTracker:
    """
    Tracks module completion status for coordinates.
    
    Ensures that coordinates cannot skip prerequisite modules,
    maintaining the integrity of the ExoQ pipeline and certificates.
    """
    
    def __init__(self):
        """Initialize the Integrity Tracker."""
        self.status_columns = {
            1: 'module1_passed',
            2: 'module2_passed',
            3: 'module3_passed',
            4: 'module4_passed',
            4.5: 'module4_5_passed',
            5: 'module5_passed',
            6: 'module6_passed',
            7: 'module7_passed'
        }
        self.timestamp_columns = {
            1: 'module1_timestamp',
            2: 'module2_timestamp',
            3: 'module3_timestamp',
            4: 'module4_timestamp',
            4.5: 'module4_5_timestamp',
            5: 'module5_timestamp',
            6: 'module6_timestamp',
            7: 'module7_timestamp'
        }
    
    def initialize_integrity_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Initialize integrity tracking columns for a new dataset.
        
        Parameters
        ----------
        df : pd.DataFrame
            Input dataframe
            
        Returns
        -------
        pd.DataFrame
            Dataframe with integrity columns added
        """
        df = df.copy()
        
        # Add status columns
        for module_id, col in self.status_columns.items():
            df[col] = False
        
        # Add timestamp columns
        for module_id, col in self.timestamp_columns.items():
            df[col] = None
        
        return df
    
    def mark_module_complete(self, df: pd.DataFrame, module_id: int) -> pd.DataFrame:
        """
        Mark coordinates as having completed a specific module.
        
        Parameters
        ----------
        df : pd.DataFrame
            Dataframe to update
        module_id : int
            Module ID (1-7)
            
        Returns
        -------
        pd.DataFrame
            Updated dataframe with module marked as complete
        """
        df = df.copy()
        
        if module_id not in self.status_columns:
            raise ValueError(f"Invalid module_id: {module_id}")
        
        status_col = self.status_columns[module_id]
        timestamp_col = self.timestamp_columns[module_id]
        
        df[status_col] = True
        df[timestamp_col] = datetime.now().isoformat()
        
        return df
    
    def check_prerequisite(self, df: pd.DataFrame, required_module: int) -> tuple:
        """
        Check if all coordinates have completed the required prerequisite module.
        
        Parameters
        ----------
        df : pd.DataFrame
            Dataframe to check
        required_module : int
            Required module ID
            
        Returns
        -------
        tuple
            (passed: bool, failed_count: int, failed_source_ids: list)
        """
        if required_module not in self.status_columns:
            raise ValueError(f"Invalid required_module: {required_module}")
        
        status_col = self.status_columns[required_module]
        
        # Check if column exists
        if status_col not in df.columns:
            return False, len(df), df.get('source_id', []).tolist()
        
        # Find coordinates that haven't passed
        failed = df[df[status_col] != True]
        failed_count = len(failed)
        
        if failed_count == 0:
            return True, 0, []
        else:
            failed_ids = failed.get('source_id', []).tolist()
            return False, failed_count, failed_ids
    
    def get_module_status(self, module_id: int, workspace_data: Dict[str, Any]) -> str:
        """
        Get the completion status of a module for the current user.
        
        Parameters
        ----------
        module_id : int
            Module ID to check
        workspace_data : dict
            User's workspace data
            
        Returns
        -------
        str
            Status: 'locked', 'ready', 'in_progress', 'complete'
        """
        if module_id == 1:
            # Module 1 is always ready
            return 'ready'
        
        # Check if prerequisite module is complete
        prerequisite = module_id - 1
        prereq_status = self.get_module_status(prerequisite, workspace_data)
        
        if prereq_status != 'complete':
            return 'locked'
        
        # Check if this module is complete
        if workspace_data and 'module_status' in workspace_data:
            module_status = workspace_data['module_status'].get(str(module_id))
            if module_status == 'complete':
                return 'complete'
            elif module_status == 'in_progress':
                return 'in_progress'
        
        return 'ready'
    
    def validate_input_for_module(self, df: pd.DataFrame, target_module: int) -> tuple:
        """
        Validate that a dataset can be used for a specific module.
        
        Parameters
        ----------
        df : pd.DataFrame
            Input dataframe
        target_module : int
            Target module ID
            
        Returns
        -------
        tuple
            (valid: bool, error_message: str)
        """
        if target_module == 1:
            # Module 1 accepts any input
            return True, ""
        
        # Check prerequisite
        required_module = target_module - 1
        passed, failed_count, failed_ids = self.check_prerequisite(df, required_module)
        
        if not passed:
            error_msg = (
                f"⚠️ **Integrity Check Failed**\n\n"
                f"{failed_count} coordinates have not passed Module {required_module}. "
                f"Please run Module {required_module} first to maintain pipeline integrity.\n\n"
                f"Affected coordinates: {', '.join(map(str, failed_ids[:5]))}"
                f"{'...' if len(failed_ids) > 5 else ''}"
            )
            return False, error_msg
        
        return True, ""


def get_module_status(module_id: int, workspace_data: Dict[str, Any]) -> str:
    """
    Convenience function to get module status.
    
    Parameters
    ----------
    module_id : int
        Module ID to check
    workspace_data : dict
        User's workspace data
        
    Returns
    -------
    str
        Status: 'locked', 'ready', 'in_progress', 'complete'
    """
    tracker = IntegrityTracker()
    return tracker.get_module_status(module_id, workspace_data)


def check_integrity(df: pd.DataFrame, required_module: int) -> tuple:
    """
    Convenience function to check prerequisite completion.
    
    Parameters
    ----------
    df : pd.DataFrame
        Dataframe to check
    required_module : int
        Required module ID
        
    Returns
    -------
    tuple
        (passed: bool, failed_count: int, failed_source_ids: list)
    """
    tracker = IntegrityTracker()
    return tracker.check_prerequisite(df, required_module)
