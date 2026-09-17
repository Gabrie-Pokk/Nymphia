import React, { useState } from 'react';
import BackButton from '../../components/BackButton';
import { Camera, Lock, Plus, Trash2 } from 'lucide-react';

export default function VisualDiary({ onBack }) {
  const [entradas, setEntradas] = useState(() => {
    const saved = localStorage.getItem('nymphia_diario_visual');
    return saved ? JSON.parse(saved) : [
      {
        id: 1,
        semana: 20,
        data: '2026-08-15',
        nota: 'Primeira vez que senti os chutes bem nítidos enquanto ouvia música clássica!',
        foto_url: null,
        foto_placeholder: 'Barriga com 20 semanas'
      }
    ];
  });

  const [semana, setSemana] = useState(24);
  const [nota, setNota] = useState('');
  const [fotoUrl, setFotoUrl] = useState(null);
  const [mostrarForm, setMostrarForm] = useState(false);

  const handleFotoChange = (e) => {
    const file = e.target.files && e.target.files[0];
    if (file) {
      if (file.size > 5 * 1024 * 1024) {
        alert("A foto selecionada ultrapassa o limite máximo de 5 MB.");
        return;
      }
      const reader = new FileReader();
      reader.onload = (ev) => {
        setFotoUrl(ev.target.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSalvarEntrada = (e) => {
    e.preventDefault();
    if (!nota.trim()) return;

    const novaEntrada = {
      id: Date.now(),
      semana: Number(semana),
      data: new Date().toISOString().split('T')[0],
      nota: nota.trim(),
      foto_url: fotoUrl || null,
      foto_placeholder: `Registro da ${semana}ª semana`
    };

    const atualizados = [novaEntrada, ...entradas];
    setEntradas(atualizados);
    localStorage.setItem('nymphia_diario_visual', JSON.stringify(atualizados));

    setNota('');
    setFotoUrl(null);
    setMostrarForm(false);
  };

  const handleRemoverEntrada = (id) => {
    const atualizados = entradas.filter((item) => item.id !== id);
    setEntradas(atualizados);
    localStorage.setItem('nymphia_diario_visual', JSON.stringify(atualizados));
  };

  return (
    <div>
      <BackButton onClick={onBack} label="Voltar para Início" />

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <div>
          <h2>Diário Visual Gestacional</h2>
          <p className="text-muted" style={{ fontSize: '0.82rem', display: 'flex', alignItems: 'center', gap: '4px' }}>
            <Lock size={12} color="var(--color-vinho)" /> Privado por padrão — apenas você tem acesso
          </p>
        </div>
        <button
          className="btn btn-primary"
          onClick={() => setMostrarForm(!mostrarForm)}
          style={{ minHeight: '40px', padding: '8px 12px', fontSize: '0.85rem' }}
        >
          <Plus size={16} /> Nova Semana
        </button>
      </div>

      {mostrarForm && (
        <form onSubmit={handleSalvarEntrada} className="card" style={{ border: '2px solid var(--color-rosa)', marginBottom: '20px' }}>
          <h3 style={{ fontSize: '1.05rem', marginBottom: '12px' }}>Registrar Memória da Semana</h3>

          <div className="form-group">
            <label>Semana Gestacional</label>
            <input
              type="number"
              className="form-control"
              min={1}
              max={45}
              value={semana}
              onChange={(e) => setSemana(e.target.value)}
              required
            />
          </div>

          <div className="form-group">
            <label>Foto da Barriga ou Ultrassom (Opcional)</label>
            <input
              type="file"
              accept="image/*"
              className="form-control"
              onChange={handleFotoChange}
            />
            {fotoUrl && (
              <div style={{ marginTop: '10px' }}>
                <img
                  src={fotoUrl}
                  alt="Prévia da foto"
                  style={{ width: '100%', maxHeight: '200px', objectFit: 'cover', borderRadius: 'var(--radius-md)' }}
                />
              </div>
            )}
          </div>

          <div className="form-group">
            <label>Relato / Pensamentos da Semana</label>
            <textarea
              className="form-control"
              rows={3}
              placeholder="O que marcou essa semana? Como foi a reação da família ou os preparativos do quartinho?"
              value={nota}
              maxLength={1000}
              onChange={(e) => setNota(e.target.value)}
              required
            />
          </div>

          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              type="button"
              className="btn btn-outline"
              style={{ flex: 1 }}
              onClick={() => {
                setMostrarForm(false);
                setFotoUrl(null);
              }}
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              style={{ flex: 1 }}
            >
              Salvar Memória
            </button>
          </div>
        </form>
      )}

      {/* Galeria de Entradas */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {entradas.map((item) => (
          <div key={item.id} className="card" style={{ padding: '16px', margin: 0 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
              <span className="badge-rosa">{item.semana}ª Semana Gestacional</span>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '0.78rem', color: 'var(--color-text-muted)' }}>
                  {new Date(item.data + 'T12:00:00').toLocaleDateString('pt-BR')}
                </span>
                <button
                  onClick={() => handleRemoverEntrada(item.id)}
                  style={{ background: 'transparent', border: 'none', color: '#999', cursor: 'pointer', padding: '4px' }}
                  title="Excluir lembrança"
                  aria-label="Excluir lembrança"
                >
                  <Trash2 size={15} />
                </button>
              </div>
            </div>

            {item.foto_url ? (
              <img
                src={item.foto_url}
                alt={`Semana ${item.semana}`}
                style={{
                  width: '100%',
                  height: '200px',
                  objectFit: 'cover',
                  borderRadius: 'var(--radius-md)',
                  marginBottom: '12px'
                }}
              />
            ) : (
              <div
                style={{
                  height: '120px',
                  backgroundColor: 'var(--color-rosa-claro)',
                  borderRadius: 'var(--radius-md)',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                  color: 'var(--color-rosa)',
                  marginBottom: '12px',
                  border: '1px dashed var(--color-border)'
                }}
              >
                <Camera size={28} />
                <span style={{ fontSize: '0.82rem', fontWeight: 600 }}>{item.foto_placeholder}</span>
              </div>
            )}

            <p style={{ fontSize: '0.92rem', color: 'var(--color-text-main)', lineHeight: 1.4, margin: 0 }}>
              "{item.nota}"
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
