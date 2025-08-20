# NFL AI

This repository collects game and player data from external sources and provides Jupyter notebooks for exploratory analysis.

## Contents

### Data Scrapers
- [ScraperFinal.py](Scrapers/ScraperFinal.py) – pulls raw game and player data into `nfl.db`
- [scrape.sh](Scrapers/scrape.sh) – helper script to run the scraper

### Core Analysis Notebooks
- [Setup & Data Preparation](Analysis/NFLAI-Setup-Data.ipynb)
- [Betting Trends](Analysis/NFLAI-Betting-Trends.ipynb)
- [Team Trends](Analysis/NFLAI-Team-Trends.ipynb)
- [Player Trends](Analysis/NFLAI-Player-Trends.ipynb)

### Additional Analyses
- [After-Loss Analysis](Analysis/After-Loss-Analysis.ipynb)
- [Coach Analysis](Analysis/Coach-Analysis.ipynb)
- [Defense Analysis](Analysis/Defense-Analysis.ipynb)
- [Home vs Away Team Analysis](Analysis/Home-Away-Team-Analysis.ipynb)
- [Scoring Analysis](Analysis/Scoring-Analysis.ipynb)
- [Travel Analysis](Analysis/Travel-Analysis.ipynb)

The notebook [Analysis/NFLAI-ANALYSIS.ipynb](Analysis/NFLAI-ANALYSIS.ipynb) provides a clickable table of contents linking to each section above.

## Contributing
Organize new analyses in separate notebooks and document them here so collaborators can discover them easily. Shared helper functions can live under `Analysis/scripts` to reduce duplication.
