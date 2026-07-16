# Fase 1 — Mapeamento Estético

**Data:** 2026-07-15
**Status:** Concluída

---

## O problema

O Victor tem um senso estético claro e consistente — visível em cada referência que salva, em cada projeto que aprecia. Mas esse senso existia de forma implícita, não documentada. Resultado: a cada projeto novo, a IA partia do zero. Cada brief precisava re-explicar o mesmo gosto. E o próprio Victor não tinha uma articulação escrita de *por que* prefere o que prefere.

## A solução

Criar um sistema onde o senso estético seja:
1. Coletado (referências visuais em `references/`)
2. Analisado (a IA lê as imagens e identifica padrões)
3. Articulado (o *porquê* documentado, não só o *o quê*)
4. Persistido (SOUL.md como fonte de verdade, memória como ponteiro)
5. Aplicável (o SOUL.md é consultado antes de qualquer decisão visual)

## O que foi criado

### Estrutura de pastas
```
references/
  _index.md
  saas/
  portfolio/
  branding/
  editorial/
  motion/
  client/
  misc/       ← 72 imagens do Pinterest aqui
```

Cada pasta tem um README descrevendo o contexto de aplicação. O sistema entende que preferências não são universais — o que funciona em portfolio pode ser errado em SaaS.

### SOUL.md
Manifesto estético vivo na raiz do repositório. Estrutura:
- Princípios universais (6 princípios derivados da análise)
- Dimensões visuais (cor, tipografia, composição, textura, hierarquia)
- Anti-patterns (o que conscientemente evitar)
- Por contexto (SaaS, portfolio, branding, editorial, clientes)
- Conexões entre contextos (pontes para uso exploratório)
- Histórico de análises (log rastreável)

### Integração com memória
Entrada em `~/.claude/projects/.../memory/project_soul.md` garante que futuras sessões comecem com o contexto já carregado.

## A ferramenta técnica

O board de Pinterest tinha ~70 imagens. Pinterest não expõe dados sem JS/login — WebFetch retorna apenas tela de login.

**Solução:** `gallery-dl`, CLI que faz scraping de boards públicos sem autenticação.

```bash
brew install gallery-dl
gallery-dl --directory references/misc <url-do-board>
```

Resultado: 72 imagens baixadas (1 vídeo falhou por falta de `yt-dlp` no PATH — não bloqueante).

## O método de análise

Leitura em 4 lotes de ~18 imagens, com checkpoint de validação do usuário ao final de cada lote. A IA não escreve o SOUL.md até ter lido todas as imagens e validado os padrões com o Victor.

### Por que lotes com validação?
- Evita comprometer o SOUL.md com padrões não confirmados
- Permite ao Victor corrigir interpretações durante o processo (não depois)
- Cria oportunidade para o Victor articular nuances que a IA não pode inferir da imagem sozinha

### O que a análise revelou além do esperado
A validação trouxe contexto que as imagens não continham:
- As referências "genéricas" de SaaS (ForgeAI, OPUS) não são admiração — são referências de mercado para o projeto Roster, onde o desafio é *superar* esse padrão
- O cluster cyber-brutalista (CYBR_, Permitify) é apreciação estética consciente, lido como "Graphic Utilitarism" — não é a voz primária mas não é rejeitado
- O primeiro projeto real a usar o SOUL.md será o portfólio pessoal

## Insights sobre o método

**A IA analisa o que está na imagem. O Victor sabe por que salvou.**
Essas são informações diferentes. A análise da IA é necessária para articular padrões visuais. Mas a intenção por trás de salvar uma imagem só o usuário conhece. O checkpoint de validação é onde essas duas camadas se fundem.

**Contexto ausente nas imagens:**
- Por que ForgeAI está salvo? (Contexto Roster — a IA não poderia inferir)
- Por que CYBR_ está salvo? (Apreciação de Graphic Utilitarism, não incoerência)
- O que o corner radius bubbly do Impact Report significa? (Contexto de cliente específico)

Sem validação, o SOUL.md seria menos preciso.
