# Guia Rápido de Uso - BPA Online

## 🎯 Para Usuários Leigos

### O que é o BPA Online?

É um sistema web que facilita a transferência de dados de atendimentos do e-SUS para o software BPA, sem precisar usar comandos ou scripts complicados.

### Como usar (Passo a Passo)

#### 1️⃣ Acessar o Sistema

Abra seu navegador e digite: `http://localhost:3000`

Você verá a tela inicial com:
- Quantidade de unidades disponíveis
- Total de registros
- Status das tarefas

#### 2️⃣ Fazer uma Nova Extração

1. Clique no botão **"Nova Extração"** (verde, na tela inicial)

2. **Selecionar CNES:**
   - Você verá cards com os números CNES
   - Clique nos cards das unidades que deseja processar
   - Cards selecionados ficam roxos
   - Pode selecionar quantos quiser

3. **Escolher o Período:**
   - **Competência Inicial**: Mês de início (ex: novembro/2025)
   - **Competência Final**: Mês final (ex: novembro/2025)
   - Para um único mês, use o mesmo nas duas

4. Clique em **"Iniciar Extração"**

#### 3️⃣ Acompanhar o Progresso

1. Você será levado para a tela de **Tarefas**

2. Lá você verá:
   - ⏳ Barra de progresso (0% a 100%)
   - 📊 Quantidade de registros processados
   - ⏰ Quando foi iniciado

3. A tela atualiza sozinha a cada 2 segundos

#### 4️⃣ Importar para o BPA

Quando a extração terminar (100%):

1. Aparecerá um botão verde **"Importar"**
2. Clique nele
3. Os dados serão enviados para o software BPA
4. Uma mensagem confirmará o sucesso

#### 5️⃣ Ver Detalhes (Opcional)

- Clique em **"Logs"** para ver detalhes técnicos
- Clique na **lixeira** para remover tarefas antigas

---

## 🆘 Problemas Comuns

### "Não vejo nenhum CNES disponível"

**Solução:** Verifique se os arquivos de dados estão na pasta correta:
- `BPA-main/arquivos_sql/`

### "Erro ao iniciar extração"

**Causas possíveis:**
1. Nenhum CNES selecionado → Selecione pelo menos um
2. Período inválido → Verifique as datas
3. Sistema offline → Chame o suporte técnico

### "Erro ao importar para Firebird"

**Solução:**
1. Verifique se o software BPA está aberto
2. Confirme que o banco de dados está acessível
3. Entre em contato com o técnico

---

## 💡 Dicas

✅ **Teste primeiro com um CNES só** para ver como funciona

✅ **Não feche o navegador** durante o processamento

✅ **Aguarde 100%** antes de importar

✅ **Guarde os IDs das tarefas** para referência futura

---

## 📱 Telas do Sistema

### Tela 1: Dashboard
- Mostra resumo geral
- Botões para nova extração e ver tarefas

### Tela 2: Nova Extração
- Selecionar CNES com cliques
- Escolher período
- Iniciar processamento

### Tela 3: Tarefas
- Ver todas as extrações
- Acompanhar progresso
- Importar dados prontos

---

## ❓ Perguntas Frequentes

**P: Posso fazer várias extrações ao mesmo tempo?**
R: Sim! Cada extração roda independente.

**P: Quanto tempo demora?**
R: Depende da quantidade de registros. Geralmente 1-5 minutos.

**P: Posso fechar o navegador?**
R: Sim, o processamento continua. Ao voltar, verá o progresso atualizado.

**P: O que é "Modo TEST"?**
R: Usa dados de exemplo já carregados. Não conecta ao e-SUS real.

**P: Como sei se deu certo?**
R: Quando chegar a 100% e aparecer "Concluído" em verde.

---

## 📞 Precisa de Ajuda?

1. Tire um print da tela de erro
2. Anote o que estava fazendo
3. Entre em contato com o suporte técnico

**Lembre-se:** Não há problema em experimentar! O modo de teste não afeta dados reais.

---

**Bom uso! 🎉**
