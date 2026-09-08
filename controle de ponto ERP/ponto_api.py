# ponto/api.py
# Dependências: pip install fastapi uvicorn python-jose[cryptography] sqlalchemy pydantic
#
# Rodar: uvicorn ponto.api:app --host 0.0.0.0 --port 8000

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timezone, timedelta
from typing import Optional
from enum import Enum
import hashlib, uuid, os, logging

from jose import jwt, JWTError
from sqlalchemy import create_engine, Column, String, DateTime, Enum as SAEnum, Float, Boolean, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

# ─── CONFIG ────────────────────────────────────────────────────────────────────
QR_SECRET     = os.getenv("QR_SECRET_KEY", "troque-em-producao-use-secret-seguro")
QR_ALGORITHM  = "HS256"
DATABASE_URL  = os.getenv("DATABASE_URL", "postgresql://erp:erp@localhost/erp")
TOLERANCIA_MIN = 10   # minutos de tolerância para calcular atraso

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("ponto")

# ─── BANCO ─────────────────────────────────────────────────────────────────────
engine       = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

class TipoRegistro(str, Enum):
    ENTRADA          = "ENTRADA"
    SAIDA            = "SAIDA"
    INTERVALO_INICIO = "INTERVALO_INICIO"
    INTERVALO_FIM    = "INTERVALO_FIM"

class OrigemRegistro(str, Enum):
    APP    = "APP"
    QRCODE = "QRCODE"
    PIN    = "PIN"
    MANUAL = "MANUAL"

class RegistroPonto(Base):
    __tablename__ = "registros_ponto"

    id                = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    funcionario_id    = Column(String, nullable=False, index=True)
    tipo              = Column(SAEnum(TipoRegistro), nullable=False)
    dt_registro       = Column(DateTime(timezone=True), nullable=False)
    origem            = Column(SAEnum(OrigemRegistro), nullable=False)
    tablet_id         = Column(String)
    latitude          = Column(Float)
    longitude         = Column(Float)
    hash_dispositivo  = Column(String)
    offline_sync      = Column(Boolean, default=False)
    justificativa     = Column(String)
    aprovado_por      = Column(String)

Base.metadata.create_all(bind=engine)

# ─── DEPENDÊNCIAS ──────────────────────────────────────────────────────────────
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ─── SCHEMAS ───────────────────────────────────────────────────────────────────
class RegistrarRequest(BaseModel):
    token_qr:  Optional[str] = None    # JWT do QR Code
    pin:       Optional[str] = None    # 4 dígitos
    tablet_id: Optional[str] = None
    latitude:  Optional[float] = None
    longitude: Optional[float] = None
    offline:   bool = False            # flag de sync offline
    dt:        Optional[str] = None    # dt original do registro offline

class RegistrarResponse(BaseModel):
    ok:          bool
    nome:        str
    tipo:        str
    horario:     str
    horas_hoje:  Optional[str] = None
    mensagem:    str

class GerarQRRequest(BaseModel):
    funcionario_id: str
    nome:           str
    validade_anos:  int = 1

# ─── HELPERS ───────────────────────────────────────────────────────────────────
def _gerar_token_qr(funcionario_id: str, nome: str, anos: int = 1) -> str:
    """Gera JWT para o QR Code do funcionário."""
    payload = {
        "sub": funcionario_id,
        "nom": nome,
        "exp": datetime.now(timezone.utc) + timedelta(days=365 * anos),
        "iat": datetime.now(timezone.utc),
        "jti": str(uuid.uuid4()),   # evita reuse de token
    }
    return jwt.encode(payload, QR_SECRET, algorithm=QR_ALGORITHM)

def _validar_token_qr(token: str) -> dict:
    """Valida e decodifica JWT do QR Code. Raises HTTPException se inválido."""
    try:
        data = jwt.decode(token, QR_SECRET, algorithms=[QR_ALGORITHM])
        return {"id": data["sub"], "nome": data["nom"]}
    except JWTError as e:
        log.warning(f"Token QR inválido: {e}")
        raise HTTPException(status_code=401, detail="QR Code inválido ou expirado")

def _validar_pin(pin: str, db: Session) -> dict:
    """
    Valida PIN de 4 dígitos consultando a tabela funcionarios.
    O PIN é armazenado como SHA-256(funcionario_id + pin + salt).
    """
    # Consulta simplificada — adapte ao seu ORM
    resultado = db.execute(
        text("SELECT id, nome FROM funcionarios WHERE pin_hash = :h AND ativo = true"),
        {"h": hashlib.sha256(f"salt_{pin}".encode()).hexdigest()}
    ).fetchone()

    if not resultado:
        raise HTTPException(status_code=401, detail="PIN inválido")
    return {"id": str(resultado.id), "nome": resultado.nome}

def _inferir_tipo(funcionario_id: str, db: Session) -> TipoRegistro:
    """Determina se o próximo registro é ENTRADA ou SAIDA pelo último registro do dia."""
    hoje_inicio = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    ultimo = db.execute(
        text("""
            SELECT tipo FROM registros_ponto
            WHERE funcionario_id = :fid AND dt_registro >= :inicio
            ORDER BY dt_registro DESC LIMIT 1
        """),
        {"fid": funcionario_id, "inicio": hoje_inicio}
    ).fetchone()

    if not ultimo:
        return TipoRegistro.ENTRADA

    sequencia = {
        TipoRegistro.ENTRADA:          TipoRegistro.INTERVALO_INICIO,
        TipoRegistro.INTERVALO_INICIO: TipoRegistro.INTERVALO_FIM,
        TipoRegistro.INTERVALO_FIM:    TipoRegistro.SAIDA,
        TipoRegistro.SAIDA:            TipoRegistro.ENTRADA,  # novo dia / hora extra
    }
    return sequencia.get(ultimo.tipo, TipoRegistro.ENTRADA)

def _calcular_horas_hoje(funcionario_id: str, db: Session) -> Optional[str]:
    """Calcula horas trabalhadas no dia (pares entrada/saída)."""
    hoje_inicio = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    registros = db.execute(
        text("""
            SELECT tipo, dt_registro FROM registros_ponto
            WHERE funcionario_id = :fid AND dt_registro >= :inicio
            ORDER BY dt_registro
        """),
        {"fid": funcionario_id, "inicio": hoje_inicio}
    ).fetchall()

    total = timedelta()
    entrada = None
    for r in registros:
        if r.tipo in (TipoRegistro.ENTRADA, TipoRegistro.INTERVALO_FIM):
            entrada = r.dt_registro
        elif r.tipo in (TipoRegistro.SAIDA, TipoRegistro.INTERVALO_INICIO) and entrada:
            total += r.dt_registro - entrada
            entrada = None

    h = int(total.total_seconds() // 3600)
    m = int((total.total_seconds() % 3600) // 60)
    return f"{h}h{m:02d}min" if total.total_seconds() > 0 else None

def _dt_registro_final(req: RegistrarRequest) -> datetime:
    """Usa dt original para registros offline, senão usa now()."""
    if req.offline and req.dt:
        try:
            return datetime.fromisoformat(req.dt)
        except ValueError:
            pass
    return datetime.now(timezone.utc)

# ─── APP ───────────────────────────────────────────────────────────────────────
app = FastAPI(title="ERP — API de Ponto", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],    # restrinja em produção ao IP do tablet
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

# ─── ENDPOINTS ─────────────────────────────────────────────────────────────────

@app.post("/api/ponto/registrar", response_model=RegistrarResponse)
async def registrar_ponto(req: RegistrarRequest, db: Session = Depends(get_db)):
    """
    Registra batida de ponto via QR Code ou PIN.
    Determina automaticamente o tipo (ENTRADA / SAÍDA / INTERVALO).
    Suporta sincronização de registros offline.
    """
    if not req.token_qr and not req.pin:
        raise HTTPException(status_code=400, detail="Forneça token_qr ou pin")

    # 1. Identificar funcionário
    if req.token_qr:
        funcionario = _validar_token_qr(req.token_qr)
        origem = OrigemRegistro.QRCODE
    else:
        funcionario = _validar_pin(req.pin, db)
        origem = OrigemRegistro.PIN

    # 2. Inferir tipo de registro
    tipo = _inferir_tipo(funcionario["id"], db)

    # 3. Resolver horário (suporte offline)
    dt_reg = _dt_registro_final(req)

    # 4. Persistir
    registro = RegistroPonto(
        funcionario_id   = funcionario["id"],
        tipo             = tipo,
        dt_registro      = dt_reg,
        origem           = origem,
        tablet_id        = req.tablet_id,
        latitude         = req.latitude,
        longitude        = req.longitude,
        offline_sync     = req.offline,
    )
    db.add(registro)
    db.commit()

    log.info(f"Ponto: {funcionario['nome']} | {tipo} | {dt_reg.isoformat()} | {origem}")

    # 5. Calcular horas do dia (só na saída)
    horas_hoje = None
    if tipo == TipoRegistro.SAIDA:
        horas_hoje = _calcular_horas_hoje(funcionario["id"], db)

    horario_fmt = dt_reg.astimezone().strftime("%H:%M")

    mensagens = {
        TipoRegistro.ENTRADA:          f"Bom trabalho, {funcionario['nome'].split()[0]}!",
        TipoRegistro.INTERVALO_INICIO: "Bom descanso!",
        TipoRegistro.INTERVALO_FIM:    "Bem-vindo de volta!",
        TipoRegistro.SAIDA:            f"Até logo! {horas_hoje or ''}",
    }

    return RegistrarResponse(
        ok         = True,
        nome       = funcionario["nome"],
        tipo       = tipo.value,
        horario    = horario_fmt,
        horas_hoje = horas_hoje,
        mensagem   = mensagens[tipo],
    )


@app.post("/api/ponto/qrcode/gerar")
async def gerar_qrcode(req: GerarQRRequest):
    """
    Gera o token JWT para o QR Code do funcionário.
    Chamar ao admitir o funcionário. O resultado é o conteúdo do QR Code a imprimir.
    Proteger este endpoint com autenticação de admin.
    """
    token = _gerar_token_qr(req.funcionario_id, req.nome, req.validade_anos)
    return {
        "funcionario_id": req.funcionario_id,
        "token":          token,
        "expira_em_anos": req.validade_anos,
        "instrucao":      "Gere o QR Code a partir deste token e imprima no crachá.",
    }


@app.get("/api/ponto/espelho/{funcionario_id}")
async def espelho_ponto(funcionario_id: str, mes: int, ano: int, db: Session = Depends(get_db)):
    """
    Retorna todos os registros do mês para geração do espelho de ponto.
    O funcionário deve assinar o espelho mensalmente (Portaria 671/2021).
    """
    inicio = datetime(ano, mes, 1, tzinfo=timezone.utc)
    fim    = (inicio + timedelta(days=32)).replace(day=1)

    registros = db.execute(
        text("""
            SELECT tipo, dt_registro, origem, justificativa
            FROM registros_ponto
            WHERE funcionario_id = :fid
              AND dt_registro >= :ini
              AND dt_registro <  :fim
            ORDER BY dt_registro
        """),
        {"fid": funcionario_id, "ini": inicio, "fim": fim}
    ).fetchall()

    return {
        "funcionario_id": funcionario_id,
        "competencia":    f"{mes:02d}/{ano}",
        "total_registros": len(registros),
        "registros": [
            {
                "tipo":         r.tipo,
                "dt":           r.dt_registro.isoformat(),
                "origem":       r.origem,
                "justificativa": r.justificativa,
            }
            for r in registros
        ],
    }


@app.get("/api/ponto/status")
async def status():
    """Health check para o tablet verificar conectividade."""
    return {"ok": True, "ts": datetime.now(timezone.utc).isoformat()}
