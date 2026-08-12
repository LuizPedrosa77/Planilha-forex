import re

with open('c:\\Users\\Gustavo\\Documents\\Git\\PlanilhaGerenciamentoForex\\Planilha_Gustavo_Pedrosa_FX.html', 'r', encoding='utf-8') as f:
    content = f.read()

funcs_to_patch = [
    'openCalendarPanel',
    'calcTopAccountKpis',
    'renderCalendar',
    'calBuildEquityCurve',
    'calRenderRecentTrades',
    'calRenderDaySummaryAndTrades',
    'openChartPanel',
    'updateChartData',
    'openHeatmapPanel',
    'renderHeatmapYear',
    'openAnalisesPanel',
    'renderAnalises'
]

for func in funcs_to_patch:
    # Match function funcName() { ... state.accounts[state.activeAccount];
    pattern = r'(function\s+' + func + r'\b.*?\{.*?)state\.accounts\[state\.activeAccount\]'
    content = re.sub(pattern, r'\1getActiveAnalysisAccount()', content, count=1, flags=re.DOTALL)

# There is a second reference in renderCalendar? Wait, let's see.
# In renderCalendar, does it reference state.accounts[state.activeAccount]? Let's check my grep output.
# {"File":"c:/Users/Gustavo/Documents/Git/PlanilhaGerenciamentoForex/Planilha_Gustavo_Pedrosa_FX.html","LineNumber":2149,"LineContent":"  var acc = state.accounts[state.activeAccount];"}
# Okay, one occurrence.

injection = """
<div id="globalAccountSelectorContainer" style="display:none;position:fixed;bottom:30px;right:30px;z-index:9999;background:#1e293b;padding:12px 18px;border-radius:12px;border:1px solid rgba(255,255,255,0.1);box-shadow:0 10px 25px rgba(0,0,0,0.5);align-items:center;gap:12px;">
  <span style="font-size:12px;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:0.5px;">🎯 Análise de:</span>
  <select id="globalAccountSelector" onchange="switchGlobalAccountMode(this.value)" style="background:#0f172a;border:1px solid rgba(255,255,255,0.1);color:#fff;padding:8px 12px;border-radius:8px;font-size:14px;font-weight:700;outline:none;cursor:pointer;"></select>
</div>

<script>
function getActiveAnalysisAccount() {
  if (state.globalAccountMode === 'all') {
    var allTrades = [];
    var initialBalance = 0;
    var allWithdrawals = {};
    var allDeposits = {};
    state.accounts.forEach(function(a) {
      if (a.trades) allTrades = allTrades.concat(a.trades);
      initialBalance += (a.balance || 0);
      if (a.withdrawals) {
        Object.keys(a.withdrawals).forEach(function(k) {
          allWithdrawals[k] = (allWithdrawals[k] || 0) + a.withdrawals[k];
        });
      }
      if (a.deposits) {
        Object.keys(a.deposits).forEach(function(k) {
          allDeposits[k] = (allDeposits[k] || 0) + a.deposits[k];
        });
      }
    });
    return {
      name: "Todas as contas conectadas",
      balance: initialBalance,
      trades: allTrades,
      withdrawals: allWithdrawals,
      deposits: allDeposits,
      meta: state.accounts[0] ? state.accounts[0].meta : 0
    };
  }
  var idx = state.globalAccountMode !== undefined ? state.globalAccountMode : state.activeAccount;
  if (!state.accounts[idx]) idx = state.activeAccount;
  return state.accounts[idx];
}

function switchGlobalAccountMode(mode) {
  state.globalAccountMode = mode;
  save();
  var accName = getActiveAnalysisAccount().name;
  if (document.getElementById('calendarPanel').style.display === 'flex') { document.getElementById('calAccName').textContent = accName; renderCalendar(); }
  else if (document.getElementById('chartPanel').style.display === 'flex') { document.getElementById('chartAccName').textContent = accName; updateChartData(); }
  else if (document.getElementById('heatmapPanel').style.display === 'flex') { document.getElementById('heatmapAccName').textContent = accName; renderHeatmapYear(); }
  else if (document.getElementById('analisesPanel').style.display === 'flex') { document.getElementById('analisesAccName').textContent = accName; renderAnalises(); }
  updateGlobalAccountSelector();
}

function updateGlobalAccountSelector() {
  var sel = document.getElementById('globalAccountSelector');
  if (!sel) return;
  var html = '<option value="all">🌐 Todas as contas conectadas</option>';
  state.accounts.forEach(function(a, i) {
    html += '<option value="' + i + '">👤 ' + escHtml(a.name) + '</option>';
  });
  sel.innerHTML = html;
  var mode = state.globalAccountMode !== undefined ? state.globalAccountMode : state.activeAccount;
  sel.value = mode;
}
</script>
</body>
"""

if "globalAccountSelector" not in content:
    content = content.replace('</body>', injection)

navgoto_code = """function navGoTo(view) {
  var globalSelector = document.getElementById('globalAccountSelectorContainer');
  if (['calendario', 'evolucao', 'analises', 'heatmap'].includes(view)) {
    if (globalSelector) {
       globalSelector.style.display = 'flex';
       updateGlobalAccountSelector();
    }
  } else {
    if (globalSelector) globalSelector.style.display = 'none';
  }
"""

if "updateGlobalAccountSelector();" not in content:
    content = content.replace('function navGoTo(view) {', navgoto_code)

with open('c:\\Users\\Gustavo\\Documents\\Git\\PlanilhaGerenciamentoForex\\Planilha_Gustavo_Pedrosa_FX.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated successfully")
