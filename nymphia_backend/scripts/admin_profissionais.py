"""
Nymphia -- Aprovação de profissionais pela linha de comando.

Conversa com a API (rotas /admin) usando o token da equipe. Não precisa de
nenhuma biblioteca além do Python.

Antes de usar, defina duas variáveis de ambiente:
  NYMPHIA_URL          endereço do site, ex.: https://app.nymphia.com.br
  NYMPHIA_ADMIN_TOKEN  o mesmo token configurado no servidor
  NYMPHIA_ADMIN_NOME   (opcional) seu nome, para a trilha de auditoria

Comandos:
  python scripts/admin_profissionais.py listar [pendente|aprovado|rejeitado|todos]
  python scripts/admin_profissionais.py documento ID arquivo_de_saida.pdf
  python scripts/admin_profissionais.py aprovar ID
  python scripts/admin_profissionais.py rejeitar ID "motivo da rejeição"
"""
import json
import os
import sys
import urllib.error
import urllib.request


def _pedido(metodo: str, caminho: str, corpo=None):
    base = os.environ.get("NYMPHIA_URL", "").rstrip("/")
    token = os.environ.get("NYMPHIA_ADMIN_TOKEN", "")
    if not base or not token:
        sys.exit("Defina NYMPHIA_URL e NYMPHIA_ADMIN_TOKEN antes de usar o script.")
    dados = json.dumps(corpo).encode("utf-8") if corpo is not None else None
    req = urllib.request.Request(base + caminho, data=dados, method=metodo)
    req.add_header("X-Admin-Token", token)
    req.add_header("X-Admin-Nome", os.environ.get("NYMPHIA_ADMIN_NOME", "equipe"))
    if dados is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.read(), resp.headers.get("Content-Type", "")
    except urllib.error.HTTPError as erro:
        sys.exit(f"Erro {erro.code}: {erro.read().decode('utf-8', 'replace')}")


def main(args) -> None:
    if not args:
        sys.exit(__doc__)
    comando = args[0]

    if comando == "listar":
        situacao = args[1] if len(args) > 1 else "pendente"
        corpo, _ = _pedido("GET", f"/admin/profissionais?situacao={situacao}")
        lista = json.loads(corpo)
        if not lista:
            print(f"Nenhum profissional com situação '{situacao}'.")
        for p in lista:
            doc = "com documento" if p["enviou_documento"] else "SEM documento"
            print(f"{p['id']}  {p['registro']:<20} {p['status_verificacao']:<10} {doc:<14} "
                  f"{p['nome']} <{p['email']}>  conferir em: {p['onde_conferir']}")
    elif comando == "documento" and len(args) == 3:
        corpo, _ = _pedido("GET", f"/admin/profissionais/{args[1]}/documento")
        with open(args[2], "wb") as f:
            f.write(corpo)
        print(f"Documento salvo em {args[2]}")
    elif comando == "aprovar" and len(args) == 2:
        corpo, _ = _pedido("POST", f"/admin/profissionais/{args[1]}/aprovar")
        print("Aprovado:", json.loads(corpo)["registro"])
    elif comando == "rejeitar" and len(args) == 3:
        corpo, _ = _pedido("POST", f"/admin/profissionais/{args[1]}/rejeitar", {"motivo": args[2]})
        print("Rejeitado:", json.loads(corpo)["registro"])
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
