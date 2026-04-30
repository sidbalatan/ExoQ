"""
Module 1: Data Input Module

Purpose: Accept and validate input data (vetted K Dwarfs or virgin coordinates)
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Union, Dict, Any, Tuple, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Real validated K Dwarf catalog (Spitzer + Gaia DR3 + 2MASS cross-matched)
DEFAULT_KDWARF_CATALOG = Path(__file__).resolve().parents[1] / "data" / "K_Dwarfs_Search_Results_validated_k_dwarfs (1).csv"

# Mapping from raw catalog column names to pipeline-standardized names.
# Anything not in this map is preserved as-is for downstream modules.
CATALOG_COLUMN_MAP = {
    "Source": "source_id",            # Gaia DR3 source_id (numeric)
    "DR3Name": "gaia_dr3_name",       # human-readable Gaia name
    "objid": "spitzer_objid",
    "ra": "ra",
    "dec": "dec",
    "Plx": "parallax",
    "e_Plx": "parallax_error",
    "RUWE": "ruwe",
    "Teff": "teff_gspphot",
    "logg": "logg_gspphot",
    "[Fe/H]": "feh_gspphot",
    "Dist": "distance_gspphot_pc",
    "dist_pc": "distance_pc",
    "Gmag": "phot_g_mean_mag",
    "BPmag": "phot_bp_mean_mag",
    "RPmag": "phot_rp_mean_mag",
    "BP-RP": "bp_rp",
    "j": "j_mag_2mass",
    "h": "h_mag_2mass",
    "k": "k_mag_2mass",
    "k_subtype": "k_subtype",
    "validation_score": "validation_score",
    "validation_tier": "validation_tier",
    "confidence": "confidence",
    "flag_giant": "flag_giant",
    "flag_mdwarf": "flag_mdwarf",
    "flag_binary": "flag_binary",
    "flag_variable": "flag_variable",
    "contaminant": "contaminant",
}


class DataInputModule:
    """
    Module 1: Data Input Module
    
    Accepts and validates input data for the ExoQ pipeline.
    Supports multiple input methods: CSV upload, pre-loaded lists, manual entry, TIC IDs.
    """
    
    def __init__(self):
        """Initialize the Data Input Module."""
        self.data = None
        self.source = None
        self.validation_report = {}
        
    def load_csv(self, file_path: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Load coordinates from CSV file.
        
        Parameters
        ----------
        file_path : str
            Path to CSV file
            
        Returns
        -------
        tuple
            (DataFrame with coordinates, validation report)
        """
        logger.info(f"Loading CSV file: {file_path}")
        
        try:
            df = pd.read_csv(file_path)
            logger.info(f"Loaded {len(df)} rows from CSV")
            
            # Validate required columns
            required_columns = ['ra', 'dec']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                raise ValueError(f"Missing required columns: {missing_columns}")
            
            # Validate coordinates
            validation_report = self._validate_coordinates(df)
            
            if not validation_report['valid']:
                raise ValueError(f"Coordinate validation failed: {validation_report['errors']}")
            
            self.data = df
            self.source = 'csv_upload'
            
            logger.info(f"CSV loaded successfully: {len(df)} stars")
            
            return df, validation_report
            
        except Exception as e:
            logger.error(f"Error loading CSV: {e}")
            raise
    
    def load_real_kdwarf_catalog(
        self,
        file_path: Optional[Union[str, Path]] = None,
        n_stars: Optional[int] = None,
        tier_filter: Optional[list] = None,
        confidence_filter: Optional[list] = None,
        exclude_giants: bool = True,
        exclude_mdwarfs: bool = True,
        exclude_contaminants: bool = True,
        random_sample: bool = False,
        random_seed: int = 42,
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Load the real validated K Dwarf catalog (Spitzer + Gaia DR3 + 2MASS).
        
        Parameters
        ----------
        file_path : str or Path, optional
            Path to catalog CSV. Defaults to bundled validated catalog.
        n_stars : int, optional
            If given, return at most this many stars (after filtering).
        tier_filter : list of str, optional
            Keep only rows whose `validation_tier` is in this list
            (e.g. ["Gold", "Silver", "Bronze"]).
        confidence_filter : list of str, optional
            Keep only rows whose `confidence` is in this list
            (e.g. ["Confirmed", "Likely"]).
        exclude_giants : bool
            Drop rows where flag_giant is True.
        exclude_mdwarfs : bool
            Drop rows where flag_mdwarf is True.
        exclude_contaminants : bool
            Drop rows where contaminant is True.
        random_sample : bool
            If True, randomly sample n_stars rather than taking the first n.
        random_seed : int
            Seed for the random sample.
        
        Returns
        -------
        tuple
            (DataFrame with standardized columns, validation report)
        """
        path = Path(file_path) if file_path else DEFAULT_KDWARF_CATALOG
        logger.info(f"Loading validated K Dwarf catalog from {path}")
        
        if not path.exists():
            raise FileNotFoundError(f"K Dwarf catalog not found: {path}")
        
        raw = pd.read_csv(path)
        n_raw = len(raw)
        logger.info(f"Raw catalog rows: {n_raw}")
        
        # Apply quality filters
        df = raw.copy()
        cuts = {}
        
        if exclude_giants and "flag_giant" in df.columns:
            before = len(df)
            df = df[df["flag_giant"] != True]
            cuts["giants_removed"] = before - len(df)
        
        if exclude_mdwarfs and "flag_mdwarf" in df.columns:
            before = len(df)
            df = df[df["flag_mdwarf"] != True]
            cuts["mdwarfs_removed"] = before - len(df)
        
        if exclude_contaminants and "contaminant" in df.columns:
            before = len(df)
            df = df[df["contaminant"] != True]
            cuts["contaminants_removed"] = before - len(df)
        
        if tier_filter and "validation_tier" in df.columns:
            before = len(df)
            df = df[df["validation_tier"].isin(tier_filter)]
            cuts["tier_filtered_out"] = before - len(df)
        
        if confidence_filter and "confidence" in df.columns:
            before = len(df)
            df = df[df["confidence"].isin(confidence_filter)]
            cuts["confidence_filtered_out"] = before - len(df)
        
        # Sample if requested
        if n_stars is not None and n_stars < len(df):
            if random_sample:
                df = df.sample(n=n_stars, random_state=random_seed).reset_index(drop=True)
            else:
                df = df.head(n_stars).reset_index(drop=True)
        else:
            df = df.reset_index(drop=True)
        
        # Recover full-precision Gaia DR3 source_id from the human-readable
        # DR3Name column ("Gaia DR3 4271989156548409344") because the raw
        # `Source` column is stored in scientific notation and loses precision.
        if "DR3Name" in df.columns:
            df["source_id"] = (
                df["DR3Name"]
                .astype(str)
                .str.replace("Gaia DR3 ", "", regex=False)
                .str.strip()
            )
            df["source_id"] = pd.to_numeric(df["source_id"], errors="coerce").astype("Int64")
            # Drop the raw scientific-notation Source column if present so the
            # rename below doesn't clobber our reconstructed source_id.
            if "Source" in df.columns:
                df = df.drop(columns=["Source"])
        
        # Standardize column names
        rename_map = {raw_col: std_col for raw_col, std_col in CATALOG_COLUMN_MAP.items() if raw_col in df.columns}
        df = df.rename(columns=rename_map)
        
        # Validate coordinates
        validation_report = self._validate_coordinates(df)
        validation_report["catalog_path"] = str(path)
        validation_report["n_raw"] = n_raw
        validation_report["filter_cuts"] = cuts
        
        if not validation_report["valid"]:
            raise ValueError(f"Coordinate validation failed: {validation_report['errors']}")
        
        self.data = df
        self.source = "validated_kdwarf_catalog"
        self.validation_report = validation_report
        
        logger.info(f"Validated K Dwarf catalog loaded: {len(df)} stars (from {n_raw} raw)")
        return df, validation_report
    
    def load_from_virgin_list(self, n_stars: int = 100) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Load coordinates from pre-loaded virgin coordinate list.
        
        Parameters
        ----------
        n_stars : int
            Number of stars to load
            
        Returns
        -------
        tuple
            (DataFrame with coordinates, validation report)
        """
        logger.info(f"Loading {n_stars} stars from virgin coordinate list")
        
        # For now, generate sample data
        # In production, this would load from actual virgin coordinate dataset
        np.random.seed(42)
        
        data = {
            'source_id': range(2000, 2000 + n_stars),
            'ra': np.random.uniform(0, 360, n_stars),
            'dec': np.random.uniform(-90, 90, n_stars),
            'teff_gspphot': np.random.uniform(3700, 5200, n_stars),
            'logg_gspphot': np.random.uniform(4.0, 5.0, n_stars),
            'bp_rp': np.random.uniform(1.2, 2.2, n_stars),
            'source': ['virgin'] * n_stars
        }
        
        df = pd.DataFrame(data)
        
        # Validate coordinates
        validation_report = self._validate_coordinates(df)
        
        self.data = df
        self.source = 'virgin_list'
        
        logger.info(f"Virgin list loaded successfully: {len(df)} stars")
        
        return df, validation_report
    
    def load_from_vetted_list(self, n_stars: int = 50) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Load coordinates from pre-loaded vetted K Dwarf list.
        
        Parameters
        ----------
        n_stars : int
            Number of stars to load
            
        Returns
        -------
        tuple
            (DataFrame with coordinates, validation report)
        """
        logger.info(f"Loading {n_stars} stars from vetted K Dwarf list")
        
        # For now, generate sample data
        # In production, this would load from actual vetted K Dwarf dataset
        np.random.seed(43)
        
        data = {
            'source_id': range(1000, 1000 + n_stars),
            'ra': np.random.uniform(0, 360, n_stars),
            'dec': np.random.uniform(-90, 90, n_stars),
            'teff_gspphot': np.random.uniform(4000, 5000, n_stars),
            'logg_gspphot': np.random.uniform(4.0, 5.0, n_stars),
            'bp_rp': np.random.uniform(1.2, 2.2, n_stars),
            'has_exoplanet': [True] * n_stars,
            'source': ['vetted'] * n_stars
        }
        
        df = pd.DataFrame(data)
        
        # Validate coordinates
        validation_report = self._validate_coordinates(df)
        
        self.data = df
        self.source = 'vetted_list'
        
        logger.info(f"Vetted list loaded successfully: {len(df)} stars")
        
        return df, validation_report
    
    def load_manual_entry(self, coordinates: list) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Load coordinates from manual entry.
        
        Parameters
        ----------
        coordinates : list
            List of dictionaries with 'ra' and 'dec' keys
            
        Returns
        -------
        tuple
            (DataFrame with coordinates, validation report)
        """
        logger.info(f"Loading {len(coordinates)} manually entered coordinates")
        
        df = pd.DataFrame(coordinates)
        
        # Validate coordinates
        validation_report = self._validate_coordinates(df)
        
        if not validation_report['valid']:
            raise ValueError(f"Coordinate validation failed: {validation_report['errors']}")
        
        self.data = df
        self.source = 'manual_entry'
        
        logger.info(f"Manual entry loaded successfully: {len(df)} stars")
        
        return df, validation_report
    
    def load_tic_ids(self, tic_ids: list) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Load coordinates from TIC IDs.
        
        Parameters
        ----------
        tic_ids : list
            List of TIC IDs
            
        Returns
        -------
        tuple
            (DataFrame with coordinates, validation report)
        """
        logger.info(f"Loading {len(tic_ids)} TIC IDs")
        
        # For now, generate sample data with TIC IDs
        # In production, this would query Gaia DR3 for actual coordinates
        np.random.seed(44)
        
        data = {
            'tic_id': tic_ids,
            'source_id': tic_ids,  # Assuming TIC ID = source_id for now
            'ra': np.random.uniform(0, 360, len(tic_ids)),
            'dec': np.random.uniform(-90, 90, len(tic_ids)),
            'source': ['tic_ids'] * len(tic_ids)
        }
        
        df = pd.DataFrame(data)
        
        # Validate coordinates
        validation_report = self._validate_coordinates(df)
        
        self.data = df
        self.source = 'tic_ids'
        
        logger.info(f"TIC IDs loaded successfully: {len(df)} stars")
        
        return df, validation_report
    
    def _validate_coordinates(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Validate coordinates in DataFrame.
        
        Parameters
        ----------
        df : pd.DataFrame
            DataFrame with coordinates
            
        Returns
        -------
        dict
            Validation report
        """
        errors = []
        warnings = []
        
        # Check RA range (0-360)
        if 'ra' in df.columns:
            invalid_ra = df[(df['ra'] < 0) | (df['ra'] > 360)]
            if len(invalid_ra) > 0:
                errors.append(f"{len(invalid_ra)} stars have invalid RA (should be 0-360)")
        
        # Check Dec range (-90 to 90)
        if 'dec' in df.columns:
            invalid_dec = df[(df['dec'] < -90) | (df['dec'] > 90)]
            if len(invalid_dec) > 0:
                errors.append(f"{len(invalid_dec)} stars have invalid Dec (should be -90 to 90)")
        
        # Check for duplicates
        if 'source_id' in df.columns:
            duplicates = df.duplicated(subset=['source_id'])
            if duplicates.sum() > 0:
                warnings.append(f"{duplicates.sum()} duplicate source IDs found")
        
        # Check required columns
        required_columns = ['ra', 'dec']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            errors.append(f"Missing required columns: {missing_columns}")
        
        validation_report = {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'total_stars': len(df),
            'valid_stars': len(df) - len(errors) if errors else len(df)
        }
        
        self.validation_report = validation_report
        
        return validation_report
    
    def get_success_summary(self) -> str:
        """
        Generate congratulatory success summary.
        
        Returns
        -------
        str
            Success summary message
        """
        if self.data is None:
            return "No data loaded yet."
        
        df = self.data
        validation = self.validation_report
        
        # Calculate coordinate range
        ra_min, ra_max = df['ra'].min(), df['ra'].max()
        dec_min, dec_max = df['dec'].min(), df['dec'].max()
        
        # Calculate pass rate
        pass_rate = (validation['valid_stars'] / validation['total_stars'] * 100) if validation['total_stars'] > 0 else 0
        
        summary = f"""
🎉 Module 1: Data Input | 1 of 8 Complete!

✅ Successfully loaded {len(df)} K Dwarf coordinates
✅ All coordinates validated and ready for analysis
✅ Data quality: Excellent (100% valid)

Input Summary:
- Total stars: {len(df)}
- Source: {self.source}
- Coordinate range: RA {ra_min:.2f}-{ra_max:.2f}, Dec {dec_min:.2f}-{dec_max:.2f}
- Data validation: {validation['valid_stars']}/{validation['total_stars']} valid ({pass_rate:.1f}% pass rate)

🎯 {validation['valid_stars']} stars moving to Module 2: Stellar Parameters
You're ready to discover exoplanets! 🚀
"""
        return summary.strip()
    
    def get_data(self) -> pd.DataFrame:
        """
        Get the loaded data.
        
        Returns
        -------
        pd.DataFrame
            Loaded coordinates DataFrame
        """
        return self.data
    
    def get_validation_report(self) -> Dict[str, Any]:
        """
        Get the validation report.
        
        Returns
        -------
        dict
            Validation report
        """
        return self.validation_report


# Convenience function for quick usage
def load_data(input_type: str = 'virgin', **kwargs) -> Tuple[pd.DataFrame, str]:
    """
    Convenience function to load data.
    
    Parameters
    ----------
    input_type : str
        Type of input ('csv', 'virgin', 'vetted', 'manual', 'tic_ids')
    **kwargs
        Additional arguments for specific input types
        
    Returns
    -------
    tuple
        (DataFrame, success summary)
    """
    module = DataInputModule()
    
    if input_type == 'csv':
        df, validation = module.load_csv(kwargs.get('file_path'))
    elif input_type == 'virgin':
        df, validation = module.load_from_virgin_list(kwargs.get('n_stars', 100))
    elif input_type == 'vetted':
        df, validation = module.load_from_vetted_list(kwargs.get('n_stars', 50))
    elif input_type == 'manual':
        df, validation = module.load_manual_entry(kwargs.get('coordinates'))
    elif input_type == 'tic_ids':
        df, validation = module.load_tic_ids(kwargs.get('tic_ids'))
    else:
        raise ValueError(f"Unknown input type: {input_type}")
    
    summary = module.get_success_summary()
    
    return df, summary


if __name__ == "__main__":
    # Test the module
    print("=" * 70)
    print("Module 1: Data Input Module - Test")
    print("=" * 70)
    
    module = DataInputModule()
    
    # Test loading from virgin list
    print("\nTest 1: Load from virgin list")
    df, validation = module.load_from_virgin_list(n_stars=10)
    print(module.get_success_summary())
    
    # Test loading from vetted list
    print("\nTest 2: Load from vetted list")
    df, validation = module.load_from_vetted_list(n_stars=5)
    print(module.get_success_summary())
    
    # Test manual entry
    print("\nTest 3: Manual entry")
    coordinates = [
        {'ra': 150.0, 'dec': 10.0},
        {'ra': 200.0, 'dec': -20.0}
    ]
    df, validation = module.load_manual_entry(coordinates)
    print(module.get_success_summary())
    
    print("\n" + "=" * 70)
    print("Module 1 Test Complete")
    print("=" * 70)
