# design — Workspace de Design

Workspace unificado: projetos profissionais na raiz, disciplinas acadêmicas em `academic/`.

## Estrutura

```
├── academic/          # Disciplinas IFB + suporte (_institucional, _scripts)
├── crema/             # Gelatos para casamentos
├── roster/            # Video Zero e outros projetos
├── designcore/        # Senso estético, referências visuais e processo
```

## Skills disponíveis

- `/letmesee` — Geração de prompts de imagem com controle de direção de arte (câmera, iluminação, composição, grading). Skill global, funciona neste repo.
- `/academico` — Humanização de textos acadêmicos
- `/normalizador` — Normalização ABNT/IFB
- `/abntex` — Exportação para LaTeX ABNT
- `/ghostwriter` — Pesquisa com evidências + redação acadêmica (regra zero: sem evidência = sem citação)

## SOUL.md — Senso Estético

`designcore/SOUL.md` documenta as preferências visuais de Victor de forma sistemática. Consultar antes de qualquer decisão visual em projetos deste workspace. Referências visuais ficam em `designcore/references/` (organizado por contexto: saas/, portfolio/, branding/, editorial/, motion/, client/, misc/). Processo documentado em `designcore/_processo/`.

## letmesee — Módulo Visual

A interface visual do letmesee será implementada no repo `design-freelance`. Spec em: `~/GitHub/design-freelance/_docs/LETMESEE-VISUAL-INTERFACE-SPEC.md`
