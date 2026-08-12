import re

with open('c:\\Users\\Gustavo\\Documents\\Git\\PlanilhaGerenciamentoForex\\Planilha_Gustavo_Pedrosa_FX.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove the broken function definition injected at line 782
broken_snippet = """function renderHeatmap() {
  var acc = getActiveAnalysisAccount();
  const year = state.activeYear;
  const month = state.activeMonth;

  const allTrades = acc.trades;
  const monthTrades = allTrades.filter(t => t.year === year && t.month === month);"""

content = content.replace(broken_snippet, '')

# Replace the actual renderHeatmap
target = """function renderHeatmap() {
  var acc = state.accounts[state.activeAccount];"""
replacement = """function renderHeatmap() {
  var acc = getActiveAnalysisAccount();"""

content = content.replace(target, replacement)

# Replace the typo in navGoTo injected script
target2 = "renderHeatmapYear();"
replacement2 = "renderHeatmap();"
content = content.replace(target2, replacement2)

with open('c:\\Users\\Gustavo\\Documents\\Git\\PlanilhaGerenciamentoForex\\Planilha_Gustavo_Pedrosa_FX.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Cleaned up and updated successfully")
