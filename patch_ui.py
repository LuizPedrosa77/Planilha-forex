import os

file_path = r'c:\Users\Gustavo\Documents\Git\PlanilhaGerenciamentoForex\Planilha_Gustavo_Pedrosa_FX.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update Calendário Header
content = content.replace(
    '<span id="calAccName" style="font-size:12px;color:#94a3b8;background:rgba(255,255,255,0.07);padding:3px 12px;border-radius:20px;"></span>',
    '<select class="globalAccountSelector" onchange="switchGlobalAccountMode(this.value)" style="background:#0f172a;border:1px solid rgba(255,255,255,0.1);color:#fff;padding:6px 10px;border-radius:6px;font-size:13px;font-weight:600;outline:none;cursor:pointer;"></select>'
)

# 2. Update Evolução da Conta Header
content = content.replace(
    '<span id="chartAccName" style="font-size:12px;color:#94a3b8;background:rgba(255,255,255,0.07);padding:3px 12px;border-radius:20px;"></span>',
    '<select class="globalAccountSelector" onchange="switchGlobalAccountMode(this.value)" style="background:#0f172a;border:1px solid rgba(255,255,255,0.1);color:#fff;padding:6px 10px;border-radius:6px;font-size:13px;font-weight:600;outline:none;cursor:pointer;"></select>'
)

# 3. Update Análises Header
content = content.replace(
    '<span style="font-size:19px;font-weight:800;color:#fff;letter-spacing:-0.5px;">📊 Análises</span>',
    '<span style="font-size:19px;font-weight:800;color:#fff;letter-spacing:-0.5px;">📊 Análises</span>\n      <select class="globalAccountSelector" onchange="switchGlobalAccountMode(this.value)" style="background:#0f172a;border:1px solid rgba(255,255,255,0.1);color:#fff;padding:6px 10px;border-radius:6px;font-size:13px;font-weight:600;outline:none;cursor:pointer;"></select>'
)

# 4. Update Heatmap Anual Header
content = content.replace(
    '<span style="font-size:19px;font-weight:800;color:#fff;letter-spacing:-0.5px;">🔥 Heatmap Anual</span>',
    '<span style="font-size:19px;font-weight:800;color:#fff;letter-spacing:-0.5px;">🔥 Heatmap Anual</span>\n      <select class="globalAccountSelector" onchange="switchGlobalAccountMode(this.value)" style="background:#0f172a;border:1px solid rgba(255,255,255,0.1);color:#fff;padding:6px 10px;border-radius:6px;font-size:13px;font-weight:600;outline:none;cursor:pointer;"></select>'
)

# 5. Remove the floating div container
# It looks like: <div id="globalAccountSelectorContainer" ...> ... </div>
import re
content = re.sub(r'<div id="globalAccountSelectorContainer"[\s\S]*?</div>', '', content)

# 6. Remove the logic in navGoTo that shows/hides the floating container
navgoto_old = """function navGoTo(view) {
  var globalSelector = document.getElementById('globalAccountSelectorContainer');
  if (['calendario', 'evolucao', 'analises', 'heatmap'].includes(view)) {
    if (globalSelector) {
       globalSelector.style.display = 'flex';
       updateGlobalAccountSelector();
    }
  } else {
    if (globalSelector) globalSelector.style.display = 'none';
  }"""
navgoto_new = """function navGoTo(view) {
  if (['calendario', 'evolucao', 'analises', 'heatmap'].includes(view)) {
    updateGlobalAccountSelector();
  }"""
content = content.replace(navgoto_old, navgoto_new)

# 7. Update updateGlobalAccountSelector to use class instead of id
update_func_old = """function updateGlobalAccountSelector() {
  var sel = document.getElementById('globalAccountSelector');
  if (!sel) return;
  var html = '<option value="all">🌐 Todas as contas conectadas</option>';
  state.accounts.forEach(function(a, i) {
    html += '<option value="' + i + '">👤 ' + escHtml(a.name) + '</option>';
  });
  sel.innerHTML = html;
  var mode = state.globalAccountMode !== undefined ? state.globalAccountMode : state.activeAccount;
  sel.value = mode;
}"""
update_func_new = """function updateGlobalAccountSelector() {
  var sels = document.querySelectorAll('.globalAccountSelector');
  if (!sels.length) return;
  var html = '<option value="all">🌐 Todas as contas conectadas</option>';
  state.accounts.forEach(function(a, i) {
    html += '<option value="' + i + '">👤 ' + escHtml(a.name) + '</option>';
  });
  var mode = state.globalAccountMode !== undefined ? state.globalAccountMode : state.activeAccount;
  sels.forEach(function(sel) {
    sel.innerHTML = html;
    sel.value = mode;
  });
}"""
content = content.replace(update_func_old, update_func_new)

# 8. Clean up switchGlobalAccountMode and occurrences that set textContent
switch_old = """function switchGlobalAccountMode(mode) {
  state.globalAccountMode = mode;
  save();
  var accName = getActiveAnalysisAccount().name;
  if (document.getElementById('calendarPanel').style.display === 'flex') { document.getElementById('calAccName').textContent = accName; renderCalendar(); }
  else if (document.getElementById('chartPanel').style.display === 'flex') { document.getElementById('chartAccName').textContent = accName; updateChartData(); }
  else if (document.getElementById('heatmapPanel').style.display === 'flex') { document.getElementById('heatmapAccName').textContent = accName; renderHeatmap(); }
  else if (document.getElementById('analisesPanel').style.display === 'flex') { document.getElementById('analisesAccName').textContent = accName; renderAnalises(); }
  updateGlobalAccountSelector();
}"""
switch_new = """function switchGlobalAccountMode(mode) {
  state.globalAccountMode = mode;
  save();
  if (document.getElementById('calendarPanel').style.display === 'flex') { renderCalendar(); }
  else if (document.getElementById('chartPanel').style.display === 'flex') { updateChartData(); }
  else if (document.getElementById('heatmapPanel').style.display === 'flex') { renderHeatmap(); }
  else if (document.getElementById('analisesPanel').style.display === 'flex') { renderAnalises(); }
  updateGlobalAccountSelector();
}"""
content = content.replace(switch_old, switch_new)

# Clean up other places where calAccName and chartAccName were set
content = content.replace("document.getElementById('calAccName').textContent = acc.name;", "")
content = content.replace("document.getElementById('chartAccName').textContent = acc.name;", "")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("HTML UI update successful")
