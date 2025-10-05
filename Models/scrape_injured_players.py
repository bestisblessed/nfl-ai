from playwright.sync_api import sync_playwright
import pandas as pd

p = sync_playwright().start()
browser = p.chromium.launch(headless=True)
page = browser.new_page()
page.goto("https://www.espn.com/nfl/injuries", wait_until="domcontentloaded")
page.wait_for_timeout(2500)
res = page.evaluate(
    """
    () => {
      const keepStatus = (s) => {
        if (!s) return false;
        const t = s.trim().toLowerCase();
        return t === 'out' || t === 'injured reserve' || t.includes('injured reserve') || t === 'reserve/injured' || t.includes('reserve/injured') || t === 'ir' || t === 'doubtful';
      };
      const included = [];
      const excluded = [];
      const tables = Array.from(document.querySelectorAll('table'));
      for (const table of tables) {
        const headers = Array.from(table.querySelectorAll('thead th')).map(th => (th.textContent||'').trim().toLowerCase());
        if (headers.length === 0) continue;
        const statusIdx = headers.indexOf('status');
        if (statusIdx === -1) continue;
        const rows = Array.from(table.querySelectorAll('tbody tr'));
        for (const row of rows) {
          const tds = Array.from(row.querySelectorAll('td'));
          if (tds.length === 0) continue;
          const statusText = (tds[statusIdx]?.textContent || '').trim();
          const a = row.querySelector('a[href*="/nfl/player/_/id/"]');
          const name = (a?.textContent || '').trim();
          if (!name) continue;
          if (keepStatus(statusText)) included.push(name); else excluded.push(name);
        }
      }
      return { included: Array.from(new Set(included)), excluded: Array.from(new Set(excluded)) };
    }
    """
)
browser.close()
p.stop()

pd.DataFrame({"full_name": res["included"]}).to_csv("/Users/td/Code/nfl-ai/Models/injured_players.csv", index=False)
pd.DataFrame({"full_name": res["excluded"]}).to_csv("/Users/td/Code/nfl-ai/Models/questionable_players.csv", index=False)
print("Wrote", len(res["included"]), "players to /Users/td/Code/nfl-ai/Models/injured_players.csv")
print("Wrote", len(res["excluded"]), "players to /Users/td/Code/nfl-ai/Models/questionable_players.csv")


