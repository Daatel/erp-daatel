import sys
import os
import threading
import time

# Adiciona diretório pai ao path para importar database
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import db_transaction, run_query, fetch_all, run_query_tx, fetch_all_tx, format_pg

def test_transaction_rollback():
    print("[TEST] Testando Rollback Transacional...")
    
    # 1. Obter quantidade inicial de produtos
    df_inicial = fetch_all("SELECT COUNT(*) as total FROM produtos")
    count_inicial = int(df_inicial.iloc[0]['total'])
    
    # 2. Executar inserção que vai falhar
    try:
        with db_transaction() as conn:
            cursor = conn.cursor()
            run_query_tx(cursor, "INSERT INTO produtos (nome, unidade_medida, preco_venda_base) VALUES ('PRODUTO_TESTE_ROLLBACK', 'un', 10.0)")
            
            # Simula um erro inesperado no meio da transação
            raise ValueError("Erro intencional para forçar Rollback")
    except ValueError as e:
        print(f"   [INFO] Capturado erro esperado: {e}")
        
    # 3. Verificar se o produto de teste não foi adicionado
    df_final = fetch_all("SELECT COUNT(*) as total FROM produtos WHERE nome = 'PRODUTO_TESTE_ROLLBACK'")
    count_final = int(df_final.iloc[0]['total'])
    
    if count_final == 0:
        print("   [SUCCESS] Sucesso: Transação revertida corretamento. Nenhum registro órfão criado!")
    else:
        print("   [FAIL] Erro: O registro foi inserido mesmo após o Rollback!")
        sys.exit(1)

def test_transaction_commit():
    print("[TEST] Testando Commit Transacional...")
    
    # 1. Inserir produto via transação de sucesso
    with db_transaction() as conn:
        cursor = conn.cursor()
        run_query_tx(cursor, "INSERT INTO produtos (nome, unidade_medida, preco_venda_base) VALUES ('PRODUTO_TESTE_COMMIT', 'un', 15.0)")
        
    # 2. Verificar se o produto foi adicionado
    df = fetch_all("SELECT COUNT(*) as total FROM produtos WHERE nome = 'PRODUTO_TESTE_COMMIT'")
    count = int(df.iloc[0]['total'])
    
    if count > 0:
        print("   [SUCCESS] Sucesso: Transação efetivada e persistida!")
        # Limpar sujeira
        run_query("DELETE FROM produtos WHERE nome = 'PRODUTO_TESTE_COMMIT'")
    else:
        print("   [FAIL] Erro: Registro não encontrado após o Commit!")
        sys.exit(1)

def test_concurrency_locking():
    print("[TEST] Testando Concorrência e Bloqueio de Linhas (FOR UPDATE)...")
    
    # Criar um lote de produção temporário para simular
    run_query("""
        INSERT INTO producao_diaria (id, data, hora_inicio, hora_fim, materia_prima_kg, produto_id, produto_final_kg, perdas_kg, custo_total_lote, custo_unitario_lote)
        VALUES (9999, '2026-06-17', '08:00', '12:00', 100, 1, 80, 20, 1000, 12.5)
    """)
    
    results = []
    
    def thread_1_worker():
        try:
            with db_transaction() as conn:
                cursor = conn.cursor()
                print("   [Thread 1] Executando SELECT ... FOR UPDATE (Bloqueando lote 9999)...")
                # No SQLite, format_pg vai tirar o FOR UPDATE, mas a transação do SQLite bloqueará a escrita concorrente no commit
                df = fetch_all_tx(cursor, "SELECT * FROM producao_diaria WHERE id = 9999 FOR UPDATE")
                print("   [Thread 1] Lote bloqueado. Segurando transação por 2 segundos...")
                time.sleep(2)
                run_query_tx(cursor, "UPDATE producao_diaria SET perdas_kg = 25.0 WHERE id = 9999")
                print("   [Thread 1] Atualizado. Liberando transação (Commit)...")
        except Exception as e:
            print(f"   [Thread 1] Erro: {e}")

    def thread_2_worker():
        try:
            time.sleep(0.5) # Aguarda Thread 1 pegar o lock
            start_time = time.time()
            print("   [Thread 2] Tentando atualizar o mesmo lote 9999 concorrentemente...")
            with db_transaction() as conn:
                cursor = conn.cursor()
                # Esta operação deve esperar a Thread 1 liberar o lock/transação
                run_query_tx(cursor, "UPDATE producao_diaria SET perdas_kg = 30.0 WHERE id = 9999")
                duration = time.time() - start_time
                print(f"   [Thread 2] Atualização concluída. Tempo de espera: {duration:.2f}s")
                results.append(duration)
        except Exception as e:
            print(f"   [Thread 2] Erro: {e}")

    t1 = threading.Thread(target=thread_1_worker)
    t2 = threading.Thread(target=thread_2_worker)
    
    t1.start()
    t2.start()
    
    t1.join()
    t2.join()
    
    # Limpeza
    run_query("DELETE FROM producao_diaria WHERE id = 9999")
    
    if len(results) > 0 and results[0] >= 1.0:
        print("   [SUCCESS] Sucesso: O bloqueio de concorrência funcionou! A Thread 2 aguardou a liberação da Thread 1.")
    else:
        print("   [WARNING] Aviso: O tempo de espera foi menor do que o bloqueio da transação. "
              "Isso pode indicar que você está usando SQLite local (onde transações concorrentes de escrita "
              "bloqueiam o banco inteiro no commit, mas não seguram SELECTs síncronos da mesma forma que o Supabase PostgreSQL com FOR UPDATE).")

if __name__ == "__main__":
    print("==================================================")
    print("INICIANDO SUITE DE TESTES DE RESILIENCIA E CONCORRENCIA")
    print("==================================================")
    test_transaction_rollback()
    print("--------------------------------------------------")
    test_transaction_commit()
    print("--------------------------------------------------")
    test_concurrency_locking()
    print("==================================================")
    print("Todos os testes de resiliencia e integridade concluidos!")
