# ExoQ: Community Quest for Earth 2.0

**Project Name:** ExoQ  
**Tagline:** Community Quest for Earth 2.0  
**Domain:** exox.earth (purchased)  
**Mission:** Community-driven search for habitable exoplanets around K Dwarf stars

---

## Core Concept

**Vision:** Empower thousands of citizen astronomers to search for habitable exoplanets around K Dwarf stars, accelerating humanity's quest for Earth 2.0.

**Why K Dwarfs?**
- Long-lived (15-30 billion years) — stable for life evolution
- Lower luminosity — habitable zone closer, easier to detect transits
- Numerous — ~75% of nearby stars are M/K dwarfs
- Lower stellar activity than M dwarfs — less harmful radiation

---

## User Journey Design

### Stage 1: Landing & Commitment

**User Mindset:** "I believe in the idea of community-driven Earth 2.0 search to save our species. What should I do next?"

**Landing Page Elements:**
```
┌─────────────────────────────────────────────────────────────┐
│  ExoQ - Community Quest for Earth 2.0                       │
│                                                             │
│  [1-Minute Video: What is ExoQ?]                           │
│  ▶ Play                                                     │
│                                                             │
│  Our Mission                                               │
│  Join thousands of citizen astronomers in humanity's       │
│  greatest quest: finding a second home for our species.    │
│                                                             │
│  [Start Searching]  [Learn More]                           │
└─────────────────────────────────────────────────────────────┘
```

### Stage 2: Coordinate Selection

**Two Starting Lists:**

#### List A: Vetted K Dwarfs (Exoplanet Vetting Pipeline)
- Purpose: Validate known exoplanet candidates
- Source: NASA Exoplanet Archive candidates
- Selection: Pre-validated K Dwarf stars with transit candidates
- Limit: 12 coordinates per pipeline feed

#### List B: Virgin Coordinates (K Dwarf Search Pipeline)
- Purpose: Discover new exoplanets from scratch
- Source: Gaia DR3 K Dwarf catalog
- Selection: Untouched K Dwarfs with no known exoplanets
- Limit: 12 coordinates per pipeline feed

---

## Key Features

### 1. Pipeline ExoQ
- Automated scientific pipeline (peer-review ready)
- Gaia DR3, NASA Exoplanet Archive, TESS integration
- Habitability scoring for candidates

### 2. ExoX Hunter Game
- Gamified light curve classification
- Train ML models while playing
- Leaderboards and achievements
- Mobile-friendly for commutes

### 3. Personal Workspace
- Save coordinates, results, FITS images, light curves
- Build your scientific portfolio
- Storage-based premium tiers

### 4. Community Gallery
- Share discoveries with social features
- Comments, likes, threaded replies
- Easy sharing to social media

### 5. Personal Dashboard
- Summary statistics and progress
- Visual gallery of discoveries
- Quick actions for continued engagement

---

## Technical Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    ExoQ Architecture                         │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│  Streamlit   │   │  PostgreSQL  │   │   Cloud      │
│  Frontend    │   │  Database    │   │   Storage    │
│  (Web App)   │   │  (Users,     │   │   (FITS,     │
│              │   │   Data)      │   │   Plots)     │
└──────────────┘   └──────────────┘   └──────────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
                            ▼
                  ┌──────────────┐
                  │  Pipeline    │
                  │  ExoQ        │
                  │  (Python)    │
                  └──────────────┘
```

---

## Pricing Model

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

---

## Non-Profit Structure

**501(c)(3) Benefits:**
- Tax-deductible donations
- Grant eligibility (NASA, NSF, private foundations)
- Institutional partnerships
- Educational program funding

---

## Implementation Roadmap

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

---

**Document Version:** 1.0  
**Last Updated:** 2026-04-29  
**Status:** Concept Complete
