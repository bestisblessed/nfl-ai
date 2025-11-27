# Documentation Index

**Welcome to the QB Interception Odds Analysis project!**

Choose the document that matches your needs:

---

## 🚀 I Want To Get Started

→ **[QUICK_START.md](QUICK_START.md)** (3.7 KB)
- 30-second start guide
- Common commands
- Quick troubleshooting
- **Best for:** Running the analysis right now

---

## 📖 I Want To Learn How It Works

→ **[README.md](README.md)** (4.5 KB)
- Project overview
- What it does
- Installation
- Basic usage examples
- **Best for:** First-time users

→ **[STEPS.md](STEPS.md)** (7.4 KB)
- Complete step-by-step guide
- Detailed execution instructions
- All command options
- Workflow examples
- **Best for:** Understanding the full process

---

## 🏗️ I Want To Understand The Code

→ **[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)** (8.3 KB)
- File organization
- Module dependencies
- Data flow diagrams
- Code metrics
- **Best for:** Developers and maintainers

---

## 🔄 I'm Migrating From Old Scripts

→ **[REFACTOR_SUMMARY.md](REFACTOR_SUMMARY.md)** (5.7 KB)
- What changed
- Before/after comparison
- New file locations
- Migration instructions
- **Best for:** Existing users updating

---

## 📊 I Want To Understand The Math

→ **[EV_VIG_KELLY.md](EV_VIG_KELLY.md)** (7.6 KB)
- Expected value theory
- VIG calculation methods
- Kelly criterion
- Mathematical foundations
- **Best for:** Understanding betting math

---

## 🎯 Quick Access by Task

### Running the System
1. **First time?** → [README.md](README.md)
2. **Quick run?** → [QUICK_START.md](QUICK_START.md) → `./run_all.sh`
3. **Need details?** → [STEPS.md](STEPS.md)

### Understanding the Code
1. **File layout?** → [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)
2. **What changed?** → [REFACTOR_SUMMARY.md](REFACTOR_SUMMARY.md)

### Learning the Concepts
1. **Betting math?** → [EV_VIG_KELLY.md](EV_VIG_KELLY.md)
2. **How it works?** → [README.md](README.md) → [STEPS.md](STEPS.md)

---

## 📁 File Reference

### Scripts (Run These)
```bash
./run_all.sh                          # ⭐ Master script
python 1_scrape_odds.py               # Scrape DraftKings
python 2_calculate_edges.py           # Find value bets
python train_qb_interceptions_model.py    # Train models
python predict_qb_interceptions.py    # Make predictions
```

### Modules (Import These)
```python
from utils.api import fetch_draftkings_interceptions
from utils.odds import american_to_probability, remove_vig
from utils.matching import build_player_mapping
from utils.parser import parse_interception_markets
from utils.io import write_odds_csv
```

### Configuration
```python
from config import ODDS_LATEST, PREDICTIONS_DIR, SCRAPE_CACHE_MINUTES
```

---

## 🆘 Help & Troubleshooting

### Common Issues

**"I don't know where to start"**
→ [QUICK_START.md](QUICK_START.md) → Run `./run_all.sh`

**"Script not working"**
→ [QUICK_START.md](QUICK_START.md) → Troubleshooting section

**"Need more detail on step X"**
→ [STEPS.md](STEPS.md) → Find your step

**"Want to modify the code"**
→ [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) → Module dependencies

**"Migrating from old version"**
→ [REFACTOR_SUMMARY.md](REFACTOR_SUMMARY.md)

**"Understanding edge calculations"**
→ [EV_VIG_KELLY.md](EV_VIG_KELLY.md)

---

## 📊 Documentation Stats

| Document | Size | Lines | Purpose |
|----------|------|-------|---------|
| QUICK_START.md | 3.7 KB | ~150 | Fast reference |
| README.md | 4.5 KB | ~180 | Overview |
| STEPS.md | 7.4 KB | ~250 | Detailed guide |
| PROJECT_STRUCTURE.md | 8.3 KB | ~300 | Architecture |
| REFACTOR_SUMMARY.md | 5.7 KB | ~200 | Changes log |
| EV_VIG_KELLY.md | 7.6 KB | ~280 | Math theory |
| **Total** | **37.2 KB** | **~1,360** | Complete docs |

---

## 🎓 Learning Path

### Beginner
1. [QUICK_START.md](QUICK_START.md) → Run `./run_all.sh`
2. [README.md](README.md) → Understand what it does
3. Review output in `predictions/betting_edges_latest.csv`

### Intermediate
1. [STEPS.md](STEPS.md) → Learn each step
2. Run individual scripts
3. [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) → Understand organization

### Advanced
1. [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) → Study architecture
2. [EV_VIG_KELLY.md](EV_VIG_KELLY.md) → Master the math
3. Modify `utils/` modules for custom features

---

## 🔗 External Resources

- **DraftKings API**: Used by `utils/api.py`
- **Player Data**: Configured in `config.py`
- **scikit-learn**: ML models in `train_qb_interceptions_model.py`

---

## ✅ Recommended Reading Order

**For New Users:**
1. This file (you are here!)
2. [QUICK_START.md](QUICK_START.md)
3. [README.md](README.md)
4. Run `./run_all.sh`
5. [STEPS.md](STEPS.md) for details

**For Developers:**
1. [README.md](README.md)
2. [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)
3. [REFACTOR_SUMMARY.md](REFACTOR_SUMMARY.md)
4. Explore `utils/` modules

**For Betting Analysts:**
1. [QUICK_START.md](QUICK_START.md)
2. [EV_VIG_KELLY.md](EV_VIG_KELLY.md)
3. [STEPS.md](STEPS.md)
4. Run analysis and review outputs

---

**Need help?** Start with [QUICK_START.md](QUICK_START.md) or [README.md](README.md)

**Version:** 2.0 (Modular Refactor)  
**Last Updated:** 2025-11-05
