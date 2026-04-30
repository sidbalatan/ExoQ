# ExoQ - ML-Assisted Exoplanet Detection Game

**Module Name:** ExoQ Hunter  
**Purpose:** Gamified light curve classification to train ML models  
**Target Use Case:** Commutes, work breaks, casual engagement  
**Status:** Design Phase

---

## Game Concept

**Name:** ExoQ Hunter - Train AI, Find Planets

**Core Loop:**
1. User is shown a light curve (TESS data)
2. User identifies if there's a transit dip (yes/no/maybe)
3. User marks the dip location (if yes)
4. User earns points for correct classifications
5. User classifications train the ML model
6. Leaderboard shows top discoverers

**Value Proposition:**
- **For Users:** Fun, quick game during breaks; contribute to science; compete on leaderboards
- **For Platform:** Free ML training data; improved automated detection; increased engagement
- **For Science:** Better exoplanet detection algorithms; human-AI collaboration

---

## Game Mechanics

### Round Structure

**Single Round (30-60 seconds):**
```
┌─────────────────────────────────────────────────────────────┐
│  ExoQ Hunter - Round 12/20                                  │
│  Score: 1,250  Streak: 5 🔥                                │
│                                                             │
│  [Light Curve Plot - Interactive]                          │
│  (Time on X-axis, Flux on Y-axis)                          │
│                                                             │
│  Is there a transit dip?                                    │
│  [Yes]  [No]  [Maybe]                                      │
│                                                             │
│  (If Yes selected)                                         │
│  Tap to mark the dip location:                              │
│  [Interactive marker on plot]                               │
│                                                             │
│  [Submit]  [Skip]                                          │
└─────────────────────────────────────────────────────────────┘
```

**Session Structure (5-10 minutes):**
- 20 rounds per session
- Progressive difficulty (easier → harder)
- Bonus rounds for streaks
- Session summary at end

### Classification Options

**Three Choices:**
1. **Yes** - Clear transit dip visible
2. **No** - No transit dip visible
3. **Maybe** - Uncertain, needs expert review

**Scoring:**
- **Correct "Yes":** +100 points
- **Correct "No":** +50 points
- **Correct "Maybe":** +75 points
- **Incorrect:** -25 points
- **Streak bonus:** +10 points per consecutive correct (max +50)
- **Speed bonus:** +5 points for fast classification (<5 seconds)

### Difficulty Levels

**Level 1 (Easy):**
- Clear, deep transits (>5% depth)
- Low noise light curves
- Known confirmed exoplanets (ground truth available)

**Level 2 (Medium):**
- Moderate transits (1-5% depth)
- Some noise
- Mix of confirmed and candidates

**Level 3 (Hard):**
- Shallow transits (<1% depth)
- High noise
- Edge cases, false positives

**Level 4 (Expert):**
- Very shallow transits (<0.5% depth)
- High noise with stellar variability
- Ambiguous cases

**Progression:**
- Start at Level 1
- Advance after 10 correct classifications
- Drop level after 3 incorrect classifications
- Users can choose difficulty level

---

## ML Training Data Collection

### Data Schema

**User Classifications Table:**
```sql
user_classifications (
    classification_id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(user_id),
    light_curve_id UUID REFERENCES light_curves(light_curve_id),
    classification VARCHAR(20), -- 'yes', 'no', 'maybe'
    dip_location DOUBLE PRECISION, -- time of marked dip
    confidence_score DOUBLE PRECISION, -- user's confidence (1-5)
    time_taken_seconds INTEGER,
    timestamp TIMESTAMP DEFAULT NOW(),
    is_correct BOOLEAN, -- compared to ground truth
    ml_prediction VARCHAR(20), -- what ML predicted
    ml_confidence DOUBLE PRECISION -- ML confidence
)
```

**Light Curves Table:**
```sql
light_curves (
    light_curve_id UUID PRIMARY KEY,
    source_id VARCHAR(50), -- TIC ID
    ra DOUBLE PRECISION,
    dec DOUBLE PRECISION,
    sector INTEGER,
    data_url VARCHAR(255),
    has_transit BOOLEAN, -- ground truth
    transit_depth DOUBLE PRECISION,
    transit_period DOUBLE PRECISION,
    transit_epoch DOUBLE PRECISION,
    difficulty_level INTEGER, -- 1-4
    classification_count INTEGER DEFAULT 0,
    consensus_classification VARCHAR(20), -- majority vote
    consensus_confidence DOUBLE PRECISION
)
```

### ML Training Pipeline

**Data Collection:**
1. User classifications are stored with metadata
2. Each light curve needs minimum 5 classifications
3. Consensus classification calculated (majority vote)
4. Disagreements flagged for expert review

**Training Dataset:**
- **Positive examples:** Light curves with confirmed transits + user "yes" classifications
- **Negative examples:** Light curves without transits + user "no" classifications
- **Ambiguous examples:** Light curves with user "maybe" classifications
- **Hard examples:** Light curves with high disagreement among users

**ML Model Types:**
1. **Binary classifier** (transit vs no transit)
2. **Transit detector** (identify dip location)
3. **Confidence estimator** (how certain is the detection)
4. **Difficulty classifier** (how hard is this light curve)

**Active Learning Loop:**
1. ML model makes predictions on new light curves
2. Uncertain predictions (low confidence) sent to users for classification
3. User classifications added to training data
4. Model retrained with new data
5. Repeat

---

## Leaderboard System

### Leaderboard Types

**1. Daily Leaderboard**
- Top 10 users by points earned today
- Resets daily
- Encourages daily engagement

**2. Weekly Leaderboard**
- Top 50 users by points earned this week
- Resets weekly
- Weekly badges for top performers

**3. All-Time Leaderboard**
- Top 100 users by total points
- Permanent record
- Hall of fame

**4. Discovery Leaderboard**
- Users who contributed to confirmed exoplanet discoveries
- Most prestigious
- Based on actual scientific impact

**5. Streak Leaderboard**
- Longest consecutive correct classifications
- Encourages accuracy over speed

### Scoring Metrics

**Points:**
- Total points earned
- Points per classification (accuracy metric)
- Points per hour (efficiency metric)

**Classifications:**
- Total classifications
- Correct classifications
- Accuracy percentage
- "Yes" classifications (discoveries)

**Impact:**
- Light curves contributed to ML training
- Consensus contributions (when user vote matches majority)
- Expert reviews triggered (user identified edge cases)
- Confirmed exoplanet contributions

### Badges and Achievements

**Classification Badges:**
- 🌟 **Novice Hunter** - 100 classifications
- ⭐ **Skilled Hunter** - 1,000 classifications
- 💫 **Expert Hunter** - 10,000 classifications
- 🏆 **Master Hunter** - 100,000 classifications

**Accuracy Badges:**
- 🎯 **Sharp Eye** - 90% accuracy over 100 classifications
- 🔭 **Eagle Eye** - 95% accuracy over 1,000 classifications
- 👁️ **Hawk Eye** - 98% accuracy over 10,000 classifications

**Discovery Badges:**
- 🪐 **First Discovery** - First "yes" classification on confirmed exoplanet
- 🌍 **Earth Hunter** - 10 Earth-sized planet classifications
- 🔥 **Hot Jupiter Hunter** - 10 hot Jupiter classifications
- 💧 **Habitable Zone Hunter** - 5 habitable zone classifications

**Streak Badges:**
- 🔥 **On Fire** - 10 consecutive correct
- ⚡ **Lightning** - 25 consecutive correct
- 🌪️ **Tornado** - 50 consecutive correct
- 💎 **Diamond** - 100 consecutive correct

**Contribution Badges:**
- 🤖 **ML Trainer** - 1,000 classifications used for ML training
- 🧠 **AI Teacher** - 10,000 classifications used for ML training
- 📊 **Data Contributor** - 100 light curves with consensus achieved
- 🔬 **Expert Reviewer** - 50 edge cases identified for expert review

---

## Gamification Strategy

### Engagement Hooks

**1. Quick Sessions**
- 5-minute sessions for commutes
- 10-minute sessions for breaks
- Progress saved automatically
- Resume anytime

**2. Instant Feedback**
- Immediate score after each classification
- Correct/incorrect notification
- Comparison to ML prediction
- Streak counter

**3. Progressive Difficulty**
- Start easy, get harder
- Sense of progression
- Unlock new levels
- Challenge yourself

**4. Social Competition**
- Leaderboards
- Friend comparisons
- Team challenges
- Weekly tournaments

**5. Scientific Impact**
- See your contribution count
- Track ML model improvements
- Discovery notifications
- Research paper acknowledgments

### Retention Mechanics

**Daily Goals:**
- Classify 20 light curves
- Maintain 80% accuracy
- Earn 1,000 points
- Reward: Daily bonus points

**Weekly Challenges:**
- Special themed challenges (e.g., "Habitable Zone Week")
- Bonus points for specific classifications
- Limited-time badges
- Community goals

**Seasonal Events:**
- "Exoplanet Discovery Month"
- Special datasets
- Double points weekends
- Exclusive badges

**Personal Bests:**
- Track personal records
- Beat your own high score
- Improvement metrics
- Progress visualization

### Monetization Integration

**Free Tier:**
- Unlimited game access
- Full leaderboard access
- All badges achievable
- Basic statistics

**Premium Tier:**
- Advanced statistics (detailed analytics)
- Personal ML model training (train on your classifications)
- Priority access to new light curves
- Exclusive badges
- Ad-free experience
- Download personal classification data

---

## Technical Implementation

### Frontend (Streamlit)

**Game Page Structure:**
```python
# pages/08_ExoQ_Hunter.py

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# Session state for game progress
if 'game_score' not in st.session_state:
    st.session_state.game_score = 0
if 'game_streak' not in st.session_state:
    st.session_state.game_streak = 0
if 'current_round' not in st.session_state:
    st.session_state.current_round = 1
if 'total_rounds' not in st.session_state:
    st.session_state.total_rounds = 20

# Load light curve data
light_curve = get_next_light_curve(user_id=st.session_state.user_id)

# Display light curve
fig = go.Figure()
fig.add_trace(go.Scatter(
    x=light_curve['time'],
    y=light_curve['flux'],
    mode='lines',
    name='Light Curve'
))
st.plotly_chart(fig, use_container_width=True)

# Classification buttons
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("Yes - Transit Detected", type="primary"):
        handle_classification("yes", light_curve)
with col2:
    if st.button("No - No Transit"):
        handle_classification("no", light_curve)
with col3:
    if st.button("Maybe - Uncertain"):
        handle_classification("maybe", light_curve)

# Progress display
st.progress(st.session_state.current_round / st.session_state.total_rounds)
st.write(f"Score: {st.session_state.game_score} | Streak: {st.session_state.game_streak} 🔥")
```

### Backend (Python)

**Light Curve Service:**
```python
# services/light_curve_service.py

class LightCurveService:
    def get_next_light_curve(self, user_id, difficulty=None):
        """Get next light curve for user to classify."""
        # Use active learning: prioritize uncertain ML predictions
        # Consider user's current difficulty level
        # Avoid recently shown light curves
        pass
    
    def submit_classification(self, user_id, light_curve_id, classification, 
                             dip_location=None, confidence=None):
        """Submit user classification."""
        # Store classification
        # Update consensus
        # Compare to ML prediction
        # Calculate score
        # Update leaderboard
        pass
    
    def get_leaderboard(self, timeframe='daily', limit=10):
        """Get leaderboard data."""
        pass
```

**ML Service:**
```python
# services/ml_service.py

class MLService:
    def predict_transit(self, light_curve):
        """ML prediction for transit detection."""
        pass
    
    def train_model(self, new_classifications):
        """Retrain model with new data."""
        pass
    
    def get_uncertain_predictions(self, n=100):
        """Get light curves with uncertain ML predictions."""
        pass
```

### Mobile Optimization

**Responsive Design:**
- Large touch targets for buttons
- Swipe gestures for navigation
- Portrait mode optimization
- Quick load times
- Offline mode (cache light curves)

**Mobile-Specific Features:**
- Haptic feedback on correct/incorrect
- One-handed play mode
- Quick-start button
- Background play (audio cues)

---

## Data Sources

### Initial Light Curve Dataset

**Sources:**
1. **TESS Mission** - Primary source via MAST API
2. **Kepler/K2** - Historical data for training
3. **Simulated Data** - Generate synthetic light curves for easy levels
4. **Planet Hunters** - Publicly available classified light curves

**Dataset Size:**
- Level 1 (Easy): 10,000 light curves
- Level 2 (Medium): 50,000 light curves
- Level 3 (Hard): 20,000 light curves
- Level 4 (Expert): 5,000 light curves
- Total: ~85,000 light curves initially

**Ground Truth:**
- Confirmed exoplanets from NASA Exoplanet Archive
- False positives from literature
- Simulated light curves with known parameters

---

## Scientific Impact

### ML Model Improvements

**Metrics to Track:**
- Classification accuracy over time
- False positive rate reduction
- False negative rate reduction
- Detection limit (shallowest detectable transit)
- Processing speed

**Validation:**
- Compare ML predictions to expert classifications
- Blind tests on new TESS data
- Peer-reviewed publication of ML model
- Open-source model release

### User Contributions

**Track:**
- Number of classifications per user
- Consensus contributions
- Edge case identifications
- Confirmed exoplanet contributions
- Research paper acknowledgments

**Recognition:**
- "Contributor" status on scientific papers
- Co-authorship for exceptional contributors
- Named discoveries (e.g., "ExoQ-1 b")
- Conference presentations

---

## Implementation Roadmap

### Phase 1: MVP Game (2 months)
- Basic light curve display
- Yes/No/Maybe classification
- Simple scoring
- Daily leaderboard
- Mobile-friendly UI

### Phase 2: ML Integration (2 months)
- ML model integration
- Active learning loop
- Consensus calculation
- Difficulty progression
- Classification storage

### Phase 3: Gamification (1 month)
- Badges and achievements
- Multiple leaderboards
- Streak system
- Social features
- Friend comparisons

### Phase 4: Advanced Features (2 months)
- Dip location marking
- Confidence scoring
- Expert review system
- Personal ML training (premium)
- Advanced analytics

### Phase 5: Scientific Validation (ongoing)
- ML model validation
- Scientific paper publication
- Open-source release
- Conference presentations

---

## Success Metrics

**User Engagement:**
- Daily active users
- Session duration
- Retention rate (day 1, day 7, day 30)
- Classifications per user per day

**ML Performance:**
- Classification accuracy improvement
- False positive rate reduction
- Detection limit improvement
- Model performance on blind tests

**Scientific Impact:**
- Confirmed exoplanet discoveries
- Research papers published
- Citations of ML model
- Community adoption

---

## Ethical Considerations

**Data Privacy:**
- User classifications anonymized for ML training
- Opt-out option for data usage
- Transparent data usage policy

**Scientific Integrity:**
- Ground truth validation
- Expert review of edge cases
- Peer review of ML methods
- Reproducible research

**Fair Play:**
- Anti-cheat measures
- Rate limiting
- Suspicious activity detection
- Account verification

---

**Document Version:** 1.0  
**Last Updated:** 2026-04-29  
**Status:** Design Complete
