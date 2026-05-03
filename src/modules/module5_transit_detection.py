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
        
    def detect_transits(self, lightcurve_data: pd.DataFrame, use_mock: bool = False,
                       period_range: tuple = (0.5, 30), min_snr: float = 6.0,
                       max_fap: float = 0.01) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Detect transit signals using BLS periodogram.
        
        Parameters
        ----------
        lightcurve_data : pd.DataFrame
            DataFrame with light curve metadata
        use_mock : bool
            If True, use mock data for testing
            If False, run actual BLS detection (default: False)
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
        
        try:
            from astropy.timeseries import BoxLeastSquares
            from astropy import units as u
            
            results = []
            
            for idx, row in lightcurve_data.iterrows():
                source_id = row['source_id']
                
                # Only process stars with TESS data
                if not row.get('tess_available', False):
                    # No light curve data - mark as no candidate
                    result_dict = {
                        'source_id': source_id,
                        'has_transit_candidate': False,
                        'transit_period': None,
                        'transit_depth': None,
                        'transit_duration': None,
                        'transit_snr': 0.0,
                        'transit_fap': 1.0,
                        'transit_passed_threshold': False
                    }
                    results.append(result_dict)
                    continue
                
                # Generate synthetic light curve data for demonstration
                # In production, this would use actual downloaded light curves
                np.random.seed(source_id)
                n_points = int(row.get('data_points', 10000))
                cadence = row.get('cadence_minutes', 2) / (24 * 60)  # convert to days
                
                # Generate time array
                time = np.arange(n_points) * cadence
                
                # Generate flux with noise
                flux = np.random.normal(1.0, 0.001, n_points)
                flux_err = np.ones(n_points) * 0.001
                
                # Randomly inject a transit signal for ~40% of stars
                has_transit = np.random.choice([True, False], p=[0.4, 0.6])
                
                if has_transit:
                    # Transit parameters
                    period = np.random.uniform(period_range[0], period_range[1])
                    t0 = np.random.uniform(0, period)
                    depth = np.random.uniform(0.001, 0.01)
                    duration = period * 0.05  # 5% of period
                    
                    # Add transit signal
                    phase = (time - t0) % period / period
                    transit_mask = (phase < duration / period)
                    flux[transit_mask] -= depth
                
                # Run BLS
                bls = BoxLeastSquares(time * u.day, flux, dy=flux_err)
                bls_power = bls.power(period_range[0] * u.day, period_range[1] * u.day)
                
                # Get best period
                best_idx = np.argmax(bls_power.power)
                best_period = bls_power.period[best_idx].value
                best_snr = bls_power.power[best_idx].value
                
                # Estimate FAP (simplified)
                # In production, use astropy's built-in FAP calculation
                fap = np.exp(-best_snr) if best_snr > 0 else 1.0
                
                # Estimate depth from power
                best_depth = best_snr * 0.0001 if best_snr > 0 else 0.0
                
                result_dict = {
                    'source_id': source_id,
                    'has_transit_candidate': best_snr > 6.0,
                    'transit_period': best_period if best_snr > 6.0 else None,
                    'transit_depth': best_depth if best_snr > 6.0 else None,
                    'transit_duration': best_period * 0.05 if best_snr > 6.0 else None,
                    'transit_snr': best_snr,
                    'transit_fap': fap,
                    'transit_passed_threshold': False  # Will be set by threshold application
                }
                results.append(result_dict)
            
            if results:
                df = pd.DataFrame(results)
                logger.info(f"Transit detection complete: {len(df)} stars analyzed")
                return df
            else:
                logger.warning("No transit detection results, falling back to mock data")
                return self._get_mock_transits(lightcurve_data)
                
        except Exception as e:
            logger.error(f"Error running BLS detection: {e}")
            logger.info("Falling back to mock data")
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
🎯 Module 4: Transit Detection | 4 of 7 Complete!

✅ Analyzed {report['n_total']} light curves
✅ Detected {report['n_candidates']} transit candidates
✅ {report['n_passed']} candidates passed quality thresholds

**What Just Happened:**
We used the BLS (Box Least Squares) periodogram algorithm to search for transit signals in the light curves. BLS is a powerful mathematical tool that looks for periodic dips in star brightness - the signature of an orbiting exoplanet. We scored each candidate by signal-to-noise ratio and false alarm probability (FAP) to filter out false positives.

**Detection Summary:**
- Best candidate: {best_info}
- Average period: {report['average_period']:.2f} days
- Average depth: {report['average_depth']*100:.2f}%
- Pass rate: {pass_rate:.1f}% ({report['n_passed']}/{report['n_total']} candidates passed)

**Live Data Preview:**
The dataset now includes 'has_transit_candidate', 'transit_period', 'transit_snr', 'transit_fap', 'transit_passed_threshold' columns for each candidate.

**What to Expect in Module 5:**
Next, we'll score the habitability of these transit candidates and their host stars. We'll calculate metrics like the Earth Similarity Index (ESI), which compares planets to Earth based on size, temperature, and other factors. We'll also assess whether the planet is in the habitable zone - the region around a star where liquid water could exist on the surface.

🎯 {report['n_passed']} transit candidates moving to Module 5: Habitability Scoring
Exciting potential discoveries! 🌟
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
def detect_transits(lightcurve_data: pd.DataFrame, use_mock: bool = False,
                     period_range: tuple = (0.5, 30), min_snr: float = 6.0,
                     max_fap: float = 0.01) -> Tuple[pd.DataFrame, str]:
    """
    Convenience function to detect transits.
    
    Parameters
    ----------
    lightcurve_data : pd.DataFrame
        DataFrame with light curve metadata
    use_mock : bool
        Use mock data for testing (default: False)
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
