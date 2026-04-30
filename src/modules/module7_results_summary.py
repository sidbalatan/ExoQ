"""
Module 7: Results Summary Module

Purpose: Present comprehensive results with visualizations and congratulations
"""

import pandas as pd
import numpy as np
from typing import Union, Dict, Any, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ResultsSummaryModule:
    """
    Module 7: Results Summary Module
    
    Presents comprehensive results with visualizations and congratulations.
    Generates statistical report and downloadable summaries.
    """
    
    def __init__(self):
        """Initialize the Results Summary Module."""
        self.data = None
        self.summary_report = {}
        
    def generate_summary(self, final_data: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Generate comprehensive results summary.
        
        Parameters
        ----------
        final_data : pd.DataFrame
            DataFrame with all pipeline results
            
        Returns
        -------
        tuple
            (DataFrame with summary, summary report)
        """
        logger.info(f"Generating results summary for {len(final_data)} stars")
        
        df = final_data.copy()
        
        # Generate summary statistics
        summary_report = self._generate_summary_statistics(df)
        
        # Identify top discoveries
        top_discoveries = self._identify_top_discoveries(df)
        summary_report['top_discoveries'] = top_discoveries
        
        self.data = df
        self.summary_report = summary_report
        
        logger.info(f"Results summary generated: {summary_report['n_total_stars']} stars analyzed")
        
        return df, summary_report
    
    def _generate_summary_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate summary statistics.
        
        Parameters
        ----------
        df : pd.DataFrame
            DataFrame with pipeline results
            
        Returns
        -------
        dict
            Summary statistics
        """
        report = {
            'n_total_stars': len(df),
            'n_stars_passed_quality': len(df) if 'ruwe' not in df.columns else df['ruwe'].count(),
        }
        
        # Stellar parameters
        if 'teff_gspphot' in df.columns:
            report['teff_range'] = (df['teff_gspphot'].min(), df['teff_gspphot'].max())
        
        # Exoplanet cross-match
        if 'has_exoplanet' in df.columns:
            report['n_known_exoplanets'] = df['has_exoplanet'].sum()
            report['n_virgin_stars'] = (~df['has_exoplanet']).sum()
        
        # Transit detection
        if 'transit_passed_threshold' in df.columns:
            report['n_transit_candidates'] = df['transit_passed_threshold'].sum()
        
        # Habitability
        if 'stellar_hab_score' in df.columns:
            report['n_highly_habitable'] = (df['stellar_hab_score'] > 0.8).sum()
        
        if 'exo_hab_score' in df.columns:
            report['n_habitable_exoplanets'] = (df['exo_hab_score'] > 0.6).sum()
        
        if 'esi' in df.columns:
            report['max_esi'] = df['esi'].max()
        
        return report
    
    def _identify_top_discoveries(self, df: pd.DataFrame) -> list:
        """
        Identify top discoveries.
        
        Parameters
        ----------
        df : pd.DataFrame
            DataFrame with pipeline results
            
        Returns
        -------
        list
            List of top discoveries
        """
        discoveries = []
        
        # Top habitable stars
        if 'stellar_hab_score' in df.columns:
            top_stars = df.nlargest(3, 'stellar_hab_score')
            for _, row in top_stars.iterrows():
                discoveries.append({
                    'type': 'habitable_star',
                    'source_id': row['source_id'],
                    'score': row['stellar_hab_score'],
                    'description': f"Habitable score: {row['stellar_hab_score']:.2f}"
                })
        
        # Top transit candidates
        if 'transit_passed_threshold' in df.columns:
            candidates = df[df['transit_passed_threshold'] == True]
            if len(candidates) > 0:
                top_transits = candidates.nlargest(3, 'transit_snr')
                for _, row in top_transits.iterrows():
                    discoveries.append({
                        'type': 'transit_candidate',
                        'source_id': row['source_id'],
                        'score': row['transit_snr'],
                        'description': f"Transit S/N: {row['transit_snr']:.1f}"
                    })
        
        # Top habitable exoplanets
        if 'exo_hab_score' in df.columns:
            candidates = df[df['exo_hab_score'] > 0]
            if len(candidates) > 0:
                top_exo = candidates.nlargest(3, 'exo_hab_score')
                for _, row in top_exo.iterrows():
                    discoveries.append({
                        'type': 'habitable_exoplanet',
                        'source_id': row['source_id'],
                        'score': row['exo_hab_score'],
                        'description': f"Exoplanet habitability: {row['exo_hab_score']:.2f}"
                    })
        
        return discoveries[:5]  # Return top 5 discoveries
    
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
        
        report = self.summary_report
        
        # Build top discoveries section
        discoveries_text = ""
        for i, discovery in enumerate(report['top_discoveries'][:3], 1):
            discoveries_text += f"{i}. TIC {discovery['source_id']} - {discovery['description']}\n"
        
        # Calculate pass rate
        passed_quality = report.get('n_stars_passed_quality', report['n_total_stars'])
        pass_rate = (passed_quality / report['n_total_stars'] * 100) if report['n_total_stars'] > 0 else 100
        
        summary = f"""
🏆 Module 7: Results Summary | 7 of 8 Complete!

🎉 You've successfully analyzed {report['n_total_stars']} K Dwarf stars!

Key Achievements:
✅ {passed_quality} stars passed all quality filters ({pass_rate:.1f}% pass rate)
✅ {report.get('n_transit_candidates', 0)} exoplanet candidates detected
✅ {report.get('n_highly_habitable', 0)} highly habitable targets identified

Top Discoveries:
{discoveries_text}

🎯 {report['n_total_stars']} stars moving to Module 8: Data Export
Your contributions help humanity's quest for Earth 2.0! 🌍🚀

Download your results using Module 8: Data Export
"""
        return summary.strip()
    
    def get_data(self) -> pd.DataFrame:
        """
        Get the processed data.
        
        Returns
        -------
        pd.DataFrame
            Processed summary DataFrame
        """
        return self.data
    
    def get_summary_report(self) -> Dict[str, Any]:
        """
        Get the summary report.
        
        Returns
        -------
        dict
            Summary report
        """
        return self.summary_report


# Convenience function for quick usage
def generate_summary(final_data: pd.DataFrame) -> Tuple[pd.DataFrame, str]:
    """
    Convenience function to generate summary.
    
    Parameters
    ----------
    final_data : pd.DataFrame
        DataFrame with pipeline results
        
    Returns
    -------
    tuple
        (DataFrame, success summary)
    """
    module = ResultsSummaryModule()
    df, report = module.generate_summary(final_data)
    summary = module.get_success_summary()
    
    return df, summary


if __name__ == "__main__":
    # Test the module
    print("=" * 70)
    print("Module 7: Results Summary Module - Test")
    print("=" * 70)
    
    # Create test final data (simulating full pipeline output)
    test_final = pd.DataFrame({
        'source_id': range(1000, 1010),
        'ra': np.random.uniform(0, 360, 10),
        'dec': np.random.uniform(-90, 90, 10),
        'teff_gspphot': np.random.uniform(4000, 5000, 10),
        'logg_gspphot': np.random.uniform(4.0, 5.0, 10),
        'ruwe': np.random.uniform(0.8, 1.3, 10),
        'has_exoplanet': np.random.choice([True, False], 10, p=[0.3, 0.7]),
        'transit_passed_threshold': np.random.choice([True, False], 10, p=[0.5, 0.5]),
        'transit_snr': np.random.uniform(6, 15, 10),
        'stellar_hab_score': np.random.uniform(0.5, 1.0, 10),
        'exo_hab_score': np.random.uniform(0, 0.9, 10),
        'esi': np.random.uniform(0, 0.8, 10)
    })
    
    module = ResultsSummaryModule()
    
    print("\nTest 1: Generate results summary")
    df, report = module.generate_summary(test_final)
    print(module.get_success_summary())
    
    print("\nTest 2: Display top discoveries")
    for discovery in report['top_discoveries']:
        print(f"{discovery['type']}: TIC {discovery['source_id']} - {discovery['description']}")
    
    print("\n" + "=" * 70)
    print("Module 7 Test Complete")
    print("=" * 70)
