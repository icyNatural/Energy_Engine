cd E:\PROJECTS\energy_engine_v1

$path = ".\index.html"
$backup = ".\index_backup_before_desktop_ui_upgrade_$(Get-Date -Format 'yyyyMMdd_HHmmss').html"
Copy-Item $path $backup -Force

$content = Get-Content $path -Raw

$content = [regex]::Replace($content, '(?s)<style id="icy-desktop-os-upgrade">.*?</style>', '')
$content = [regex]::Replace($content, '(?s)<script id="icy-desktop-os-upgrade-script">.*?</script>', '')

$css = @'
<style id="icy-desktop-os-upgrade">
@media (min-width: 1000px) {
  body {
    padding: 0 !important;
    min-height: 100vh !important;
    background:
      radial-gradient(circle at 82% 0%, rgba(120,210,255,.22), transparent 32%),
      radial-gradient(circle at 18% 8%, rgba(185,240,255,.14), transparent 28%),
      linear-gradient(135deg, #04101c 0%, #082237 45%, #0b2c43 100%) !important;
  }

  .desktop-shell {
    display: block !important;
  }

  .desktop-sidebar {
    position: fixed;
    left: 0;
    top: 0;
    bottom: 0;
    width: 250px;
    padding: 34px 30px;
    background: linear-gradient(180deg, rgba(6,20,34,.78), rgba(3,12,24,.88));
    border-right: 1px solid rgba(210,245,255,.14);
    z-index: 20;
  }

  .desktop-brand {
    display: flex;
    align-items: center;
    gap: 14px;
    font-size: 25px;
    font-weight: 950;
    letter-spacing: -0.04em;
    margin-bottom: 58px;
  }

  .desktop-logo {
    width: 46px;
    height: 46px;
    display: grid;
    place-items: center;
    border-radius: 14px;
    background: linear-gradient(135deg, rgba(180,235,255,.28), rgba(80,180,230,.12));
    box-shadow: 0 0 24px rgba(155,231,255,.18);
  }

  .desktop-side-nav {
    display: grid;
    gap: 14px;
  }

  .desktop-side-nav button {
    height: 64px;
    border: 1px solid transparent;
    border-radius: 0 18px 18px 0;
    background: transparent;
    color: rgba(235,250,255,.72);
    font-size: 17px;
    font-weight: 850;
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 0 20px;
    cursor: pointer;
  }

  .desktop-side-nav button.active {
    background: rgba(145,220,255,.16);
    color: white;
    border-color: rgba(190,240,255,.12);
    box-shadow: inset 3px 0 0 #9be7ff;
  }

  .desktop-top-status {
    position: fixed;
    top: 34px;
    right: 44px;
    z-index: 30;
    display: flex;
    align-items: center;
    gap: 18px;
  }

  .desktop-pill {
    padding: 12px 18px;
    border-radius: 999px;
    border: 1px solid rgba(220,250,255,.13);
    background: rgba(255,255,255,.045);
    color: rgba(235,250,255,.72);
    font-weight: 800;
    font-size: 13px;
  }

  .desktop-pill::before {
    content: "";
    display: inline-block;
    width: 10px;
    height: 10px;
    margin-right: 10px;
    border-radius: 50%;
    background: #41d27d;
    box-shadow: 0 0 12px rgba(65,210,125,.55);
  }

  .desktop-avatar {
    width: 48px;
    height: 48px;
    border-radius: 50%;
    display: grid;
    place-items: center;
    background: linear-gradient(135deg, #b071ff, #ff6f91);
    box-shadow: 0 0 22px rgba(180,120,255,.25);
  }

  .wrap {
    max-width: none !important;
    margin: 0 44px 0 320px !important;
    padding: 86px 0 44px !important;
  }

  .app-title {
    font-size: 0 !important;
    height: 0 !important;
    margin: 0 !important;
    overflow: hidden !important;
  }

  .app-sub {
    font-size: 15px !important;
    margin: 0 0 26px !important;
    color: rgba(220,240,255,.68) !important;
  }

  .nav {
    margin-bottom: 28px !important;
    gap: 18px !important;
  }

  .nav-btn {
    min-width: 132px !important;
    height: 56px !important;
    border-radius: 18px !important;
    border: 1px solid rgba(210,245,255,.14) !important;
    background: rgba(255,255,255,.045) !important;
  }

  .nav-btn.active {
    background: linear-gradient(135deg, #eaffff, #9be7ff) !important;
    color: #031019 !important;
    box-shadow: 0 0 22px rgba(155,231,255,.32) !important;
  }

  #page-home:not(.hidden) {
    display: grid !important;
    grid-template-columns: minmax(0, 1fr) 420px !important;
    gap: 24px !important;
    align-items: start !important;
  }

  #page-home > .hero {
    grid-column: 1 / 2 !important;
    min-height: 360px !important;
    padding: 30px 34px !important;
  }

  #desktopGlance {
    grid-column: 2 / 3 !important;
    grid-row: 1 !important;
    display: block !important;
  }

  #page-home > .grid-2 {
    grid-column: 1 / -1 !important;
    display: grid !important;
    grid-template-columns: 1fr 1fr !important;
    gap: 24px !important;
  }

  .card {
    border-radius: 26px !important;
    border: 1px solid rgba(210,245,255,.14) !important;
    background:
      linear-gradient(180deg, rgba(255,255,255,.06), rgba(155,231,255,.035)),
      rgba(8, 26, 42, .62) !important;
  }

  .hero-actions {
    grid-template-columns: repeat(3, 1fr) !important;
  }

  .phase {
    font-size: 64px !important;
  }

  .emoji {
    font-size: 54px !important;
  }

  .energy-state {
    font-size: 30px !important;
  }

  .desktop-glance-item {
    display: flex;
    align-items: center;
    gap: 18px;
    padding: 18px;
    border-radius: 18px;
    background: rgba(255,255,255,.045);
    border: 1px solid rgba(210,245,255,.10);
    margin-top: 14px;
  }

  .desktop-glance-icon {
    width: 48px;
    height: 48px;
    border-radius: 50%;
    display: grid;
    place-items: center;
    background: rgba(155,231,255,.20);
    font-size: 24px;
  }

  .desktop-glance-label {
    color: rgba(220,240,255,.66);
    font-size: 13px;
    font-weight: 800;
  }

  .desktop-glance-value {
    font-size: 22px;
    font-weight: 950;
    margin-top: 3px;
  }
}

@media (max-width: 999px) {
  .desktop-shell,
  #desktopGlance {
    display: none !important;
  }
}
</style>
'@

$js = @'
<script id="icy-desktop-os-upgrade-script">
(function () {
  function showDesktopPage(page) {
    if (typeof switchPage === "function") switchPage(page);

    document.querySelectorAll(".desktop-side-nav button").forEach(btn => {
      btn.classList.toggle("active", btn.dataset.page === page);
    });
  }

  function ensureDesktopShell() {
    if (document.getElementById("desktopShell")) return;

    const shell = document.createElement("div");
    shell.id = "desktopShell";
    shell.className = "desktop-shell";
    shell.innerHTML = `
      <aside class="desktop-sidebar">
        <div class="desktop-brand">
          <div class="desktop-logo">❄️</div>
          <div>Icy Natural OS</div>
        </div>

        <div class="desktop-side-nav">
          <button data-page="home">⌂ Home</button>
          <button data-page="energy">⚡ Energy</button>
          <button data-page="interpreter">🧠 Interpreter</button>
          <button data-page="patterns">📊 Patterns</button>
          <button data-page="settings">⚙ Settings</button>
        </div>
      </aside>

      <div class="desktop-top-status">
        <div class="desktop-pill">All Systems Normal</div>
        <div class="desktop-avatar">👤</div>
      </div>
    `;

    document.body.prepend(shell);

    shell.querySelectorAll(".desktop-side-nav button").forEach(btn => {
      btn.addEventListener("click", () => showDesktopPage(btn.dataset.page));
    });
  }

  function ensureGlance() {
    const home = document.getElementById("page-home");
    if (!home || document.getElementById("desktopGlance")) return;

    const card = document.createElement("div");
    card.id = "desktopGlance";
    card.className = "card";
    card.innerHTML = `
      <div class="section-title">Today at a glance</div>

      <div class="desktop-glance-item">
        <div class="desktop-glance-icon">◷</div>
        <div>
          <div class="desktop-glance-label">Wake Window</div>
          <div class="desktop-glance-value" id="desktopWakeGlance">--:--</div>
        </div>
      </div>

      <div class="desktop-glance-item">
        <div class="desktop-glance-icon">💤</div>
        <div>
          <div class="desktop-glance-label">Nap Credit</div>
          <div class="desktop-glance-value" id="desktopNapGlance">0m</div>
        </div>
      </div>

      <div class="desktop-glance-item">
        <div class="desktop-glance-icon">⚡</div>
        <div>
          <div class="desktop-glance-label">Energy Trend</div>
          <div class="desktop-glance-value" id="desktopEnergyGlance">Low</div>
        </div>
      </div>

      <button class="btn btn-ghost" type="button" id="desktopViewEnergy" style="margin-top:18px;">View Full Energy →</button>
    `;

    const hero = home.querySelector(".hero");
    if (hero) hero.insertAdjacentElement("afterend", card);

    const energyBtn = document.getElementById("desktopViewEnergy");
    if (energyBtn) energyBtn.addEventListener("click", () => showDesktopPage("energy"));
  }

  function syncDesktopShell() {
    ensureDesktopShell();
    ensureGlance();

    const state = typeof loadState === "function" ? loadState() : {};
    const activePage = state.page || "home";

    document.querySelectorAll(".desktop-side-nav button").forEach(btn => {
      btn.classList.toggle("active", btn.dataset.page === activePage);
    });

    const wake = document.getElementById("wakeValue")?.textContent || "--:--";
    const nap = document.getElementById("napCreditValue")?.textContent || "0m";
    const energy = document.getElementById("energyState")?.textContent || "Low";

    const wakeEl = document.getElementById("desktopWakeGlance");
    const napEl = document.getElementById("desktopNapGlance");
    const energyEl = document.getElementById("desktopEnergyGlance");

    if (wakeEl) wakeEl.textContent = wake;
    if (napEl) napEl.textContent = nap;
    if (energyEl) energyEl.textContent = energy;
  }

  const oldRenderDesktopOS = window.render;
  window.render = function () {
    if (typeof oldRenderDesktopOS === "function") oldRenderDesktopOS();
    syncDesktopShell();
  };

  document.addEventListener("DOMContentLoaded", syncDesktopShell);
})();
</script>
'@

$content = $content -replace '</head>', "$css`n</head>"
$content = $content -replace '</body>', "$js`n</body>"

Set-Content $path $content -Encoding UTF8