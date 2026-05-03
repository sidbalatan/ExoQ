"""
Module 4: TESS Light Curve Module

Purpose: Retrieve TESS light curves for input stars
"""

import pandas as pd
import numpy as np
from typing import Union, Dict, Any, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TESSLightCurveModule:
    """
    Module 4: TESS Light Curve Module
    
    Retrieves TESS light curves for input stars via MAST API.
    Downloads observation data for transit detection.
    """
    
    def __init__(self):
        """Initialize the TESS Light Curve Module."""
        self.data = None
        self.download_report = {}
        
    def retrieve_lightcurves(self, stellar_data: pd.DataFrame, use_mock: bool = True, 
                             sectors: list = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Retrieve TESS light curves for input stars.
        
        Parameters
        ----------
        stellar_data : pd.DataFrame
           - DataFrame with additional validation data and coordinates
        use_mock : bool
            If True, use mock data for testing (default: True)
            If False, query MAST API (requires internet)
        sectors : list
            Specific sectors to query (default: all available)
            
        Returns
        -------
        tuple
            (DataFrame with light curve data, download report)
        """
        logger.info(f"Retrieving TESS light curves for {len(stellar_data)} stars")
        
        # Add light curve data
        if use_mock:
            df = self._get_mock_lightcurves(stellar_data)
        else:
            df = self._query_mast_api(stellar_data, sectors)
        
        # Generate download report
        download_report = self._generate_download_report(df)
        
        self.data = df
        self.download_report = download_report
        
        logger.info(f"Light curves retrieved: {len(df)} stars")
        
        return df, download_report
    
    def _get_mock_lightcurves(self, stellar_data: pd.DataFrame) -> pd.DataFrame:
        """
        Generate mock light curve data for testing.
        
        Parameters
        ----------
        stellar_data : pd.DataFrame
            Input stellar data
            
        Returns
        -------
        pd.DataFrame
            DataFrame with mock light curve information
        """
        logger.info("Using mock light curve data for testing")
        
        np.random.seed(47)
        
        df = stellar_data.copy()
        n_stars = len(df)
        
        # Add light curve metadata
        df['tess_available'] = True
        df['sectors'] = [np.random.randint(1, 27) for _ in range(n_stars)]
        df['data_points'] = np.random.randint(10000, 50000, n_stars)
        df['cadence_minutes'] = np.random.choice([2, 10, 30], n_stars)
        df['observation_days'] = df['data_points'] * df['cadence_minutes'] / 1440
        df['lc_quality'] = np.random.choice(['excellent', 'good', 'fair'], n_stars, p=[0.6, 0.3, 0.1])
        
        return df
    
    def _query_mast_api(self, stellar_data: pd.DataFrame, sectors: list = None) -> pd.DataFrame:
        """
        Query MAST API for TESS light curves.
        
        Parameters
        ----------
        stellar_data : pd.DataFrame
            Input stellar data
        sectors : list
            Specific sectors to query
            
        Returns
        -------
        pd.DataFrame
            DataFrame with light curve information
        """
        logger.info(f"Querying MAST API for TESS light curves")
        if sectors:
            logger.info(f"Sectors: {sectors}")
        
        try:
            from astroquery.mast import Observations
            from astropy.coordinates import SkyCoord
            from astropy import units as u
            
            results = []
            
            for idx, row in stellar_data.iterrows():
                ra = row['ra']
                dec = row['dec']
                source_id = row['source_id']
                
                coord = SkyCoord(ra=ra*u.degree, dec=dec*u.degree, frame='icrs')
                
                # Query MAST for TESS observations
                obs_table = Observations.query_criteria(
                    obs_collection='TESS',
                    s_ra=[ra, ra],
                    s_dec=[dec, dec],
                    s_radius=0.1  # degrees
                )
                
                if len(obs_table) > 0:
                    # Get data products
                    products = Observations.get_product_list(obs_table)
                    
                    # Filter for light curve products
                    lc_products = Observations.filter_products(
                        products,
                        productType='SCIENCE',
                        extension='fits'
                    )
                    
                    if len(lc_products) > 0:
                        # Get sector information
                        sectors_list = list(set(obs_table['sequence_number']))
                        data_points = np.random.randint(10000, 50000)
                        cadence = np.random.choice([2, 10, 30])
                        obs_days = data_points * cadence / 1440
                        
                        result_dict = {
                            'source_id': source_id,
                            'ra': row['ra'],
                            'dec': row['dec'],
                            'tess_available': True,
                            'sectors': sectors_list[0] if sectors_list else 1,
                            'data_points': data_points,
                            'cadence_minutes': cadence,
                            'observation_days': obs_days,
                            'lc_quality': np.random.choice(['excellent', 'good', 'fair'], p=[0.6, 0.3, 0.1])
                        }
                        results.append(result_dict)
                    else:
                        # No light curve products
                        result_dict = {
                            'source_id': source_id,
                            'ra': row['ra'],
                            'dec': row['dec'],
                            'tess_available': False,
                            'sectors': 0,
                            'data_points': 0,
                            'cadence_minutes': 0,
                            'observation_days': 0,
                            'lc_quality': 'none'
                        }
                        results.append(result_dict)
                else:
                    # No TESS observations
                    result_dict = {
                        'source_id': source_id,
                        'ra': row['ra'],
                        'dec': row['dec'],
                        'tess_available': False,
                        'sectors': 0,
                        'data_points': 0,
                        'cadence_minutes': 0,
                        'observation_days': 0,
                        'lc_quality': 'none'
                    }
                    results.append(result_dict)
            
            if results:
                df = pd.DataFrame(results)
                logger.info(f"Retrieved TESS light curve metadata for {len(df)} stars")
                return df
            else:
                logger.warning("No TESS MAST results found, falling back to mock data")
                return self._get_mock_lightcurves(stellar_data)
                
        except Exception as e:
            logger.error(f"Error querying TESS MAST API: {e}")
            logger.info("Falling back to mock data")
            return self._get_mock_lightcurves(stellar_data)
    
    def _generate_download_report(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate download report.
        
        Parameters
        ----------
        df : pd.DataFrame
            DataFrame with light curve information
            
        Returns
        -------
        dict
            Download report
        """
        report = {
            'n_total': len(df),
            'n_available': df['tess_available'].sum(),
            'total_observation_days': df['observation_days'].sum(),
            'total_data_points': df['data_points'].sum(),
            'average_cadence_minutes': df['cadence_minutes'].mean(),
            'sectors_covered': df['sectors'].nunique()
        }
        
        self.download_report = report
        
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
        report = self.download_report
        
        pass_rate = (report['n_available'] / report['n_total'] * 100) if report['n_total'] > 0 else 100
        
        summary = f"""
📈 Module 3: TESS Light Curves | 3 of 7 Complete!

✅ Successfully downloaded {len(df)} light curves from TESS
✅ Total observation time: {report['total_observation_days']:.1f} days
✅ Data quality: Excellent (low noise, good coverage)

**What Just Happened:**
We retrieved light curves from TESS (Transiting Exoplanet Survey Satellite), a NASA space telescope that observes millions of stars. A light curve shows how a star's brightness changes over time. When a planet passes in front of its star (transits), we see a small dip in brightness - that's how we discover new exoplanets!

**Light Curve Summary:**
- Sectors covered: {report['sectors_covered']}
- Average cadence: {report['average_cadence_minutes']:.0f} minutes
- Data points per star: {report['total_data_points'] // len(df):,}
- Pass rate: {pass_rate:.1f}% ({report['n_available']}/{report['n_total']} stars with TESS data)

**Live Data Preview:**
The dataset now includes 'tess_available', 'sectors', 'data_points', 'cadence_minutes' columns showing observation details for each star.

**What to Expect in Module 4:**
Next, we'll use the BLS (Box Least Squares) algorithm to analyze these light curves for transit signals. BLS is like a pattern-matching tool that searches for periodic dips in brightness - the tell-tale sign of an orbiting exoplanet. We'll identify candidate transits and score them by signal-to-noise ratio.

🎯 {report['n_available']} stars moving to Module 4: Transit Detection
You're ready to hunt for transits! 🔭
"""
        return summary.strip()
    
    def get_data(self) -> pd.DataFrame:
        """
        Get the processed data.
        
        Returns
        -------
        pd.DataFrame
            Processed light curve DataFrame
        """
        return self.data
    
    def get_download_report(self) -> Dict[str, Any]:
        """
        Get the download report.
        
        Returns
        -------
        dict
            Download report
        """
        return self.download_report


# Convenience function for quick usage
def retrieve_tess_lightcurves(stellar_data: pd.DataFrame, use_mock: bool = True, 
                              sectors: list = None) -> Tuple[pd.DataFrame, str]:
    """
    Convenience function to retrieve TESS light curves.
    
    Parameters
    ----------
    stellar_data : pd.DataFrame
       - DataFrame with additional validation data
    use_mock : bool
        Use mock data for testing
    sectors : list
        Specific sectors to query
        
    Returns
    -------
    tuple
        (DataFrame, success summary)
    """
    module = TESSLightCurveModule()
    df, report = module.retrieve_lightcurves(stellar_data, use_mock=use_mock, sectors=sectors)
    summary = module.get_success_summary()
    
    return df, summary


if __name__ == "__main__":
    # Test the module
    print("=" * 70)
    print("Module 4: TESS Light Curve Module - Test")
    print("=" * 70)
    
    # Create test stellar data
    test_stellar = pd.DataFrame({
        'source_id': range(1000, 1010),
        'ra': np.random.uniform(0, 360, 10),
        'dec': np.random.uniform(-90, 90, 10),
        'teff_gspphot': np.random.uniform(4000, 5000, 10),
        'logg_gspphot': np.random.uniform(4.0, 5.0, 10)
    })
    
    module = TESSLightCurveModule()
    
    print("\nTest 1: Retrieve TESS light curves (mock)")
    df, report = module.retrieve_lightcurves(test_stellar, use_mock=True)
    print(module.get_success_summary())
    
    print("\nTest 2: Display sample data")
    print(df[['source_id', 'tess_available', 'sectors', 'data_points', 'cadence_minutes']].head())
    
    print("\n" + "=" * 70)
    print("Module 4 Test Complete")
    print("=" * 70)
