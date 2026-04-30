# ExoQ: Community Quest for Earth 2.0

**ExoQ** is a community-driven platform for discovering habitable exoplanets around K Dwarf stars. Join thousands of citizen astronomers in humanity's greatest quest: finding a second home for our species.

## Mission

> **Find Earth 2.0 together**

Climate change and nuclear threats endanger our planet. ExoQ empowers the community to search for habitable worlds around K Dwarf stars — the most promising targets for Earth-like planets.

## Why K Dwarfs?

- **Long-lived** (15-30 billion years) — stable for life evolution
- **Lower luminosity** — habitable zone closer, easier to detect transits
- **Numerous** — ~75% of nearby stars are M/K dwarfs
- **Lower activity** — less harmful radiation than M dwarfs

## Features

### 🎯 Two-Path System
- **Vetted K Dwarfs** — Validate known exoplanet candidates (quick wins)
- **Virgin Coordinates** — Discover new exoplanets from scratch

### 🤖 Pipeline ExoQ
- Automated scientific pipeline (peer-review ready)
- Gaia DR3, NASA Exoplanet Archive, TESS integration
- Habitability scoring for candidates

### 🎮 ExoX Hunter Game
- Gamified light curve classification
- Train ML models while playing
- Leaderboards and achievements
- Mobile-friendly for commutes

### 💾 Personal Workspace
- Save coordinates, results, FITS images, light curves
- Build your scientific portfolio
- Storage-based premium tiers

### 🌐 Community Gallery
- Share discoveries with social features
- Comments, likes, threaded replies
- Easy sharing to social media

### 📊 Personal Dashboard
- Summary statistics and progress
- Visual gallery of discoveries
- Quick actions for continued engagement

## Technology Stack

- **Frontend:** Streamlit (mobile-first)
- **Backend:** Python (Pipeline ExoQ)
- **Database:** PostgreSQL (Supabase)
- **Storage:** Cloud storage (FITS, plots, data)
- **Deployment:** Streamlit Community Cloud

## Getting Started

### Prerequisites
- Python 3.14+
- pip

### Installation
```bash
git clone https://github.com/sidbalatan/ExoQ.git
cd ExoQ
pip install -r requirements.txt
```

### Run the App
```bash
streamlit run streamlit_app/Home.py
```

## Project Structure

```
ExoQ/
├── docs/                    # Documentation
├── streamlit_app/           # Streamlit application
│   ├── pages/              # App pages
│   └── Home.py             # Landing page
├── src/                     # Source code
│   ├── pipeline/           # Pipeline ExoQ
│   └── data/               # Data preparation
├── data/                    # Datasets
├── requirements.txt         # Dependencies
└── .devcontainer/          # GitHub Codespace config
```

## Roadmap

### Phase 1: MVP (2-3 months)
- User authentication
- Coordinate selection (vetted vs virgin)
- Pipeline ExoQ integration (vetting only)
- Basic results display
- Landing page with tutorial

### Phase 2: Core Platform (3-4 months)
- Discovery pipeline integration
- Full results saving
- Community gallery
- Comments system
- Personal dashboard

### Phase 3: Advanced Features (2-3 months)
- Threaded comments
- User profiles and following
- Advanced filtering
- Collaboration features
- ExoX Hunter game

### Phase 4: Operations (1-2 months)
- Storage-based pricing
- Payment integration
- Analytics
- Grant applications

## Pricing

**Free Tier**
- 1 GB storage
- 10 pipeline runs/day
- Full community features

**Premium Tier**
- 10 GB storage
- Unlimited pipeline runs
- Priority queue
- Email support
- $5/month or $50/year

## Non-Profit Status

ExoQ is structured as a non-profit to enable:
- Tax-deductible donations
- Grant eligibility (NASA, NSF, private foundations)
- Institutional partnerships
- Educational program funding

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

[MIT License](LICENSE)

## Contact

- GitHub: https://github.com/sidbalatan/ExoQ
- Email: balatasc7582@student.laccd.edu

## Acknowledgments

- Gaia Collaboration
- NASA Exoplanet Archive
- STScI/MAST
- TESS Mission Team
- Citizen science community

---

**ExoQ: Community Quest for Earth 2.0**
