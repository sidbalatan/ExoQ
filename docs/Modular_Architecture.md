# ExoQ Modular Architecture

**Development Philosophy:** Build by modules, test each module to 101% completion before moving to next  
**Goal:** Each module runs independently with clear inputs, outputs, and success summaries  
**Status:** Design Phase

---

## Module Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    ExoQ Modular Pipeline                      │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│  Module 0    │   │  Module 1    │   │  Module 2    │
│  User Home   │───▶│  Data Input  │───▶│  Stellar     │
│  Page        │   │              │   │  Parameters  │
└──────────────┘   └──────────────┘   └──────────────┘
                            │
                            ▼
                  ┌──────────────┐
                  │  Module 3    │
                  │  Exoplanet   │
                  │  Cross-Match │
                  └──────────────┘
                            │
                            ▼
                  ┌──────────────┐
                  │  Module 4    │
                  │  TESS Light  │
                  │  Curves      │
                  └──────────────┘
                            │
                            ▼
                  ┌──────────────┐
                  │  Module 5    │
                  │  Transit     │
                  │  Detection   │
                  └──────────────┘
                            │
                            ▼
                  ┌──────────────┐
                  │  Module 6    │
                  │  Habitability │
                  │  Scoring     │
                  └──────────────┘
                            │
                            ▼
                  ┌──────────────┐
                  │  Module 7    │
                  │  Results     │
                  │  Summary     │
                  └──────────────┘
                            │
                            ▼
                  ┌──────────────┐
                  │  Module 8    │
                  │  Data Export │
                  └──────────────┘
```

---

## Module 0: User Home Page Module

**Purpose:** Main landing page and navigation hub for ExoQ platform

**Inputs:**
- User authentication status (logged in/out)
- User session state
- User preferences

**Outputs:**
- Navigation to other modules
- User dashboard display
- Quick stats display
- Recent activity feed

**Features:**

**Landing Page Components:**
- Hero section with mission statement
- Quick demo button (simulated pipeline run)
- Register/Login buttons
- Quick stats (community members, stars analyzed, discoveries)

**Dashboard Components (if logged in):**
- User summary (stars analyzed, exoplanets discovered, storage used)
- Recent activity feed
- Quick actions (new search, view saved coordinates, view gallery)
- Module access buttons

**Navigation:**
- Module 1: Data Input
- Module 2: Stellar Parameters
- Module 3: Exoplanet Cross-Match
- Module 4: TESS Light Curves
- Module 5: Transit Detection
- Module 6: Habitability Scoring
- Module 7: Results Summary
- Module 8: Data Export
- ExoQ Hunter Game
- Community Gallery
- Personal Dashboard

**Success Summary (Congratulatory Tone):**
```
🏠 Welcome to ExoQ!

✅ Platform loaded successfully
✅ All modules ready for use
✅ Community thriving with [N] active users

Quick Stats:
- Stars analyzed today: [N]
- New discoveries: [N]
- Community members: [N]

Ready to find Earth 2.0? Let's go! 🚀
```

**File Structure:**
```
streamlit_app/
├── Home.py (Module 0)
└── pages/
    ├── 01_Register.py
    ├── 02_User_Dashboard.py
    ├── 03_Data_Input.py (Module 1)
    ├── 04_Stellar_Parameters.py (Module 2)
    ├── 05_Exoplanet_Crossmatch.py (Module 3)
    ├── 06_TESS_Lightcurves.py (Module 4)
    ├── 07_Transit_Detection.py (Module 5)
    ├── 08_Habitability_Scoring.py (Module 6)
    ├── 09_Results_Summary.py (Module 7)
    ├── 10_Data_Export.py (Module 8)
    ├── 11_ExoQ_Hunter.py
    └── 12_Community_Gallery.py
```

---

## Module 1: Data Input Module

**Purpose:** Accept and validate input data (vetted K Dwarfs or virgin coordinates)

**Inputs:**
- Option A: Upload CSV file with vetted K Dwarfs
- Option B: Select from pre-loaded virgin coordinate list
- Option C: Manual coordinate entry (RA, Dec)
- Option D: Paste TIC IDs

**Outputs:**
- Validated DataFrame with coordinates
- Data quality report
- Input summary statistics

**Validation:**
- Check coordinate format (RA: 0-360, Dec: -90 to 90)
- Check for duplicates
- Check required columns (if CSV upload)
- Check TIC ID format (if provided)

**Success Summary (Congratulatory Tone):**
```
🎉 Data Input Complete!

✅ Successfully loaded [N] K Dwarf coordinates
✅ All coordinates validated and ready for analysis
✅ Data quality: Excellent (100% valid)

Input Summary:
- Total stars: [N]
- Source: [vetted/virgin/custom]
- Coordinate range: RA [min-max], Dec [min-max]
- Average distance: [X] light-years

You're ready to discover exoplanets! 🚀
```

**File Structure:**
```
src/modules/
├── module1_data_input.py
└── tests/
    └── test_module1_data_input.py
```

---

## Module 2: Stellar Parameter Module

**Purpose:** Retrieve stellar parameters from Gaia DR3 for input coordinates

**Inputs:**
- DataFrame with coordinates (RA, Dec) or TIC IDs
- Optional: Maximum radius for query (arcseconds)

**Outputs:**
- DataFrame with Gaia DR3 parameters
- Stellar quality metrics
- Parameter completeness report

**Parameters Retrieved:**
- source_id, ra, dec
- teff_gspphot (effective temperature)
- logg_gspphot (surface gravity)
- bp_rp (color)
- ruwe (renormalized unit weight error)
- parallax, parallax_over_error
- phot_g_mean_mag, phot_bp_mean_mag, phot_rp_mean_mag

**Quality Cuts:**
- ruwe < 1.4
- parallax_over_error > 10
- teff_gspphot between 3700-5200 K (K Dwarf range)
- logg_gspphot > 4.0 (main sequence)

**Success Summary (Congratulatory Tone):**
```
🌟 Stellar Parameters Retrieved!

✅ Successfully retrieved [N] stellar parameters from Gaia DR3
✅ Quality filters applied: [X] stars passed all cuts
✅ Parameter completeness: [X]%

Stellar Summary:
- Temperature range: [min-max] K (K Dwarf range ✓)
- Surface gravity: [min-max] dex (main sequence ✓)
- Data quality: Excellent (ruwe < 1.4, parallax S/N > 10)

Your K Dwarf sample is scientifically robust! 🎯
```

**File Structure:**
```
src/modules/
├── module2_stellar_parameters.py
└── tests/
    └── test_module2_stellar_parameters.py
```

---

## Module 3: Exoplanet Cross-Match Module

**Purpose:** Cross-match stars with NASA Exoplanet Archive for known exoplanets

**Inputs:**
- DataFrame with stellar parameters and coordinates
- Cross-match radius (default: 2 arcseconds)

**Outputs:**
- DataFrame with exoplanet information
- Cross-match statistics
- Known exoplanet list

**Cross-Match Process:**
1. Query NASA Exoplanet Archive for stars within radius
2. Match by position (RA, Dec)
3. Retrieve exoplanet parameters:
   - pl_name (planet name)
   - pl_orbper (orbital period)
   - pl_rade (radius in Earth radii)
   - pl_eqt (equilibrium temperature)
   - st_refname (host star reference)

**Success Summary (Congratulatory Tone):**
```
🪐 Exoplanet Cross-Match Complete!

✅ Cross-matched [N] stars with NASA Exoplanet Archive
✅ Found [X] stars with known exoplanets
✅ [Y] stars are untouched (perfect for new discovery!)

Cross-Match Summary:
- Stars with exoplanets: [X] ([X%])
- Virgin stars: [Y] ([Y%])
- Average separation: [X] arcsec

You have both vetting candidates and discovery targets! 🎉
```

**File Structure:**
```
src/modules/
├── module3_exoplanet_crossmatch.py
└── tests/
    └── test_module3_exoplanet_crossmatch.py
```

---

## Module 4: TESS Light Curve Module

**Purpose:** Retrieve TESS light curves for input stars

**Inputs:**
- DataFrame with TIC IDs or coordinates
- Optional: Sectors to query (default: all available)

**Outputs:**
- Light curve data (time, flux, flux_err)
- Light curve metadata
- Download statistics

**Data Sources:**
- MAST API (TESS mission)
- lightkurve package for download

**Success Summary (Congratulatory Tone):**
```
📈 TESS Light Curves Retrieved!

✅ Successfully downloaded [N] light curves from TESS
✅ Total observation time: [X] days
✅ Data quality: Excellent (low noise, good coverage)

Light Curve Summary:
- Sectors covered: [X]
- Average cadence: [X] minutes
- Data points per star: [X]

You're ready to hunt for transits! 🔭
```

**File Structure:**
```
src/modules/
├── module4_tess_lightcurves.py
└── tests/
    └── test_module4_tess_lightcurves.py
```

---

## Module 5: Transit Detection Module

**Purpose:** Detect transit signals in light curves using BLS periodogram

**Inputs:**
- Light curve data (time, flux, flux_err)
- Optional: BLS parameters (period range, frequency grid)

**Outputs:**
- Transit candidates
- BLS periodogram results
- Detection statistics

**Detection Method:**
- Box Least Squares (BLS) periodogram
- Signal-to-noise ratio (S/N) calculation
- False alarm probability (FAP) calculation

**Parameters:**
- Period range: 0.5 - 30 days (typical for Earth-sized planets)
- Frequency grid: 100,000 points
- Minimum S/N: 6.0
- Maximum FAP: 0.01

**Success Summary (Congratulatory Tone):**
```
🎯 Transit Detection Complete!

✅ Analyzed [N] light curves
✅ Detected [X] transit candidates
✅ [Y] candidates passed quality thresholds

Detection Summary:
- Candidates with S/N > 6: [X]
- Average period: [X] days
- Average depth: [X]%
- Most promising: [TIC ID] (S/N = [X])

You've found potential exoplanets! 🌍
```

**File Structure:**
```
src/modules/
├── module5_transit_detection.py
└── tests/
    └── test_module5_transit_detection.py
```

---

## Module 6: Habitability Scoring Module

**Purpose:** Score habitability of stars and exoplanet candidates

**Inputs:**
- DataFrame with stellar parameters
- DataFrame with exoplanet candidates (from Module 3 or 5)

**Outputs:**
- Stellar habitability scores
- Exoplanet habitability scores
- Earth Similarity Index (ESI)

**Scoring Criteria:**

**Stellar Habitability:**
- Temperature: 3900-4800 K (optimal)
- Surface gravity: > 4.5 dex (main sequence)
- Metallicity: > -0.5 dex
- Activity: Low (low variability)
- Age: > 1 Gyr

**Exoplanet Habitability:**
- Radius: 0.8-1.5 Earth radii
- Orbital period: Within habitable zone
- Equilibrium temperature: 200-350 K
- Star type: K Dwarf

**Success Summary (Congratulatory Tone):**
```
💧 Habitability Scoring Complete!

✅ Scored [N] stars for habitability
✅ [X] stars are highly habitable (score > 0.8)
✅ [Y] exoplanet candidates in habitable zone

Habitability Summary:
- Best host star: [TIC ID] (score = [X])
- Most Earth-like planet: [planet name] (ESI = [X])
- Habitable zone candidates: [X]

You've found potential Earth 2.0 candidates! 🌏
```

**File Structure:**
```
src/modules/
├── module6_habitability_scoring.py
└── tests/
    └── test_module6_habitability_scoring.py
```

---

## Module 7: Results Summary Module

**Purpose:** Present comprehensive results with visualizations and congratulations

**Inputs:**
- Outputs from all previous modules
- User preferences (what to display)

**Outputs:**
- Visual summary dashboard
- Statistical report
- Downloadable reports (CSV, JSON, PDF)

**Visualizations:**
- Temperature vs gravity plot (K Dwarf diagram)
- Habitability score distribution
- Transit periodogram
- Light curve with detected transit
- Sky map of targets

**Success Summary (Congratulatory Tone):**
```
🏆 ExoQ Pipeline Complete! Congratulations!

🎉 You've successfully analyzed [N] K Dwarf stars!

Key Achievements:
✅ [X] stars passed all quality filters
✅ [Y] exoplanet candidates detected
✅ [Z] highly habitable targets identified

Top Discoveries:
1. [TIC ID] - Habitable score: [X], Transit S/N: [X]
2. [TIC ID] - Habitable score: [X], Transit S/N: [X]
3. [TIC ID] - Habitable score: [X], Known exoplanet: [name]

Your contributions help humanity's quest for Earth 2.0! 🌍🚀

Download your results below:
[CSV] [JSON] [PDF]
```

**File Structure:**
```
src/modules/
├── module7_results_summary.py
└── tests/
    └── test_module7_results_summary.py
```

---

## Module 8: Data Export Module

**Purpose:** Export results in multiple formats for user records

**Inputs:**
- Complete results DataFrame
- User preferences (format, what to include)

**Outputs:**
- CSV file (spreadsheet-friendly)
- JSON file (machine-readable)
- FITS files (astronomical standard)
- Plots (PNG, PDF)

**Export Options:**
- Include/exclude raw data
- Include/exclude intermediate results
- Custom filename prefix
- Compression option

**Success Summary (Congratulatory Tone):**
```
💾 Data Export Complete!

✅ Results exported successfully
✅ All formats generated and ready for download

Export Summary:
- CSV file: [filename].csv ([X] KB)
- JSON file: [filename].json ([X] KB)
- FITS files: [N] files
- Plots: [N] images

Your scientific data is saved and ready to share! 🎓
```

**File Structure:**
```
src/modules/
├── module8_data_export.py
└── tests/
    └── test_module8_data_export.py
```

---

## Module Independence

Each module is designed to:
1. **Run independently** - can be tested without other modules
2. **Have clear inputs** - defined data structures
3. **Have clear outputs** - standardized DataFrames
4. **Include tests** - unit tests for each module
5. **Have success summary** - congratulatory tone with statistics
6. **Handle errors gracefully** - informative error messages
7. **Log progress** - detailed logging for debugging

---

## Module Testing Strategy

**For each module:**
1. Create sample input data
2. Run module independently
3. Verify outputs match expected format
4. Check success summary displays correctly
5. Test error handling with invalid inputs
6. Verify module can be imported and used standalone

**Test Command:**
```bash
python -m src.modules.test_moduleX
```

---

## Module Integration

**Full Pipeline:**
```python
from src.modules import (
    module1_data_input,
    module2_stellar_parameters,
    module3_exoplanet_crossmatch,
    module4_tess_lightcurves,
    module5_transit_detection,
    module6_habitability_scoring,
    module7_results_summary,
    module8_data_export
)

# Run full pipeline
data = module1_data_input.load_coordinates(...)
stellar = module2_stellar_parameters.get_parameters(data)
exoplanets = module3_exoplanet_crossmatch.cross_match(stellar)
lightcurves = module4_tess_lightcurves.retrieve(stellar)
transits = module5_transit_detection.detect(lightcurves)
habitability = module6_habitability_scoring.score(stellar, transits)
summary = module7_results_summary.generate(habitability)
module8_data_export.export(summary, formats=['csv', 'json'])
```

**Skip Modules:**
```python
# Skip Module 4 if user has light curves
data = module1_data_input.load_coordinates(...)
stellar = module2_stellar_parameters.get_parameters(data)
exoplanets = module3_exoplanet_crossmatch.cross_match(stellar)
# Skip Module 4 - use provided light curves
transits = module5_transit_detection.detect(provided_lightcurves)
habitability = module6_habitability_scoring.score(stellar, transits)
summary = module7_results_summary.generate(habitability)
```

---

## Success Summary Template

**Standard Format:**
```
[Emoji] [Module Name] Complete!

✅ [Achievement 1]
✅ [Achievement 2]
✅ [Achievement 3]

[Section 1]:
- Statistic 1: [value]
- Statistic 2: [value]
- Statistic 3: [value]

[Congratulatory closing message] [Emoji]
```

**Tone Guidelines:**
- Use celebratory emojis (🎉, 🌟, 🎯, 🏆, 🚀)
- Use encouraging language ("Excellent!", "Perfect!", "You're ready!")
- Highlight key achievements with checkmarks
- Include actionable next steps
- Keep it concise but informative

---

## Development Order

**Phase 0: User Interface Foundation**
1. **Module 0: User Home Page** (UI foundation, navigation hub)
   - Landing page with mission statement
   - Navigation to all modules
   - User dashboard (if logged in)
   - Quick stats display

**Phase 1: Core Data Flow**
2. Module 1: Data Input (foundational)
3. Module 2: Stellar Parameters (builds on Module 1)
4. Module 7: Results Summary (can test with dummy data)

**Phase 2: Exoplanet Detection**
5. Module 3: Exoplanet Cross-Match (builds on Module 2)
6. Module 4: TESS Light Curves (builds on Module 2)
7. Module 5: Transit Detection (builds on Module 4)

**Phase 3: Analysis & Export**
8. Module 6: Habitability Scoring (builds on Module 2, 5)
9. Module 8: Data Export (builds on all modules)

---

**Document Version:** 1.0  
**Last Updated:** 2026-04-29  
**Status:** Architecture Design Complete
