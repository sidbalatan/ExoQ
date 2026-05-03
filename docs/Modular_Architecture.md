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
│  (Home Page) │   │  (Data Input)│   │  (Exoplanet) │
│  Page        │   │              │   │  Quest)      │
└──────────────┘   └──────────────┘   └──────────────┘
                            │
                            ▼
                  ┌──────────────┐
                  │  Module 3    │
                  │  TESS Light  │
                  │  Curves      │
                  └──────────────┘
                            │
                            ▼
                  ┌──────────────┐
                  │  Module 4    │
                  │  Transit     │
                  │  Detection   │
                  └──────────────┘
                            │
                            ▼
                  ┌──────────────┐
                  │  Module 5    │
                  │  Habitability│
                  │  Scoring     │
                  └──────────────┘
                            │
                            ▼
                  ┌──────────────┐
                  │  Module 6    │
                  │  Results     │
                  │  Summary     │
                  └──────────────┘
                            │
                            ▼
                  ┌──────────────┐
                  │  Module 7    │
                  │  Data        │
                  │  Export      │
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
- Module 1: Data Input and Gaia Survival Test
- Module 2: Start Exoplanet Quest
- Module 3: TESS Light Curves
- Module 4: Transit Detection
- Module 5: Habitability Scoring
- Module 6: Results Summary
- Module 7: Data Export
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

## Module 1: Data Input and Gaia Survival Test Module

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

## Module 2: Start Exoplanet Quest Module

**Purpose:** Cross-match stars with NASA Exoplanet Archive to identify known exoplanet hosts and virgin discovery targets

**Inputs:**
- DataFrame with stellar parameters (from Module 1)
- Optional: Search radius for cross-match (arcseconds)

**Outputs:**
- DataFrame with exoplanet cross-match results
- Cross-match statistics (hosts, virgin stars, separation)

**Key Features:**
- Spatial query against NASA Exoplanet Archive
- Identification of known exoplanet hosts
- Flagging of virgin stars for new discovery
- Separation distance calculation

**Success Summary (Congratulatory Tone):**
```
🪐 Module 2: Start Exoplanet Quest | 2 of 7 Complete!

✅ Cross-matched N stars with NASA Exoplanet Archive
✅ Found M stars with known exoplanets
✅ V stars are untouched (perfect for new discovery!)

Cross-Match Summary:
- Stars with exoplanets: M (X%)
- Virgin stars: V (Y%)
- Average separation: Z arcsec
- Pass rate: 100% (all N stars processed)

🎯 N stars moving to Module 3: TESS Light Curves
You have both vetting candidates and discovery targets! 🎉
```

**File Structure:**
```
src/modules/
├── module2_exoplanet_crossmatch.py
└── tests/
    └── test_module2_exoplanet_crossmatch.py
```

---

## Module 3: TESS Light Curve Module

**Purpose:** Download TESS light curves for target stars from MAST API

**Inputs:**
- DataFrame with stellar coordinates (from Module 2)
- Optional: Sector selection, data quality filters

**Outputs:**
- DataFrame with light curve metadata
- Downloaded light curve files
- Quality assessment metrics

**Key Features:**
- MAST API query for TESS observations
- Light curve product filtering
- Sector coverage analysis
- Data quality assessment

**Success Summary (Congratulatory Tone):**
```
📈 Module 3: TESS Light Curves | 3 of 7 Complete!

✅ Successfully downloaded N light curves from TESS
✅ Total observation time: X days
✅ Data quality: Excellent (low noise, good coverage)

Light Curve Summary:
- Sectors covered: X
- Average cadence: Y minutes
- Data points per star: Z
- Pass rate: P% (N/M stars with TESS data)

🎯 N stars moving to Module 4: Transit Detection
You're ready to hunt for transits! 🔭
```

**File Structure:**
```
src/modules/
├── module3_tess_lightcurves.py
└── tests/
    └── test_module3_tess_lightcurves.py
```

---

## Module 4: Transit Detection Module

**Purpose:** Detect transit signals in TESS light curves using BLS periodogram

**Inputs:**
- DataFrame with light curve data (from Module 3)
- Optional: Period range, transit duration range

**Outputs:**
- DataFrame with transit candidates
- Detection statistics (candidates, S/N, periods)
- Periodogram plots

**Key Features:**
- Box Least Squares (BLS) periodogram
- Signal-to-noise ratio calculation
- False alarm probability (FAP) assessment
- Period and duration estimation

**Success Summary (Congratulatory Tone):**
```
🎯 Module 4: Transit Detection | 4 of 7 Complete!

✅ Analyzed N light curves
✅ Detected M transit candidates
✅ K candidates passed quality thresholds

Detection Summary:
- Best candidate: TIC XXX (S/N = Y)
- Average period: Z days
- Average depth: W%
- Pass rate: P% (K/N candidates passed)

🎯 K transit candidates moving to Module 5: Habitability Scoring
Exciting potential discoveries! �
```

**File Structure:**
```
src/modules/
├── module4_transit_detection.py
└── tests/
    └── test_module4_transit_detection.py
```

---

## Module 5: Habitability Scoring Module

**Purpose:** Score stellar and exoplanet habitability using multiple metrics

**Inputs:**
- DataFrame with transit candidates (from Module 4)
- Stellar parameters from Module 1

**Outputs:**
- DataFrame with habitability scores
- Earth Similarity Index (ESI)
- Habitable zone analysis
**Key Features:**
- Stellar habitability scoring
- Earth Similarity Index (ESI) calculation
- Habitable zone assessment
- Multi-metric ranking

**Success Summary (Congratulatory Tone):**
```
💧 Module 5: Habitability Scoring | 5 of 7 Complete!

✅ Scored N stars for habitability
✅ M stars are highly habitable (score > 0.8)
✅ K exoplanet candidates in habitable zone

Habitability Summary:
- Best host star: TIC XXX (score = Y)
- Most Earth-like planet: ESI = Z
- Habitable zone candidates: K
- Pass rate: P% (M/N stars highly habitable)

🎯 N stars moving to Module 6: Results Summary
Your discoveries are ready for the final report! 📊
```

**File Structure:**
```
src/modules/
├── module5_habitability_scoring.py
└── tests/
    └── test_module5_habitability_scoring.py
```

---

## Module 6: Results Summary Module

**Purpose:** Generate comprehensive summary of all discoveries and findings

**Inputs:**
- DataFrame with all processed data from previous modules

**Outputs:**
- Summary report with key statistics
- Top discoveries list
- Visualizations and plots

**Key Features:**
- Discovery ranking
- Statistical analysis
- Visualization generation
- Report compilation

**Success Summary (Congratulatory Tone):**
```
📊 Module 6: Results Summary | 6 of 7 Complete!

✅ Generated comprehensive summary of all discoveries
✅ Found N potential exoplanet candidates
✅ M high-confidence detections

Results Summary:
- Top discovery: TIC XXX
- Average ESI: Y
- Stars with habitable planets: Z
- Total data processed: W stars

🎯 All results moving to Module 7: Data Export
Ready to share your discoveries with the world! 🌍
```

**File Structure:**
```
src/modules/
├── module6_results_summary.py
└── tests/
    └── test_module6_results_summary.py
```

---

## Module 7: Data Export Module

**Purpose:** Export processed data in multiple formats for sharing and analysis

**Inputs:**
- DataFrame with final results from all modules
- Export format preferences (CSV, JSON, FITS)

**Outputs:**
- Exported data files
- Export report with metadata
- Downloadable files

**Key Features:**
- Multiple format support (CSV, JSON, FITS)
- Metadata preservation
- Batch export capabilities
- File compression options

**Success Summary (Congratulatory Tone):**
```
📤 Module 7: Data Export | 7 of 7 Complete!

✅ Successfully exported data in N format(s)
✅ M rows exported
✅ K columns included

Export Summary:
- Formats: CSV, JSON
- File size: X MB
- Export time: Y seconds

🎉 Pipeline Complete! All 7 modules finished successfully.
Your data is ready for analysis and sharing! 🌍
```

**File Structure:**
```
src/modules/
├── module7_data_export.py
└── tests/
    └── test_module7_data_export.py
```

---

## File Structure Overview

```
ExoQ/
├── src/
│   ├── modules/
│   │   ├── module1_data_input.py
│   │   ├── module2_exoplanet_crossmatch.py
│   │   ├── module3_tess_lightcurves.py
│   │   ├── module4_transit_detection.py
│   │   ├── module5_habitability_scoring.py
│   │   ├── module6_results_summary.py
│   │   └── module7_data_export.py
│   └── tests/
│       └── test_*.py
├── streamlit_app/
│   ├── Home.py (Module 0)
│   └── pages/
│       ├── 2_My_Workspace.py
│       └── 3_Community_Gallery.py
├── docs/
│   └── Modular_Architecture.md
└── notebooks/
    └── pipeline_tutorial.ipynb
```

---

## Development Priority

1. **Module 0: User Home Page** (UI foundation, navigation hub)
2. Module 1: Data Input and Gaia Survival Test (foundational)
3. Module 2: Start Exoplanet Quest (builds on Module 1)
4. Module 6: Results Summary (can test with dummy data)
5. Module 3: TESS Light Curves (builds on Module 2)
6. Module 4: Transit Detection (builds on Module 3)
7. Module 5: Habitability Scoring (builds on Module 2, 4)
8. Module 7: Data Export (builds on all modules)

---

## Module Dependencies**
- DataFrame with additional validation data
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
2. Module 1: Data Input and Gaia Survival Test (foundational)
3. Module 2: Additional Validation Filters (builds on Module 1)
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
