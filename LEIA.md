# Ramo `dados` (não vai para o site)

Dados de trabalho do Dermatolog.IA, **criptografados** (AES-GCM; a chave sai da frase de acesso do app). Contém características das 10.725 imagens do ISIC extraídas com o modelo do app, listas e rótulos, divisão das pastas, máscaras resumidas das estruturas e o modelo int8 (licença CC BY-NC: uso pessoal).

Restaurar numa conversa nova:
```
git clone --depth 1 --branch dados https://github.com/pedrogschmitz-dotcom/dermia-estudo dados
python3 dados/abre_dados.py dados /home/claude/dermia/restauro   # pede a frase do app
sh /home/claude/dermia/restauro/backup/restaurar.sh
```
Depois copiar `pipeline/` do ramo `main` para /home/claude/dermia/scripts.
