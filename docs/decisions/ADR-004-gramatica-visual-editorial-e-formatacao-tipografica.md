# ADR-004: Gramática visual editorial (Bloomberg Orange) e formatação tipográfica

- **Status:** Aceito
- **Data:** 2026-11-25

## Contexto

Painéis macroeconômicos densos perdem legibilidade rapidamente quando utilizam múltiplas cores saturadas por série, badges coloridos em todas as linhas de tabela, rótulos truncados no mobile ou métricas sem unidade explícita (`%`, `pp`, `R$`).

Durante a evolução do dashboard em `reports/`, os testes visuais em desktop (`1440px`) e mobile identificaram problemas recorrentes com o layout padrão: fontes desproporcionais nos KPIs, subtítulos cortados com reticências, barras negativas na mesma cor das positivas, tabelas misturando taxas percentuais e cotações cambiais sem sufixo, além de rótulos cortados em gráficos de rosca e barras horizontais.

## Decisão

Definir uma gramática visual editorial escura inspirada em terminais financeiros (`#ff6b00` como cor focal única), aplicada de forma uniforme nos estilos globais (`reports/pages/+layout.svelte`, `reports/evidence.config.yaml`) e nos quatro componentes Svelte customizados (`reports/components/`):

1. **Superfícies neutras e foco único:** fundo `#0f0f0f`, cards `#161616`, bordas `#2a2a2a`, largura máxima centralizada em `1440px` e cabeçalho fixo com botão de menu em ícone único à esquerda usando `popover="auto"` em telas estreitas. Apenas o elemento principal, líder ou estado de alerta recebe `#ff6b00`; séries secundárias, referências e barras negativas (como déficit primário) usam cinzas neutros (`#737373`, `#525252`, `#a6a6a6`).
2. **Hierarquia tipográfica tabular:** valores principais dos cartões KPI (`KPITerminalCard.svelte`) usam `Inter` com `tabular-nums`, textos e títulos usam `IBM Plex Sans`, e datas e células numéricas de tabelas (`ExecutiveTable.svelte`, `ConditionalTable.svelte`) usam `IBM Plex Mono`. Subtítulos evitam truncamento prematuro no mobile.
3. **Rótulos diretos no final das séries (`TerminalLineChart.svelte`):** séries reais exibem marcador circular e valor final à direita do gráfico com deslocamento vertical anti-sobreposição (`shiftY`). Linhas de referência estáticas (como `Meta 3,0%` e `Teto 4,5%`) omitem callouts redundantes, e `boundaryGap` garante ticks redondos no eixo Y.
4. **Formatação condicional puramente tipográfica (`ConditionalTable.svelte`):** três níveis discretos de destaque (`alert` em laranja negrito, `primary` em branco neutro e `muted` em cinza esmaecido), sem pílulas coloridas, sem bolinhas de status e sem fundo colorido em linhas inteiras. As unidades são resolvidas linha a linha pelos formatadores (`focusVal`, `focusDelta`, `focusDesvio`, `sgsVal`, `brl4`, além dos prefixos `signed*`) para distinguir automaticamente indicadores em `%`, `pp`, `R$` e bilhões/milhões.
5. **Distribuição por fonte com componente nativo (`qualidade-e-linhagem.md`):** usar `<BarChart swapXY=true>` nativo do Evidence com padding à direita e `yMax` explícito no gráfico de distribuição da camada Silver, garantindo consistência de eixos e exibição integral do percentual líder em telas estreitas.

## Alternativas consideradas

### 1. Tema padrão claro/multicolorido do Evidence com pílulas de status
- **Prós:** nenhuma customização CSS ou Svelte para manter em upgrades do framework.
- **Contras:** reduz o contraste em uso prolongado, cria competição visual entre séries de apoio e séries principais e transforma tabelas longas em mosaicos de badges coloridos.

### 2. Gráficos de barras customizados em HTML puro ou gráfico de rosca
- **Prós:** liberdade total de CSS no caso de HTML; formato compacto no gráfico de rosca.
- **Contras:** o gráfico de rosca apresentou quebra e truncamento de legenda no mobile, e barras HTML isoladas destoavam da engine ECharts usada nos demais painéis; o `<BarChart swapXY=true>` nativo resolveu ambos com padding controlável.

### 3. Formatação genérica por coluna única em tabelas
- **Prós:** configuração declarativa mais curta nas páginas `.md`.
- **Contras:** tabelas heterogêneas (como painel Focus geral e explorador SGS) misturam linhas em `R$` (Câmbio), `%` (IPCA, Selic, PIB) e saldo/volume em moedas (`Reservas`, `Concessões`), exigindo formatação condicionada ao código/indicador da linha.

## Consequências

### Positivas
- **Maior razão dado-tinta:** o usuário identifica imediatamente a série ativa, o desvio positivo/negativo e as unidades corretas sem decodificar legendas extensas.
- **Consistência entre desktop e mobile:** a mesma paleta, tipografia e navegação responsiva funcionam de `390px` a `1920px` sem barras horizontais inesperadas.

### Negativas
- **Manutenção de componentes próprios:** atualizações principais do `@evidence-dev/core-components` exigem validar os quatro componentes em `reports/components/` via `npm run build:strict`.

### Neutras
- A configuração `appearance.switcher: true` permanece ativa em `reports/evidence.config.yaml`, mas `+layout.svelte` inicializa o terminal no tema escuro (`data-theme="dark"`) por padrão.
