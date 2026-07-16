# Roster — Brief do Redesign

**Projeto:** rostergiving.com — nova proposta de site
**Data:** 2026-07-15
**Autor:** Victor Costa
**Status:** Brief aprovado — execução pendente

---

## 1. Diagnóstico do site atual

O site atual em rostergiving.com é tecnicamente competente (Astro 5, Switzer, boas animações de entrada) mas tem um problema de identidade: foi construído como uma amalgama de referências de SaaS genérico que conflita com o que o produto realmente é.

**O que está certo no site atual:**
- O copy é forte. *"Every way to give is a fixed amount. Except one."* — permanece.
- A fonte Switzer é a escolha correta.
- A estrutura de informação (hero → prova → produto → como funciona → pricing → waitlist) faz sentido.
- O uso de ouro para versículos bíblicos é um detalhe preciso.
- Os três stats (95%, Once., 2%) comunicam bem.
- O grain sobre fotos é a linguagem certa.

**O que está errado:**
1. **Paleta SaaS genérica.** O indigo #4f3fd8 como acento primário, o azul-roxo gradient no chevron do logo, o off-white frio Stripe (#f6f9fc) — são escolhas de mercado, não de identidade. Um produto para igrejas não deveria parecer uma fintech de SF.
2. **Decoração tecnológica como personalidade.** Particle field, aurora wash, glow cards, stripe threads — esses elementos comunicam "SaaS de engenharia", não "uma nova forma de dar dízimo". A decoração substitui o caráter em vez de servi-lo.
3. **Ausência de pessoas.** A única fotografia atual é uma imagem de membros de joelhos em oração — de fundo de stock. Um produto que serve congregações deveria mostrar congregações reais.
4. **Tensão não resolvida.** O comentário no CSS diz: *"the engineering of Stripe with the soul of a church"* — essa é a tese certa. Mas o site atual executa só a metade Stripe, e a metade church aparece apenas na copy e no versículo de Provérbios. O design não abraça a tensão; escolhe um lado e ignora o outro.

---

## 2. Estratégia

**Tese do novo design:** mostrar que tecnologia precisa e calor humano não são opostos — são o produto.

Roster é uma sacada de produto: você adiciona um botão ao lado de ACH, cartão e Pix-equivalente americano. O botão diz *Give from your paycheck*. O membro configura uma vez, escolhe uma porcentagem, e nunca mais precisa pensar nisso. Para a Igreja: receita que cresce com a renda dos membros, sem card expirado, sem app deletado.

O site precisa comunicar três coisas em ordem:
1. **O que é** — uma nova opção de pagamento, não uma substituição (pastor entende em 10 segundos)
2. **Por que funciona** — percentagem vs. valor fixo; a giving que acompanha a vida
3. **Como instalar** — self-service, menos de 5 minutos, um snippet

**O visitante-alvo:** pastor ou liderança organizacional forte de uma igreja. Não é um engenheiro. Mas é alguém que toma decisões financeiras e de tecnologia para a congregação. Precisa confiar antes de instalar. A confiança vem de clareza, não de animação.

**A conversão desejada:** entrar na waitlist. O contexto é o evento The Church Network — as pessoas vão ao site já com intenção. O design não precisa convencer do zero; precisa confirmar a qualidade que a conversa pessoal criou.

---

## 3. Direção visual

### Princípios aplicados (SOUL.md → Roster)

**1. Fundo:** substituir o off-white frio Stripe (#f6f9fc) por creme/off-white quente (~#f8f5f0 ou similar). A temperatura da superfície de uma sala de reunião de uma igreja, não de um dashboard de São Francisco.

**2. Tipografia:** Switzer permanece como fonte principal — é a escolha certa. O que muda é o uso: display mais agressivo no hero, sem intermediários de tamanho sem convicção. Newsreader permanece exclusivamente para versículos — esse detail fica.

**3. Acento cromático:** o indigo SaaS sai. O ouro que já existe no sistema (#d9a03f / #8a6118) é elevado de "cor de versículo" para acento primário do produto. É quente, é sério, remete a fé sem ser kitsch. CTAs em ouro escuro sobre creme têm contraste WCAG AA.

**4. Logo:** o wordmark ROSTER em navy (#06365B) pode migrar para ink (#17171d) — mais neutro, menos corporativo. O chevron com gradient purple-to-blue (#8B5CF6 → #3B82F6) é o elemento que mais grita "SaaS genérico" — proposta: substituir o gradient por ouro (#d9a03f) ou por um único âmbar quente, alinhando o símbolo ao novo acento. Decisão final pendente de aprovação.

**5. Fotografia:** elemento mais crítico da mudança. Todas as imagens devem ser geradas especificamente para o projeto. Cada seção que precisa de foto tem um brief detalhado na Seção 6 abaixo.

**6. Componentes decorativos removidos:** particle field, aurora wash, glow cards com efeito de brilho, stripe threads animado, pricing background generativo. Substituídos por: espaço vazio intencional, tipografia em escala, dados como elementos gráficos.

**7. O que fica dos componentes atuais:** o PaycheckFlowCard (animação do fluxo de enrollment) é um componente de produto real — permanece, possivelmente redesenhado no novo sistema de cores. O GivingOptionsCard (botão dockando na página de doação) também fica — é a demonstração central do produto.

### Paleta proposta

| Token | Atual | Proposto | Razão |
|---|---|---|---|
| `--color-paper` | #f6f9fc (frio) | #f8f5f0 (quente) | temperatura humana vs. Stripe |
| `--color-surface` | #ffffff | #ffffff | sem mudança |
| `--color-ink` | #17171d | #17171d | sem mudança |
| `--color-accent` | #4f3fd8 (indigo) | #b07d2a (ouro escuro) | identidade vs. SaaS genérico |
| `--color-accent-soft` | #eae8f8 | #f5edd9 | derivado do novo acento |
| `--color-gold` / `--color-gold-ink` | #d9a03f / #8a6118 | mantido ou unificado com accent | |
| Logo chevron | #8B5CF6 → #3B82F6 | #d9a03f (ou derivado) | alinhamento com acento |

### Tipografia

| Uso | Fonte | Mudança |
|---|---|---|
| Display/headings | Switzer variable | sem mudança |
| Body | Switzer | sem mudança |
| Mono (dados, snippets) | Geist Mono | sem mudança |
| Versículos | Newsreader italic | sem mudança |

---

## 4. Arquitetura de páginas

### Páginas do escopo

| Página | Status atual | Decisão |
|---|---|---|
| `/` | Homepage (ChurchesLanding) | Redesign completo |
| `/how-it-works` | Página existente, boa estrutura | Redesign visual, manter conteúdo |
| `/terms` | Existe | Redesign tipográfico simples |
| `/privacy` | Existe | Redesign tipográfico simples |
| `/vulnerability-disclosure` | Existe | Redesign tipográfico simples |

**Páginas fora do escopo:** /pricing, /faq, /integrations, /churches, /hospitals, /embed, /lab — permanecem como estão.

### Estrutura proposta da homepage

A ordem das seções atual é sólida. As mudanças são de execução, não de arquitetura:

```
1. Hero          — tipo display + foto de congregação (nova)
2. Stats bar     — 95% / Once. / 2% — mantido, redesenhado
3. "Not a replacement"  — logos de plataformas + novo visual
4. Produto       — PaycheckFlowCard + GivingOptionsCard — mantidos, redesenhados
5. "Every season" — o argumento da porcentagem — copy mantida
6. Scripture     — Proverbs 3:9 + foto de oração (nova, gerada)
7. How it works  — 3 passos — copy mantida
8. Pricing       — 2% flat — mantido, sem background generativo
9. Trust bar     — FDIC, IRS, SOC2 — mantido
10. Waitlist CTA — novo visual
```

---

## 5. Tabela de decisões

| Elemento | Decisão | Justificativa |
|---|---|---|
| Copy do hero | Mantida | É boa. "Every way to give is a fixed amount. Except one." |
| Fonte principal | Switzer — mantida | Já é a escolha certa; Söhne-family, caráter forte |
| Newsreader para versículos | Mantida | Detalhe preciso, certo para o contexto |
| Off-white frio | Substituído por creme quente | Temperatura humana; anti-pattern evitado: branco de hospital |
| Acento indigo | Substituído por ouro | Identidade própria vs. cor de mercado |
| Gradient do logo | Proposta de mudança para ouro | Alinhamento da identidade; pendente aprovação |
| Glow cards | Removidos | Decoração tecnológica que cria distância emocional |
| Particle field | Removido | Ruído sem função; não serve o contexto de congregação |
| Aurora wash | Removido | Mesmo motivo |
| StripeThreads | Removido | Mesmo motivo |
| PricingBackground generativo | Removido | Substituído por espaço e tipografia |
| PaycheckFlowCard | Mantido | É produto, não decoração |
| GivingOptionsCard | Mantido | É produto, não decoração |
| Fotos | Todas substituídas | Geradas especificamente; sem Pinterest/stock |
| Stats (95%, Once., 2%) | Mantidos | Conteúdo forte; redesign visual |
| Scripture section | Mantida | Toque certo para o mercado |
| CTA primário | Waitlist — mantido | Contexto atual: pré-lançamento |

---

## 6. Briefs de fotografia

Todas as imagens devem ser geradas (não stock). Descrições para geração:

### Hero — foto principal
**Cena:** Interior de uma igreja contemporânea durante culto. Congregação presente, tomado de trás para frente — mostrando fileiras de assentos preenchidos, pessoas olhando para frente. Luz natural entrando por janelas altas. Atmosfera: domingo pela manhã, calma e concentrada. Sem poses.
**Tratamento:** Luz quente de manhã, leve grain fotográfico. Paleta quente (madeira, pele, luz). Sem filtro azulado.
**Proporção:** 3:2 paisagem ou 4:5 retrato (dependendo do layout hero).
**Uso:** ocupa metade do hero em desktop, full-bleed em mobile.

### Scripture section — foto de oração
**Cena:** Grupo pequeno (4–6 pessoas) num círculo de oração dentro de uma sala de uma igreja. Mãos unidas, cabeças levemente inclinadas. Diversidade racial presente. Luz difusa, interior.
**Tratamento:** Leve blur de fundo (foco nas mãos/conexão), grain suave. Preto e branco ou ligeiramente dessaturado.
**Proporção:** 4:5 retrato.
**Uso:** ao lado do versículo Proverbs 3:9.

### How it works — contexto de uso (opcional, 1 imagem)
**Cena:** Uma pessoa no celular, em contexto de Igreja (banco de uma pew, ou corredor), configurando algo no app. Expressão relaxada, casual. Não é foto de produto — é foto de pessoa.
**Tratamento:** Quente, bokeh suave, grain.
**Proporção:** 16:9 landscape.

### Waitlist CTA — foto de fundo (se usada)
**Cena:** Vista de uma congregação em momento de conexão — após o culto, pessoas em pequenos grupos conversando. Luz de tarde entrando. Movimento leve.
**Tratamento:** Levemente subexposto (para texto branco acima), grain, quente.
**Proporção:** 16:9 wide.

---

## 7. Componentes a construir/redesenhar

| Componente | Ação | Notas |
|---|---|---|
| Header/Nav | Redesenhar | Novo sistema de cores; mesmos links |
| Hero section | Construir novo | Tipo display + foto + stats inline |
| Stats bar | Redesenhar | Mesmo conteúdo, sem dark mode |
| Platform section | Redesenhar | Logos mantidos, sem decoração |
| PaycheckFlowCard | Redesenhar internamente | Novo sistema de cores, mesma lógica |
| GivingOptionsCard | Redesenhar internamente | Novo sistema de cores |
| "Every season" section | Redesenhar | Quase só tipografia + foto nova |
| Scripture section | Redesenhar | Gold accent, Newsreader, foto nova |
| How it works | Redesenhar | 3 passos, sem linha SVG decorativa |
| Pricing section | Redesenhar | Sem PricingBackground; espaço + tipo |
| Trust bar | Redesenhar | Novo acento |
| Waitlist CTA | Redesenhar | Sem wheat field stock |
| Footer | Redesenhar | Novo sistema |
| Páginas legais | Template único | Switzer, tipo limpo, sem boilerplate de UI |

---

## 8. Próximos passos

1. Aprovação do brief (Victor)
2. Geração das fotos (Victor, com os briefs da Seção 6)
3. Atualização do design system (`churches.css` ou novo arquivo)
4. Implementação da homepage em `/lab/new-home` para revisão lado a lado
5. Apresentação ao board
6. Aprovação → merge na homepage principal
