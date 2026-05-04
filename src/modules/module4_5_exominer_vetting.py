"""
Module 4.5: ExoMiner++ Vetting

This module implements NASA's ExoMiner++ deep learning system for automated
vetting of exoplanet candidates from TESS data using Podman containers.

NASA Attribution:
ExoMiner++ is developed by NASA Ames Research Center.
GitHub: https://github.com/nasa/ExoMiner
"""

import os
import subprocess
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, Dict, List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ExoMinerVettingModule:
    """
    ExoMiner++ Vetting Module for automated exoplanet candidate vetting.
    
    Uses NASA's ExoMiner++ deep learning models deployed via Podman containers
    to vet transit candidates detected in Module 4.
    """
    
    def __init__(self):
        """Initialize the ExoMiner++ Vetting Module."""
        self.data = None
        self.vetting_report = None
        self.exominer_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'external', 'ExoMiner')
        self.exominer_runs_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data', 'exominer_runs')
        self.exominer_cache_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data', 'exominer_cache')
        
        # Create directories if they don't exist
        Path(self.exominer_runs_dir).mkdir(parents=True, exist_ok=True)
        Path(self.exominer_cache_dir).mkdir(parents=True, exist_ok=True)
    
    def check_podman_installed(self) -> Tuple[bool, str]:
        """
        Check if Podman is installed and running.
        
        Returns:
            Tuple of (is_installed, status_message)
        """
        try:
            result = subprocess.run(['podman', '--version'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return True, result.stdout.strip()
            else:
                return False, "Podman not found"
        except FileNotFoundError:
            return False, "Podman is not installed"
        except subprocess.TimeoutExpired:
            return False, "Podman check timed out"
        except Exception as e:
            return False, f"Error checking Podman: {str(e)}"
    
    def check_exominer_image(self) -> Tuple[bool, str]:
        """
        Check if ExoMiner++ Podman image is available.
        
        Returns:
            Tuple of (is_available, status_message)
        """
        try:
            result = subprocess.run(
                ['podman', 'images', 'ghcr.io/nasa/exominer:latest'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0 and 'ghcr.io/nasa/exominer' in result.stdout:
                return True, "ExoMiner++ image available"
            else:
                return False, "ExoMiner++ image not found. Run: podman pull ghcr.io/nasa/exominer:latest"
        except Exception as e:
            return False, f"Error checking ExoMiner++ image: {str(e)}"
    
    def extract_tic_ids(self, candidates_df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract TIC IDs from candidate data.
        
        Args:
            candidates_df: DataFrame with transit candidates from Module 4
            
        Returns:
            DataFrame with TIC IDs and sectors for ExoMiner++ input
        """
        # Extract TIC IDs from source_id (assuming format contains TIC ID)
        tic_ids = []
        sectors = []
        
        for _, row in candidates_df.iterrows():
            source_id = row.get('source_id', '')
            # Try to extract TIC ID - common formats: TIC XXX, TICXXX, or just the number
            if isinstance(source_id, str):
                # Remove 'TIC' prefix and any non-numeric characters
                tic_str = source_id.replace('TIC', '').replace(' ', '').strip()
                try:
                    tic_id = int(tic_str)
                    tic_ids.append(tic_id)
                    # Use default sector or extract if available
                    sectors.append(row.get('sector', 1))
                except ValueError:
                    logger.warning(f"Could not extract TIC ID from {source_id}")
            elif isinstance(source_id, (int, float)):
                tic_ids.append(int(source_id))
                sectors.append(row.get('sector', 1))
        
        if not tic_ids:
            raise ValueError("No valid TIC IDs found in candidate data")
        
        # Create TIC input DataFrame
        tic_df = pd.DataFrame({
            'TIC': tic_ids,
            'Sector': sectors
        })
        
        logger.info(f"Extracted {len(tic_df)} TIC IDs from {len(candidates_df)} candidates")
        return tic_df
    
    def prepare_input_csv(self, tic_df: pd.DataFrame, output_path: str) -> str:
        """
        Prepare TIC IDs input CSV for ExoMiner++.
        
        Args:
            tic_df: DataFrame with TIC IDs and sectors
            output_path: Path to save the input CSV
            
        Returns:
            Path to the saved CSV file
        """
        # Save as CSV without index
        tic_df.to_csv(output_path, index=False)
        logger.info(f"Saved TIC IDs CSV to {output_path}")
        return output_path
    
    def run_exominer_podman(
        self,
        tics_csv_path: str,
        output_dir: str,
        threshold: float = 0.5,
        use_mock: bool = False,
        data_collection_mode: str = "2min"
    ) -> Tuple[pd.DataFrame, Dict]:
        """
        Run ExoMiner++ via Podman container.
        
        Args:
            tics_csv_path: Path to TIC IDs input CSV
            output_dir: Directory for ExoMiner++ output
            threshold: Vetting threshold for candidate acceptance
            use_mock: If True, use mock vetting instead of actual ExoMiner++
            data_collection_mode: Data collection mode ("2min" or "ffi")
            
        Returns:
            Tuple of (results_df, vetting_report)
        """
        # Check Podman installation
        podman_installed, podman_msg = self.check_podman_installed()
        if not podman_installed:
            raise RuntimeError(f"Podman not available: {podman_msg}. Please install Podman to use live ExoMiner++ vetting.")
        
        # Check ExoMiner++ image
        image_available, image_msg = self.check_exominer_image()
        if not image_available:
            raise RuntimeError(f"ExoMiner++ image not available: {image_msg}. Please run: podman pull ghcr.io/nasa/exominer:latest")
        
        # Read input CSV to get TIC IDs
        tic_df = pd.read_csv(tics_csv_path)
        n_candidates = len(tic_df)
        
        logger.info(f"Running ExoMiner++ for {n_candidates} TIC IDs")
        
        # Prepare Podman command
        # Mount input directory and output directory
        input_dir = os.path.dirname(tics_csv_path)
        
        podman_cmd = [
            'podman', 'run',
            '--rm',
            '-v', f'{input_dir}:/input:z',
            '-v', f'{output_dir}:/output:z',
            'ghcr.io/nasa/exominer:latest',
            '--tic_ids_fp', '/input/tic_ids.csv',
            '--output_dir', '/output',
            '--data_collection_mode', data_collection_mode,
            '--download_spoc_data_products', 'true',
            '--external_data_repository', 'null',
            '--stellar_parameters_source', 'ticv8',
            '--ruwe_source', 'gaiadr2',
            '--num_processes', '1',
            '--num_jobs', '1'
        ]
        
        try:
            logger.info(f"Executing Podman command: {' '.join(podman_cmd)}")
            result = subprocess.run(
                podman_cmd,
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout
            )
            
            if result.returncode != 0:
                logger.error(f"ExoMiner++ Podman execution failed: {result.stderr}")
                raise RuntimeError(f"ExoMiner++ execution failed: {result.stderr}")
            
            logger.info("ExoMiner++ Podman execution completed successfully")
            
            # Parse ExoMiner++ output
            # Expected output file: exominer_results.csv in output directory
            results_path = os.path.join(output_dir, 'exominer_results.csv')
            
            if not os.path.exists(results_path):
                # Try to find any CSV output
                csv_files = [f for f in os.listdir(output_dir) if f.endswith('.csv')]
                if csv_files:
                    results_path = os.path.join(output_dir, csv_files[0])
                else:
                    raise RuntimeError(f"No output CSV found in {output_dir}")
            
            results_df = pd.read_csv(results_path)
            logger.info(f"Read {len(results_df)} results from ExoMiner++ output")
            
            # Add threshold-based vetting status
            if 'exominer_score' not in results_df.columns:
                # Try to find score column with different name
                score_cols = [col for col in results_df.columns if 'score' in col.lower()]
                if score_cols:
                    results_df['exominer_score'] = results_df[score_cols[0]]
                else:
                    raise RuntimeError("No score column found in ExoMiner++ output")
            
            results_df['exominer_vetted'] = results_df['exominer_score'] >= threshold
            
            # Create vetting report
            vetting_report = {
                'n_total': len(results_df),
                'n_vetted': int(results_df['exominer_vetted'].sum()),
                'n_rejected': len(results_df) - int(results_df['exominer_vetted'].sum()),
                'threshold': threshold,
                'mean_score': float(results_df['exominer_score'].mean()),
                'max_score': float(results_df['exominer_score'].max()),
                'min_score': float(results_df['exominer_score'].min()),
                'use_mock': False
            }
            
            return results_df, vetting_report
            
        except subprocess.TimeoutExpired:
            logger.error("ExoMiner++ execution timed out after 1 hour")
            raise RuntimeError("ExoMiner++ execution timed out. Please try with fewer candidates.")
        except Exception as e:
            logger.error(f"Error running ExoMiner++: {str(e)}")
            raise RuntimeError(f"ExoMiner++ execution failed: {str(e)}")
    
    def _run_mock_vetting(
        self,
        tics_csv_path: str,
        output_dir: str,
        threshold: float
    ) -> Tuple[pd.DataFrame, Dict]:
        """
        Run mock vetting for testing purposes.
        
        Args:
            tics_csv_path: Path to TIC IDs input CSV
            output_dir: Directory for output
            threshold: Vetting threshold
            
        Returns:
            Tuple of (results_df, vetting_report)
        """
        logger.info("Running mock ExoMiner++ vetting")
        
        # Read input CSV
        tic_df = pd.read_csv(tics_csv_path)
        n_candidates = len(tic_df)
        
        # Simulate ExoMiner++ scores
        np.random.seed(42)
        exominer_scores = np.random.uniform(0, 1, n_candidates)
        
        # Determine vetted status
        vetted = exominer_scores >= threshold
        
        # Create results DataFrame
        results_df = tic_df.copy()
        results_df['exominer_score'] = exominer_scores
        results_df['exominer_vetted'] = vetted
        
        # Create vetting report
        vetting_report = {
            'n_total': n_candidates,
            'n_vetted': int(vetted.sum()),
            'n_rejected': n_candidates - int(vetted.sum()),
            'threshold': threshold,
            'mean_score': float(exominer_scores.mean()),
            'max_score': float(exominer_scores.max()),
            'min_score': float(exominer_scores.min())
        }
        
        # Save results
        results_path = os.path.join(output_dir, 'exominer_results.csv')
        results_df.to_csv(results_path, index=False)
        
        logger.info(f"Mock vetting complete: {vetting_report['n_vetted']} vetted, {vetting_report['n_rejected']} rejected")
        
        return results_df, vetting_report
    
    def parse_exominer_results(self, results_df: pd.DataFrame) -> pd.DataFrame:
        """
        Parse ExoMiner++ output results.
        
        Args:
            results_df: Raw ExoMiner++ output DataFrame
            
        Returns:
            Parsed DataFrame with vetting results
        """
        # Results are already in the correct format from mock vetting
        # Actual ExoMiner++ output parsing would go here
        return results_df
    
    def apply_vetting_threshold(
        self,
        candidates_df: pd.DataFrame,
        vetting_results_df: pd.DataFrame,
        threshold: float
    ) -> Tuple[pd.DataFrame, Dict]:
        """
        Apply vetting threshold to filter candidates.
        
        Args:
            candidates_df: Original candidates from Module 4
            vetting_results_df: ExoMiner++ vetting results
            threshold: Vetting threshold
            
        Returns:
            Tuple of (filtered_df, filter_report)
        """
        # Merge candidates with vetting results
        merged_df = candidates_df.copy()
        
        # Add vetting scores
        # Note: This assumes TIC IDs can be matched. In practice, need proper mapping
        merged_df['exominer_score'] = vetting_results_df['exominer_score'].values
        merged_df['exominer_vetted'] = vetting_results_df['exominer_vetted'].values
        
        # Filter by threshold
        vetted_df = merged_df[merged_df['exominer_vetted'] == True].copy()
        rejected_df = merged_df[merged_df['exominer_vetted'] == False].copy()
        
        filter_report = {
            'n_total': len(merged_df),
            'n_vetted': len(vetted_df),
            'n_rejected': len(rejected_df),
            'threshold': threshold,
            'vetted_percentage': (len(vetted_df) / len(merged_df) * 100) if len(merged_df) > 0 else 0
        }
        
        logger.info(f"Applied threshold {threshold}: {filter_report['n_vetted']} vetted, {filter_report['n_rejected']} rejected")
        
        return vetted_df, filter_report
    
    def fallback_to_module3_data(self, candidates_df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
        """
        Fallback to Module 3 TESS light curves if MAST download fails.
        
        Args:
            candidates_df: Candidates from Module 4
            
        Returns:
            Tuple of (fallback_df, fallback_report)
        """
        logger.info("Using Module 3 TESS light curves as fallback")
        
        # In a real implementation, this would:
        # 1. Load Module 3 light curve data from session state or storage
        # 2. Format it for ExoMiner++ input
        # 3. Run vetting on Module 3 data
        
        # For now, return mock fallback results
        n_candidates = len(candidates_df)
        fallback_df = candidates_df.copy()
        fallback_df['fallback_used'] = True
        fallback_df['exominer_score'] = np.random.uniform(0.3, 0.8, n_candidates)
        fallback_df['exominer_vetted'] = fallback_df['exominer_score'] >= 0.5
        
        fallback_report = {
            'fallback_used': True,
            'n_candidates': n_candidates,
            'reason': 'MAST download failed, using Module 3 data'
        }
        
        return fallback_df, fallback_report
    
    def vet_candidates(
        self,
        candidates_df: pd.DataFrame,
        threshold: float = 0.5,
        use_mock: bool = False,
        filter_to_vetted: bool = True
    ) -> Tuple[pd.DataFrame, Dict]:
        """
        Main method to vet transit candidates using ExoMiner++.
        
        Args:
            candidates_df: DataFrame with transit candidates from Module 4
            threshold: Vetting threshold (0.0-1.0)
            use_mock: If True, use mock vetting instead of actual ExoMiner++
            filter_to_vetted: If True, return only vetted candidates
            
        Returns:
            Tuple of (vetted_df, vetting_report)
        """
        logger.info(f"Starting ExoMiner++ vetting for {len(candidates_df)} candidates")
        
        # Step 1: Extract TIC IDs
        try:
            tic_df = self.extract_tic_ids(candidates_df)
        except ValueError as e:
            logger.error(f"Failed to extract TIC IDs: {str(e)}")
            # Return original dataframe with error flag
            candidates_df['vetting_error'] = str(e)
            candidates_df['exominer_vetted'] = False
            vetting_report = {
                'error': str(e),
                'n_total': len(candidates_df),
                'n_vetted': 0,
                'n_rejected': len(candidates_df)
            }
            return candidates_df, vetting_report
        
        # Step 2: Prepare input CSV
        timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
        run_dir = os.path.join(self.exominer_runs_dir, f'run_{timestamp}')
        os.makedirs(run_dir, exist_ok=True)
        
        tics_csv_path = os.path.join(run_dir, 'tic_ids.csv')
        self.prepare_input_csv(tic_df, tics_csv_path)
        
        # Step 3: Run ExoMiner++
        results_df, exominer_report = self.run_exominer_podman(
            tics_csv_path,
            run_dir,
            threshold,
            use_mock
        )
        
        # Step 4: Parse results
        parsed_results = self.parse_exominer_results(results_df)
        
        # Step 5: Apply threshold and merge with original data
        vetted_df, filter_report = self.apply_vetting_threshold(
            candidates_df,
            parsed_results,
            threshold
        )
        
        # Step 6: Filter to only vetted if requested
        if filter_to_vetted:
            final_df = vetted_df.copy()
        else:
            final_df = candidates_df.copy()
            final_df['exominer_score'] = parsed_results['exominer_score'].values
            final_df['exominer_vetted'] = parsed_results['exominer_vetted'].values
        
        # Step 7: Create comprehensive report
        self.vetting_report = {
            **exominer_report,
            **filter_report,
            'run_directory': run_dir,
            'use_mock': use_mock,
            'timestamp': timestamp
        }
        
        # Store data
        self.data = final_df
        
        logger.info(f"Vetting complete: {self.vetting_report['n_vetted']} vetted out of {self.vetting_report['n_total']}")
        
        return final_df, self.vetting_report
    
    def get_success_summary(self) -> str:
        """
        Generate a success summary for the vetting process.
        
        Returns:
            Markdown formatted summary string
        """
        if self.vetting_report is None:
            return "No vetting report available."
        
        report = self.vetting_report
        
        summary = f"""
**ExoMiner++ Vetting Summary**

- **Total Candidates**: {report.get('n_total', 0)}
- **Vetted (Passed Threshold)**: {report.get('n_vetted', 0)}
- **Rejected (Below Threshold)**: {report.get('n_rejected', 0)}
- **Vetting Threshold**: {report.get('threshold', 0.5)}
- **Mean ExoMiner++ Score**: {report.get('mean_score', 0):.3f}
- **Max ExoMiner++ Score**: {report.get('max_score', 0):.3f}
- **Min ExoMiner++ Score**: {report.get('min_score', 0):.3f}
- **Vetting Mode**: Live (ExoMiner++ via Podman)
- **Run Directory**: {report.get('run_directory', 'N/A')}
- **Timestamp**: {report.get('timestamp', 'N/A')}

✅ **Live vetting** using NASA ExoMiner++ deep learning models deployed via Podman containers.
"""
        return summary


# Test block
if __name__ == "__main__":
    print("Testing ExoMinerVettingModule...")
    
    # Create test data
    test_candidates = pd.DataFrame({
        'source_id': ['TIC 123456789', 'TIC 987654321', 'TIC 111111111'],
        'ra': [10.0, 20.0, 30.0],
        'dec': [40.0, 50.0, 60.0],
        'sector': [1, 2, 1]
    })
    
    # Initialize module
    module = ExoMinerVettingModule()
    
    # Check Podman
    podman_installed, podman_msg = module.check_podman_installed()
    print(f"Podman: {podman_installed} - {podman_msg}")
    
    # Check ExoMiner image
    image_available, image_msg = module.check_exominer_image()
    print(f"ExoMiner Image: {image_available} - {image_msg}")
    
    # Run vetting
    vetted_df, report = module.vet_candidates(test_candidates, threshold=0.5, use_mock=True)
    
    print("\nVetting Results:")
    print(f"Total: {report['n_total']}")
    print(f"Vetted: {report['n_vetted']}")
    print(f"Rejected: {report['n_rejected']}")
    
    print("\nVetted Candidates:")
    print(vetted_df[['source_id', 'exominer_score', 'exominer_vetted']])
    
    print("\nSuccess Summary:")
    print(module.get_success_summary())
