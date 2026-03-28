"""
Demonstra produtor + consumidor no mesmo processo, compartilhando queue.Queue.
"""

from __future__ import annotations

import threading
import time

from mercadinho.assincrono import PedidoAsyncService
from mercadinho.models import FormaPagamento
from mercadinho.workers.payment_worker import processar_mensagem


def main() -> None:
    from mercadinho.messaging import FilaPedidos

    fila = FilaPedidos()
    worker = threading.Thread(
        target=lambda: fila.consumir(processar_mensagem),
        daemon=True,
    )
    worker.start()

    svc = PedidoAsyncService(fila)
    svc.registrar_pedido_na_fila(
        "cli-1",
        [{"nome": "Água", "preco": 3.0, "qtd": 2}],
        FormaPagamento.PIX,
    )
    time.sleep(0.5)


if __name__ == "__main__":
    main()
