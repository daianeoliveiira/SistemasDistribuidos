"""
Estado em memória dos pedidos (status + histórico por cliente), compartilhado
entre a API web e o worker de pagamento no mesmo processo.
"""

from __future__ import annotations

import copy
import threading
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

from mercadinho.models.pedido import PedidoMensagem


@dataclass
class PedidoStatus:
    pedido_id: str
    cliente_id: str
    itens: list[dict[str, Any]]
    forma_pagamento: str
    estado: str  # pendente | concluido
    autorizado: bool | None = None
    mensagem_cliente: str = ""
    mensagem_recibo: str = ""
    atualizado_em: str = ""


class PedidoStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._status: dict[str, PedidoStatus] = {}
        self._historico: dict[str, list[dict[str, Any]]] = {}

    def registrar_pendente(
        self,
        pedido_id: str,
        cliente_id: str,
        itens: list[dict],
        forma_pagamento: str,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._lock:
            self._status[pedido_id] = PedidoStatus(
                pedido_id=pedido_id,
                cliente_id=cliente_id,
                itens=copy.deepcopy(itens),
                forma_pagamento=forma_pagamento,
                estado="pendente",
                atualizado_em=now,
            )

    def finalizar_processamento(
        self,
        pedido: PedidoMensagem,
        autorizado: bool,
        recibo_mensagem: str,
        forma_final: str,
        status: str,
    ) -> None:
        if status == "pendente":
            mensagem_cliente = "Pagamento pendente. Aguardando liberação controlada."
        elif autorizado:
            mensagem_cliente = "Autorizado. Compra efetuada com sucesso."
        else:
            mensagem_cliente = "Compra não autorizada. Tente novamente."
        now = datetime.now(timezone.utc).isoformat()

        mensagem_recibo_final = recibo_mensagem
        if forma_final:
            mensagem_recibo_final = f"{recibo_mensagem} Forma final: {forma_final}."

        with self._lock:
            st = self._status.get(pedido.pedido_id)
            if st is None:
                st = PedidoStatus(
                    pedido_id=pedido.pedido_id,
                    cliente_id=pedido.cliente_id,
                    itens=copy.deepcopy(pedido.itens),
                    forma_pagamento=pedido.forma_pagamento.value,
                    estado="concluido" if status != "pendente" else "pendente_pagamento",
                    autorizado=autorizado if status != "pendente" else None,
                    mensagem_cliente=mensagem_cliente,
                    mensagem_recibo=mensagem_recibo_final,
                    atualizado_em=now,
                )
                self._status[pedido.pedido_id] = st
            else:
                st.estado = "concluido" if status != "pendente" else "pendente_pagamento"
                st.autorizado = autorizado if status != "pendente" else None
                st.mensagem_cliente = mensagem_cliente
                st.mensagem_recibo = mensagem_recibo_final
                st.atualizado_em = now

            entry = {
                "pedido_id": pedido.pedido_id,
                "autorizado": autorizado,
                "forma_pagamento": pedido.forma_pagamento.value,
                "itens": copy.deepcopy(pedido.itens),
                "mensagem_cliente": mensagem_cliente,
                "mensagem_recibo": mensagem_recibo_final,
                "quando": now,
            }
            lst = self._historico.setdefault(pedido.cliente_id, [])
            lst.insert(0, entry)

    def liberar_pedido(self, pedido_id: str, cliente_id: str) -> dict[str, Any] | None:
        now = datetime.now(timezone.utc).isoformat()
        with self._lock:
            st = self._status.get(pedido_id)
            if st is None or st.cliente_id != cliente_id:
                return None
            if st.estado != "pendente_pagamento":
                return asdict(st)

            st.estado = "concluido"
            st.autorizado = True
            st.mensagem_cliente = "Autorizado por liberação controlada."
            st.mensagem_recibo = f"{st.mensagem_recibo} Liberado_em: {now}."
            st.atualizado_em = now

            entry = {
                "pedido_id": pedido_id,
                "autorizado": True,
                "forma_pagamento": st.forma_pagamento,
                "itens": copy.deepcopy(st.itens),
                "mensagem_cliente": st.mensagem_cliente,
                "mensagem_recibo": st.mensagem_recibo,
                "quando": now,
            }
            lst = self._historico.setdefault(cliente_id, [])
            lst.insert(0, entry)
            return asdict(st)

    def obter_status(self, pedido_id: str, cliente_id: str) -> dict[str, Any] | None:
        with self._lock:
            st = self._status.get(pedido_id)
            if st is None or st.cliente_id != cliente_id:
                return None
            return asdict(st)

    def listar_historico(self, cliente_id: str) -> list[dict[str, Any]]:
        with self._lock:
            return copy.deepcopy(self._historico.get(cliente_id, []))


pedido_store = PedidoStore()
