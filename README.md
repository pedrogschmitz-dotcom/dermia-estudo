# DermIA · estudo de dermatoscopia

Uso pessoal de estudo do Dr. Pedro Schmitz (CRM/SC 38229). Não é diagnóstico; não usar para conduta. Software que apoia diagnóstico exige registro na ANVISA.

- App estático (PWA): `index.html`, `sw.js`, `data/`, `thumbs/`, `vendor/`, `fonts/`, `icons/`.
- Modelo: DermLIP-PanDerm (Derm1M, CC BY-NC 4.0), servido **criptografado** em `model/` (AES-GCM). Não redistribuir o modelo aberto.
- Banco e miniaturas: ISIC Archive (CC-0, CC-BY, CC-BY-NC), atribuição por caso em `data/bank.json`. Uso não comercial.
- `pipeline/`: scripts que geram os dados (extração, treino, exportação, criptografia). Ordem e números em `pipeline/` e no documento do projeto.
- Publicação: cada push na `main` publica no GitHub Pages pelo Actions e o app no iPhone se atualiza sozinho.
