"""
Module 6: Habitability Scoring Module

Purpose: Score habitability of stars and exoplanet candidates
"""

import pandas as pd
import numpy as np
from typing import Union, Dict, Any, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HabitabilityScoringModule:
    """
    Module 6: Habitability Scoring Module
    
    Scores habitability of stars and exoplanet candidates.
    Calculates Earth Similarity Index (ESI) for exoplanets.
    """
    
    def __init__(self):
        """Initialize the Habitability Scoring Module."""
        self.data = None
        self.scoring_report = {}
        
    def score_habitability(self, stellar_data: pd.DataFrame, transit_data: pd.DataFrame = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Score habitability of stars and exoplanet candidates.
        
        Parameters
        ----------
        stellar_data : pd.DataFrame
            DataFrame with stellar parameters
        transit_data : pd.DataFrame, optional
            DataFrame with transit detection results
            
        Returns
        -------
        tuple
            (DataFrame with habitability scores, scoring report)
        """
        logger.info(f"Scoring habitability for {len(stellar_data)} stars")
        
        # Merge stellar and transit data if provided
        if transit_data is not None:
            df = pd.merge(stellar_data, transit_data, on='source_id', how='left')
        else:
            df = stellar_data.copy()
        
        # Score stellar habitability
        df = self._score_stellar_habitability(df)
        
        # Score exoplanet habitability (if transit data available)
        if 'transit_passed_threshold' in df.columns:
            df = self._score_exoplanet_habitability(df)
        
        # Calculate ESI for exoplanets
        if 'transit_passed_threshold' in df.columns:
            df = self._calculate_esi(df)
        
        # Generate scoring report
        scoring_report = self._generate_scoring_report(df)
        
        self.data = df
        self.scoring_report = scoring_report
        
        logger.info(f"Habitability scoring complete: {scoring_report['n_highly_habitable']} highly habitable stars")
        
        return df, scoring_report
    
    def _score_stellar_habitability(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Score stellar habitability based on stellar parameters.
        
        Parameters
        ----------
        df : pd.DataFrame
            DataFrame with stellar parameters
            
        Returns
        -------
        pd.DataFrame
            DataFrame with stellar habitability scores
        """
        logger.info("Scoring stellar habitability")
        
        # Initialize stellar habitability score
        df['stellar_hab_score'] = 0.0
        
        # Temperature score (optimal: 3900-4800 K)
        temp_score = np.where(
            (df['teff_gspphot'] >= 3900) & (df['teff_gspphot'] <= 4800),
            1.0,
            np.where(
                (df['teff_gspphot'] >= 3700) & (df['teff_gspphot'] < 3900),
                0.7,
                np.where(
                    (df['teff_gspphot'] > 4800) & (df['teff_gspphot'] <= 5200),
                    0.7,
                    0.3
                )
            )
        )
        df['stellar_hab_score'] += temp_score * 0.4
        
        # Surface gravity score (main sequence: > 4.5 dex)
        logg_score = np.where(df['logg_gspphot'] > 4.5, 1.0, 0.5)
        df['stellar_hab_score'] += logg_score * 0.3
        
        # RUWE score (low variability: < 1.2)
        ruwe_score = np.where(df['ruwe'] < 1.2, 1.0, 0.6)
        df['stellar_hab_score'] += ruwe_score * 0.3
        
        return df
    
    def _score_exoplanet_habitability(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Score exoplanet habitability based on transit parameters.
        
        Parameters
        ----------
        df : pd.DataFrame
            DataFrame with transit parameters
            
        Returns
        -------
        pd.DataFrame
            DataFrame with exoplanet habitability scores
        """
        logger.info("Scoring exoplanet habitability")
        
        # Initialize exoplanet habitability score
        df['exo_hab_score'] = 0.0
        
        # Only score candidates that passed thresholds
        candidates = df['transit_passed_threshold'] == True
        
        # Radius score (Earth-like: 0.8-1.5 Earth radii)
        # For mock data, estimate from transit depth
        # depth ≈ (R_planet / R_star)^2, assuming R_star ~ 0.7 R_sun
        if 'transit_depth' in df.columns:
            estimated_radius = np.sqrt(df['transit_depth']) * 0.7 * 109  # in Earth radii
            radius_score = np.where(
                candidates & (estimated_radius >= 0.8) & (estimated_radius <= 1.5),
                1.0,
                np.where(
                    candidates,
                    0.5,
                    0.0
                )
            )
            df['exo_hab_score'] += radius_score * 0.4
        
        # Period score (habitable zone: depends on stellar temperature)
        # For K dwarfs, habitable zone is roughly 5-20 days
        if 'transit_period' in df.columns:
            period_score = np.where(
                candidates & (df['transit_period'] >= 5) & (df['transit_period'] <= 20),
                1.0,
                np.where(
                    candidates,
                    0.3,
                    0.0
                )
            )
            df['exo_hab_score'] += period_score * 0.4
        
        # S/N score (reliable detection: > 8)
        if 'transit_snr' in df.columns:
            snr_score = np.where(
                candidates & (df['transit_snr'] > 8),
                1.0,
                np.where(
                    candidates,
                    0.5,
                    0.0
                )
            )
            df['exo_hab_score'] += snr_score * 0.2
        
        return df
    
    def _calculate_esi(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate Earth Similarity Index (ESI) for exoplanets.
        
        Parameters
        ----------
        df : pd.DataFrame
            DataFrame with stellar and transit parameters
            
        Returns
        -------
        pd.DataFrame
            DataFrame with ESI values
        """
        logger.info("Calculating Earth Similarity Index")
        
        # Initialize ESI
        df['esi'] = 0.0
        
        # Only calculate for candidates that passed thresholds
        candidates = df['transit_passed_threshold'] == True
        
        # Simplified ESI calculation
        # ESI = 1 - sqrt((r - r_earth)^2 + (T - T_earth)^2)
        # where r is radius ratio, T is temperature ratio
        
        if 'transit_depth' in df.columns and 'teff_gspphot' in df.columns:
            # Estimate planet radius
            estimated_radius = np.sqrt(df['transit_depth']) * 0.7 * 109  # in Earth radii
            
            # Estimate equilibrium temperature
            # T_eq = T_star * (R_star / 2a)^{1/2}
            # Simplified: assume a from period, R_star from temperature
            if 'transit_period' in df.columns:
                # Very rough estimate
                estimated_temp = df['teff_gspphot'] * 0.7 * (1 / np.sqrt(df['transit_period']))
                
                # Calculate ESI
                r_ratio = estimated_radius / 1.0  # Earth radius
                t_ratio = estimated_temp / 288  # Earth temperature (K)
                
                esi = 1 - np.sqrt((r_ratio - 1)**2 + (t_ratio - 1)**2)
                esi = np.clip(esi, 0, 1)
                
                df.loc[candidates, 'esi'] = esi.loc[candidates]
        
        return df
    
    def _generate_scoring_report(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate scoring report.
        
        Parameters
        ----------
        df : pd.DataFrame
            DataFrame with habitability scores
            
        Returns
        -------
        dict
            Scoring report
        """
        n_total = len(df)
        n_highly_habitable = (df['stellar_hab_score'] > 0.8).sum()
        n_habitable = (df['stellar_hab_score'] > 0.6).sum()
        
        # Exoplanet habitability
        if 'exo_hab_score' in df.columns:
            n_exo_candidates = (df['transit_passed_threshold'] == True).sum()
            n_habitable_exo = (df['exo_hab_score'] > 0.6).sum()
            
            # Best candidate
            if n_exo_candidates > 0:
                candidates = df[df['transit_passed_threshold'] == True]
                best_star = candidates.loc[candidates['stellar_hab_score'].idxmax()]
                best_star_id = best_star['source_id']
                best_star_score = best_star['stellar_hab_score']
            else:
                best_star_id = None
                best_star_score = 0
        else:
            n_exo_candidates = 0
            n_habitable_exo = 0
            best_star_id = None
            best_star_score = 0
        
        # ESI
        if 'esi' in df.columns:
            max_esi = df['esi'].max()
        else:
            max_esi = 0
        
        report = {
            'n_total': n_total,
            'n_highly_habitable': n_highly_habitable,
            'n_habitable': n_habitable,
            'fraction_highly_habitable': n_highly_habitable / n_total if n_total > 0 else 0,
            'n_exo_candidates': n_exo_candidates,
            'n_habitable_exo': n_habitable_exo,
            'best_star_id': best_star_id,
            'best_star_score': best_star_score,
            'max_esi': max_esi
        }
        
        self.scoring_report = report
        
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
        report = self.scoring_report
        
        summary = f"""
💧 Habitability Scoring Complete!

✅ Scored {report['n_total']} stars for habitability
✅ {report['n_highly_habitable']} stars are highly habitable (score > 0.8)
✅ {report['n_habitable_exo']} exoplanet candidates in habitable zone

Habitability Summary:
- Best host star: TIC {report['best_star_id']} (score = {report['best_star_score']:.2f})
- Most Earth-like planet: ESI = {report['max_esi']:.2f}
- Habitable zone candidates: {report['n_habitable_exo']}

You've found potential Earth 2.0 candidates! 🌏
"""
        return summary.strip()
    
    def get_data(self) -> pd.DataFrame:
        """
        Get the processed data.
        
        Returns
        -------
        pd.DataFrame
            Processed habitability DataFrame
        """
        return self.data
    
    def get_scoring_report(self) -> Dict[str, Any]:
        """
        Get the scoring report.
        
        Returns
        -------
        dict
            Scoring report
        """
        return self.scoring_report


# Convenience function for quick usage
def score_habitability(stellar_data: pd.DataFrame, transit_data: pd.DataFrame = None) -> Tuple[pd.DataFrame, str]:
    """
    Convenience function to score habitability.
    
    Parameters
    ----------
    stellar_data : pd.DataFrame
        DataFrame with stellar parameters
    transit_data : pd.DataFrame, optional
        DataFrame with transit detection results
        
    Returns
    -------
    tuple
        (DataFrame, success summary)
    """
    module = HabitabilityScoringModule()
    df, report = module.score_habitability(stellar_data, transit_data)
    summary = module.get_success_summary()
    
    return df, summary


if __name__ == "__main__":
    # Test the module
    print("=" * 70)
    print("Module 6: Habitability Scoring Module - Test")
    print("=" * 70)
    
    # Create test stellar data
    test_stellar = pd.DataFrame({
        'source_id': range(1000, 1010),
        'ra': np.random.uniform(0, 360, 10),
        'dec': np.random.uniform(-90, 90, 10),
        'teff_gspphot': np.random.uniform(4000, 5000, 10),
        'logg_gspphot': np.random.uniform(4.0, 5.0, 10),
        'ruwe': np.random.uniform(0.8, 1.3, 10)
    })
    
    # Create test transit data
    test_transit = pd.DataFrame({
        'source_id': range(1000, 1010),
        'has_transit_candidate': np.random.choice([True, False], 10, p=[0.4, 0.6]),
        'transit_period': np.random.uniform(1, 25, 10),
        'transit_depth': np.random.uniform(0.005, 0.05, 10),
        'transit_snr': np.random.uniform(6, 15, 10),
        'transit_passed_threshold': np.random.choice([True, False], 10, p=[0.5, 0.5])
    })
    
    module = HabitabilityScoringModule()
    
    print("\nTest 1: Score habitability")
    df, report = module.score_habitability(test_stellar, test_transit)
    print(module.get_success_summary())
    
    print("\nTest 2: Display sample data")
    print(df[['source_id', 'stellar_hab_score', 'exo_hab_score', 'esi']].head())
    
    print("\n" + "=" * 70)
    print("Module 6 Test Complete")
    print("=" * 70)
