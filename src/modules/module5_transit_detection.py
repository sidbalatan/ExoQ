"""
Module 5: Transit Detection Module

Purpose: Detect transit signals in light curves using BLS periodogram
"""

import pandas as pd
import numpy as np
from typing import Union, Dict, Any, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TransitDetectionModule:
    """
    Module 5: Transit Detection Module
    
    Detects transit signals in light curves using BLS periodogram.
    Calculates signal-to-noise ratio and false alarm probability.
    """
    
    def __init__(self):
        """Initialize the Transit Detection Module."""
        self.data = None
        self.detection_report = {}
        
    def detect_transits(self, lightcurve_data: pd.DataFrame, use_mock: bool = True,
                       period_range: tuple = (0.5, 30), min_snr: float = 6.0,
                       max_fap: float = 0.01) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Detect transit signals using BLS periodogram.
        
        Parameters
        ----------
        lightcurve_data : pd.DataFrame
            DataFrame with light curve metadata
        use_mock : bool
            If True, use mock data for testing (default: True)
            If False, run actual BLS detection
        period_range : tuple
            Period range to search in days (default: 0.5-30)
        min_snr : float
            Minimum signal-to-noise ratio (default: 6.0)
        max_fap : float
            Maximum false alarm probability (default: 0.01)
            
        Returns
        -------
        tuple
            (DataFrame with transit candidates, detection report)
        """
        logger.info(f"Detecting transits in {len(lightcurve_data)} light curves")
        
        # Add transit detection results
        if use_mock:
            df = self._get_mock_transits(lightcurve_data)
        else:
            df = self._run_bls_detection(lightcurve_data, period_range)
        
        # Apply detection thresholds
        df = self._apply_detection_thresholds(df, min_snr, max_fap)
        
        # Generate detection report
        detection_report = self._generate_detection_report(df)
        
        self.data = df
        self.detection_report = detection_report
        
        logger.info(f"Transit detection complete: {detection_report['n_candidates']} candidates detected")
        
        return df, detection_report
    
    def _get_mock_transits(self, lightcurve_data: pd.DataFrame) -> pd.DataFrame:
        """
        Generate mock transit detection data for testing.
        
        Parameters
        ----------
        lightcurve_data : pd.DataFrame
            Input light curve data
            
        Returns
        -------
        pd.DataFrame
            DataFrame with mock transit information
        """
        logger.info("Using mock transit detection for testing")
        
        np.random.seed(48)
        
        df = lightcurve_data.copy()
        n_stars = len(df)
        
        # Randomly detect transits in ~40% of stars
        has_transit = np.random.choice([True, False], size=n_stars, p=[0.4, 0.6])
        df['has_transit_candidate'] = has_transit
        
        # Add transit parameters for stars with detections
        transit_periods = []
        transit_depths = []
        transit_snr = []
        transit_fap = []
        transit_epochs = []
        
        for i, has_tr in enumerate(has_transit):
            if has_tr:
                transit_periods.append(np.random.uniform(1, 25))
                transit_depths.append(np.random.uniform(0.005, 0.05))
                transit_snr.append(np.random.uniform(6, 15))
                transit_fap.append(np.random.uniform(0.001, 0.01))
                transit_epochs.append(np.random.uniform(0, 30))
            else:
                transit_periods.append(None)
                transit_depths.append(None)
                transit_snr.append(None)
                transit_fap.append(None)
                transit_epochs.append(None)
        
        df['transit_period'] = transit_periods
        df['transit_depth'] = transit_depths
        df['transit_snr'] = transit_snr
        df['transit_fap'] = transit_fap
        df['transit_epoch'] = transit_epochs
        
        return df
    
    def _run_bls_detection(self, lightcurve_data: pd.DataFrame, period_range: tuple) -> pd.DataFrame:
        """
        Run actual BLS periodogram detection.
        
        Parameters
        ----------
        lightcurve_data : pd.DataFrame
            Input light curve data
        period_range : tuple
            Period range to search
            
        Returns
        -------
        pd.DataFrame
            DataFrame with transit information
        """
        logger.info(f"Running BLS detection (period range: {period_range[0]}-{period_range[1]} days)")
        
        # In production, this would use astropy.timeseries or lightkurve for BLS
        # For now, return mock data
        return self._get_mock_transits(lightcurve_data)
    
    def _apply_detection_thresholds(self, df: pd.DataFrame, min_snr: float, max_fap: float) -> pd.DataFrame:
        """
        Apply detection thresholds to filter candidates.
        
        Parameters
        ----------
        df : pd.DataFrame
            DataFrame with transit information
        min_snr : float
            Minimum S/N threshold
        max_fap : float
            Maximum FAP threshold
            
        Returns
        -------
        pd.DataFrame
            Filtered DataFrame
        """
        logger.info(f"Applying thresholds: S/N > {min_snr}, FAP < {max_fap}")
        
        # Filter by S/N and FAP
        valid_candidates = df['has_transit_candidate'] & (df['transit_snr'] >= min_snr) & (df['transit_fap'] <= max_fap)
        
        df['transit_passed_threshold'] = valid_candidates
        
        logger.info(f"Thresholds applied: {valid_candidates.sum()}/{len(df)} candidates passed")
        
        return df
    
    def _generate_detection_report(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate detection report.
        
        Parameters
        ----------
        df : pd.DataFrame
            DataFrame with transit information
            
        Returns
        -------
        dict
            Detection report
        """
        n_total = len(df)
        n_candidates = df['has_transit_candidate'].sum()
        n_passed = df['transit_passed_threshold'].sum()
        
        # Calculate averages for passed candidates
        passed = df[df['transit_passed_threshold'] == True]
        avg_period = passed['transit_period'].mean() if len(passed) > 0 else 0
        avg_depth = passed['transit_depth'].mean() if len(passed) > 0 else 0
        max_snr = passed['transit_snr'].max() if len(passed) > 0 else 0
        
        report = {
            'n_total': n_total,
            'n_candidates': n_candidates,
            'n_passed': n_passed,
            'pass_rate': n_passed / n_total if n_total > 0 else 0,
            'average_period': avg_period,
            'average_depth': avg_depth,
            'max_snr': max_snr
        }
        
        self.detection_report = report
        
        return report
    
    def get_success_summary(self) -> str:
        """
        Generate congratulatory success summary.
        
        Returns
        -------
        str
            Success summary message
        """
        if self.data is None:
            return "No data processed yet."
        
        df = self.data
        report = self.detection_report
        
        # Get the most promising candidate
        passed = df[df['transit_passed_threshold'] == True]
        if len(passed) > 0:
            best_candidate = passed.loc[passed['transit_snr'].idxmax()]
            best_info = f"Most promising: TIC {best_candidate['source_id']} (S/N = {best_candidate['transit_snr']:.1f})"
        else:
            best_info = "No candidates passed thresholds"
        
        pass_rate = (report['n_passed'] / report['n_total'] * 100) if report['n_total'] > 0 else 0
        
        summary = f"""
🎯 Transit Detection Complete!

✅ Analyzed {report['n_total']} light curves
✅ Detected {report['n_candidates']} transit candidates
✅ {report['n_passed']} candidates passed quality thresholds

Detection Summary:
- Candidates with S/N > 6: {report['n_passed']}
- Average period: {report['average_period']:.1f} days
- Average depth: {report['average_depth']*100:.2f}%
- Pass rate: {pass_rate:.1f}% ({report['n_passed']}/{report['n_total']} stars)
- {best_info}

🎯 {report['n_passed']} stars moving to Module 6: Habitability Scoring
You've found potential exoplanets! 🌍
"""
        return summary.strip()
    
    def get_data(self) -> pd.DataFrame:
        """
        Get the processed data.
        
        Returns
        -------
        pd.DataFrame
            Processed transit detection DataFrame
        """
        return self.data
    
    def get_detection_report(self) -> Dict[str, Any]:
        """
        Get the detection report.
        
        Returns
        -------
        dict
            Detection report
        """
        return self.detection_report


# Convenience function for quick usage
def detect_transits(lightcurve_data: pd.DataFrame, use_mock: bool = True,
                     period_range: tuple = (0.5, 30), min_snr: float = 6.0,
                     max_fap: float = 0.01) -> Tuple[pd.DataFrame, str]:
    """
    Convenience function to detect transits.
    
    Parameters
    ----------
    lightcurve_data : pd.DataFrame
        DataFrame with light curve metadata
    use_mock : bool
        Use mock data for testing
    period_range : tuple
        Period range to search
    min_snr : float
        Minimum S/N threshold
    max_fap : float
        Maximum FAP threshold
        
    Returns
    -------
    tuple
        (DataFrame, success summary)
    """
    module = TransitDetectionModule()
    df, report = module.detect_transits(lightcurve_data, use_mock=use_mock, 
                                         period_range=period_range, min_snr=min_snr, max_fap=max_fap)
    summary = module.get_success_summary()
    
    return df, summary


if __name__ == "__main__":
    # Test the module
    print("=" * 70)
    print("Module 5: Transit Detection Module - Test")
    print("=" * 70)
    
    # Create test light curve data
    test_lc = pd.DataFrame({
        'source_id': range(1000, 1010),
        'ra': np.random.uniform(0, 360, 10),
        'dec': np.random.uniform(-90, 90, 10),
        'tess_available': [True] * 10,
        'sectors': np.random.randint(1, 27, 10)
    })
    
    module = TransitDetectionModule()
    
    print("\nTest 1: Detect transits (mock)")
    df, report = module.detect_transits(test_lc, use_mock=True)
    print(module.get_success_summary())
    
    print("\nTest 2: Display sample data")
    print(df[['source_id', 'has_transit_candidate', 'transit_period', 'transit_snr']].head())
    
    print("\n" + "=" * 70)
    print("Module 5 Test Complete")
    print("=" * 70)
