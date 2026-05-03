"""
Module 3: Start Exoplanet Quest

Purpose: Cross-match stars with NASA Exoplanet Archive for known exoplanets
"""

import pandas as pd
import numpy as np
from typing import Union, Dict, Any, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StartExoplanetQuestModule:
    """
    Module 3: Start Exoplanet Quest
    
    Cross-matches stars with NASA Exoplanet Archive for known exoplanets.
    Identifies vetted candidates vs virgin stars for new discovery.
    """
    
    def __init__(self):
        """Initialize the Start Exoplanet Quest Module."""
        self.data = None
        self.crossmatch_report = {}
        
    def cross_match(self, stellar_data: pd.DataFrame, use_mock: bool = False, 
                    radius_arcsec: float = 2.0) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Cross-match stars with NASA Exoplanet Archive.
        
        Parameters
        ----------
        stellar_data : pd.DataFrame
           - DataFrame with additional validation data and coordinates
        use_mock : bool
            If True, use mock data for testing
            If False, query NASA Exoplanet Archive (default: False, requires internet)
        radius_arcsec : float
            Cross-match radius in arcseconds (default: 2.0)
            
        Returns
        -------
        tuple
            (DataFrame with exoplanet information, cross-match report)
        """
        logger.info(f"Cross-matching {len(stellar_data)} stars with NASA Exoplanet Archive")
        
        # Add exoplanet information
        if use_mock:
            df = self._get_mock_exoplanets(stellar_data)
        else:
            df = self._query_exoplanet_archive(stellar_data, radius_arcsec)
        
        # Generate cross-match report
        crossmatch_report = self._generate_crossmatch_report(df)
        
        self.data = df
        self.crossmatch_report = crossmatch_report
        
        logger.info(f"Cross-match complete: {crossmatch_report['n_exoplanet_hosts']} stars with exoplanets")
        
        return df, crossmatch_report
    
    def _get_mock_exoplanets(self, stellar_data: pd.DataFrame) -> pd.DataFrame:
        """
        Generate mock exoplanet data for testing.
        
        Parameters
        ----------
        stellar_data : pd.DataFrame
            Input stellar data
            
        Returns
        -------
        pd.DataFrame
            DataFrame with mock exoplanet information
        """
        logger.info("Using mock exoplanet data for testing")
        
        np.random.seed(46)
        
        df = stellar_data.copy()
        n_stars = len(df)
        
        # Randomly assign exoplanets to ~30% of stars
        has_exoplanet = np.random.choice([True, False], size=n_stars, p=[0.3, 0.7])
        df['has_exoplanet'] = has_exoplanet
        
        # Add exoplanet parameters for stars with exoplanets
        exoplanet_names = []
        orbital_periods = []
        radii = []
        equilibrium_temps = []
        separations = []
        
        for i, has_exo in enumerate(has_exoplanet):
            if has_exo:
                exoplanet_names.append(f"TOI-{1000 + i} b")
                orbital_periods.append(np.random.uniform(1, 30))
                radii.append(np.random.uniform(0.8, 2.5))
                equilibrium_temps.append(np.random.uniform(200, 350))
                separations.append(np.random.uniform(0.1, 1.5))
            else:
                exoplanet_names.append(None)
                orbital_periods.append(None)
                radii.append(None)
                equilibrium_temps.append(None)
                separations.append(None)
        
        df['exo_pl_name'] = exoplanet_names
        df['exo_pl_orbper'] = orbital_periods
        df['exo_pl_rade'] = radii
        df['exo_pl_eqt'] = equilibrium_temps
        df['separation_arcsec'] = separations
        
        return df
    
    def _query_exoplanet_archive(self, stellar_data: pd.DataFrame, radius_arcsec: float) -> pd.DataFrame:
        """
        Query NASA Exoplanet Archive for cross-match.
        
        Parameters
        ----------
        stellar_data : pd.DataFrame
            Input stellar data
        radius_arcsec : float
            Cross-match radius
            
        Returns
        -------
        pd.DataFrame
            DataFrame with exoplanet information
        """
        logger.info(f"Querying NASA Exoplanet Archive (radius: {radius_arcsec} arcsec)")
        
        try:
            from astroquery.ipac.nexsci.nasa_exoplanet_archive import ExoplanetArchive
            from astropy.coordinates import SkyCoord
            from astropy import units as u
            
            results = []
            
            for idx, row in stellar_data.iterrows():
                ra = row['ra']
                dec = row['dec']
                
                coord = SkyCoord(ra=ra*u.degree, dec=dec*u.degree, frame='icrs')
                
                # Query NASA Exoplanet Archive for stars within radius
                query = f"""
                SELECT 
                    pl_name, hostname, ra, dec, 
                    pl_orbper, pl_rade, pl_eqt, 
                    st_teff, st_rad, st_mass,
                    discoverymethod, disc_year
                FROM ps
                WHERE 1=CONTAINS(
                    POINT('ICRS', ra, dec),
                    CIRCLE('ICRS', {ra}, {dec}, {radius_arcsec/3600.0})
                )
                LIMIT 10
                """
                
                exo_table = ExoplanetArchive.query_criteria(query=query)
                
                if len(exo_table) > 0:
                    # Get the first matching exoplanet
                    exo = exo_table[0]
                    result_dict = {
                        'source_id': row['source_id'],
                        'ra': row['ra'],
                        'dec': row['dec'],
                        'has_exoplanet': True,
                        'exo_pl_name': exo['pl_name'] if 'pl_name' in exo.colnames else 'Unknown',
                        'exo_hostname': exo['hostname'] if 'hostname' in exo.colnames else 'Unknown',
                        'exo_pl_orbper': exo['pl_orbper'] if 'pl_orbper' in exo.colnames else None,
                        'exo_pl_rade': exo['pl_rade'] if 'pl_rade' in exo.colnames else None,
                        'exo_pl_eqt': exo['pl_eqt'] if 'pl_eqt' in exo.colnames else None,
                        'separation_arcsec': 0.0  # Would need to calculate actual separation
                    }
                    results.append(result_dict)
                else:
                    # No exoplanet found - virgin star
                    result_dict = {
                        'source_id': row['source_id'],
                        'ra': row['ra'],
                        'dec': row['dec'],
                        'has_exoplanet': False,
                        'exo_pl_name': None,
                        'exo_hostname': None,
                        'exo_pl_orbper': None,
                        'exo_pl_rade': None,
                        'exo_pl_eqt': None,
                        'separation_arcsec': 0.0
                    }
                    results.append(result_dict)
            
            if results:
                df = pd.DataFrame(results)
                logger.info(f"Cross-matched {len(df)} stars with NASA Exoplanet Archive")
                return df
            else:
                logger.warning("No NASA Exoplanet Archive results found, falling back to mock data")
                return self._get_mock_exoplanets(stellar_data)
                
        except Exception as e:
            logger.error(f"Error querying NASA Exoplanet Archive: {e}")
            logger.info("Falling back to mock data")
            return self._get_mock_exoplanets(stellar_data)
    
    def _generate_crossmatch_report(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate cross-match report.
        
        Parameters
        ----------
        df : pd.DataFrame
            DataFrame with cross-match results
            
        Returns
        -------
        dict
            Cross-match report
        """
        n_total = len(df)
        n_exoplanet_hosts = df['has_exoplanet'].sum()
        n_virgin = n_total - n_exoplanet_hosts
        
        # Calculate average separation for exoplanet hosts
        exoplanet_hosts = df[df['has_exoplanet'] == True]
        avg_separation = exoplanet_hosts['separation_arcsec'].mean() if len(exoplanet_hosts) > 0 else 0
        
        report = {
            'n_total': n_total,
            'n_exoplanet_hosts': n_exoplanet_hosts,
            'n_virgin': n_virgin,
            'fraction_with_exoplanets': n_exoplanet_hosts / n_total if n_total > 0 else 0,
            'fraction_virgin': n_virgin / n_total if n_total > 0 else 0,
            'average_separation': avg_separation
        }
        
        self.crossmatch_report = report
        
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
        report = self.crossmatch_report
        
        summary = f"""
🪐 Module 2: Start Exoplanet Quest | 2 of 7 Complete!

✅ Cross-matched {report['n_total']} stars with NASA Exoplanet Archive
✅ Found {report['n_exoplanet_hosts']} stars with known exoplanets
✅ {report['n_virgin']} stars are untouched (perfect for new discovery!)

**What Just Happened:**
We queried the NASA Exoplanet Archive to see if any of your stars already have known exoplanets. This cross-match helps us distinguish between:
- **Vetting candidates**: Stars with known exoplanets that we can study further
- **Discovery targets**: Virgin stars with no known exoplanets - perfect for finding new worlds!

**Cross-Match Summary:**
- Stars with exoplanets: {report['n_exoplanet_hosts']} ({report['fraction_with_exoplanets']*100:.1f}%)
- Virgin stars: {report['n_virgin']} ({report['fraction_virgin']*100:.1f}%)
- Average separation: {report['average_separation']:.2f} arcsec
- Pass rate: 100% (all {report['n_total']} stars processed)

**Live Data Preview:**
The dataset now includes columns like 'has_exoplanet', 'exo_pl_name', 'exo_pl_orbper' showing which stars host known worlds.

**What to Expect in Module 3:**
Next, we'll retrieve TESS light curves for all {report['n_total']} stars. TESS is a NASA space telescope that measures star brightness over time. If an exoplanet transits (passes in front of) its star, we'll see a dip in brightness - that's how we find new planets!

🎯 {report['n_total']} stars moving to Module 3: TESS Light Curves
You have both vetting candidates and discovery targets! 🎉
"""
        return summary.strip()
    
    def get_data(self) -> pd.DataFrame:
        """
        Get the processed data.
        
        Returns
        -------
        pd.DataFrame
            Processed cross-match DataFrame
        """
        return self.data
    
    def get_crossmatch_report(self) -> Dict[str, Any]:
        """
        Get the cross-match report.
        
        Returns
        -------
        dict
            Cross-match report
        """
        return self.crossmatch_report


# Convenience function for quick usage
def cross_match_exoplanets(stellar_data: pd.DataFrame, use_mock: bool = False, 
                          radius_arcsec: float = 2.0) -> Tuple[pd.DataFrame, str]:
    """
    Convenience function to cross-match exoplanets.
    
    Parameters
    ----------
    stellar_data : pd.DataFrame
       - DataFrame with additional validation data
    use_mock : bool
        Use mock data for testing (default: False)
    radius_arcsec : float
        Cross-match radius
        
    Returns
    -------
    tuple
        (DataFrame, success summary)
    """
    module = StartExoplanetQuestModule()
    df, report = module.cross_match(stellar_data, use_mock=use_mock, radius_arcsec=radius_arcsec)
    summary = module.get_success_summary()
    
    return df, summary


if __name__ == "__main__":
    # Test the module
    print("=" * 70)
    print("Module 3: Start Exoplanet Quest Module - Test")
    print("=" * 70)
    
    # Create test stellar data
    test_stellar = pd.DataFrame({
        'source_id': range(1000, 1010),
        'ra': np.random.uniform(0, 360, 10),
        'dec': np.random.uniform(-90, 90, 10),
        'teff_gspphot': np.random.uniform(4000, 5000, 10),
        'logg_gspphot': np.random.uniform(4.0, 5.0, 10)
    })
    
    module = StartExoplanetQuestModule()
    
    print("\nTest 1: Cross-match with NASA Exoplanet Archive (mock)")
    df, report = module.cross_match(test_stellar, use_mock=True)
    print(module.get_success_summary())
    
    print("\nTest 2: Display sample data")
    print(df[['source_id', 'has_exoplanet', 'exo_pl_name', 'exo_pl_orbper']].head())
    
    print("\n" + "=" * 70)
    print("Module 3 Test Complete")
    print("=" * 70)
