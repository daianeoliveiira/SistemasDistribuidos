import os

from dotenv import load_dotenv

load_dotenv()

# Resiliência do pagamento (diagrama)
PAGAMENTO_MAX_TENTATIVAS = 3
PAGAMENTO_TIMEOUT_SEGUNDOS = 5.0

# Backoff exponencial entre tentativas (1s, 2s, 4s).
PAGAMENTO_BACKOFF_BASE_SEGUNDOS = float(os.getenv("PAGAMENTO_BACKOFF_BASE_SEGUNDOS", "1.0"))

# Token simples para simular "liberação controlada" no fallback.
LIBERACAO_TOKEN = os.getenv("LIBERACAO_TOKEN", "admin")

# Simulação para demonstrar Retry/Timeout/Fallback no projeto.
# - Se o usuário escolher PIX e o valor total for >= PAGAMENTO_SIMULAR_TIMEOUT_PIX_EM_VALOR_MIN,
#   o "banco" vai dormir por um tempo maior que PAGAMENTO_TIMEOUT_SEGUNDOS (dispara Timeout).
# - Se PIX der Timeout, o PagamentoService executa fallback e tenta com outra forma.
# - Débito é recusado acima de PAGAMENTO_SIMULAR_RECUSA_DEBITO_ACIMA_VALOR para conseguir também
#   a lógica de retry por retorno False.
PAGAMENTO_SIMULAR_TIMEOUT_PIX = os.getenv("PAGAMENTO_SIMULAR_TIMEOUT_PIX", "1") == "1"
PAGAMENTO_SIMULAR_TIMEOUT_PIX_EM_VALOR_MIN = float(
    os.getenv("PAGAMENTO_SIMULAR_TIMEOUT_PIX_EM_VALOR_MIN", "30")
)
PAGAMENTO_SIMULAR_TIMEOUT_EXTRA_SEGUNDOS = float(
    os.getenv("PAGAMENTO_SIMULAR_TIMEOUT_EXTRA_SEGUNDOS", "1.0")
)
PAGAMENTO_SIMULAR_RECUSA_DEBITO_ACIMA_VALOR = float(
    os.getenv("PAGAMENTO_SIMULAR_RECUSA_DEBITO_ACIMA_VALOR", "20")
)
