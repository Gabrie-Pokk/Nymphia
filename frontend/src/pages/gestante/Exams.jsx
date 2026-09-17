import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import BackButton from '../../components/BackButton';
import { UploadCloud, FileText, CheckCircle2, Calendar, Activity } from 'lucide-react';

export default function Exams({ onBack }) {
  const { authHeaders } = useAuth();
  const [exames, setExames] = useState([]);
  const [tipo, setTipo] = useState('Hemograma Completo');
  const [dataRealizacao, setDataRealizacao] = useState(new Date().toISOString().split('T')[0]);
  const [observacoes, setObservacoes] = useState('');
  const [arquivo, setArquivo] = useState(null);
  const [carregando, setCarregando] = useState(false);
  const [erro, setErro] = useState('');
  const [sucesso, setSucesso] = useState('');

  const carregarExames = async () => {
    try {
      const res = await fetch('/exames', { headers: authHeaders() });
      if (res.ok) {
        const data = await res.json();
        setExames(data);
      }
    } catch (err) {}
  };

  useEffect(() => {
    carregarExames();
  }, []);

  const handleUpload = async (e) => {
    e.preventDefault();
    setErro('');
    setSucesso('');

    if (!arquivo) {
      setErro('Por favor, selecione um arquivo de laudo (PDF, JPG ou PNG).');
      return;
    }
    if (arquivo.size > 10 * 1024 * 1024) {
      setErro('O arquivo é muito grande. O limite máximo permitido é 10 MB.');
      return;
    }

    setCarregando(true);
    const formData = new FormData();
    formData.append('tipo', tipo);
    formData.append('data_realizacao', dataRealizacao);
    if (observacoes) formData.append('observacoes', observacoes);
    formData.append('arquivo', arquivo);

    try {
      const res = await fetch('/exames/upload', {
        method: 'POST',
        headers: authHeaders(),
        body: formData
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Falha ao processar exame.');
      }
      setSucesso('Exame enviado e valores extraídos com sucesso pelo OCR!');
      setArquivo(null);
      setObservacoes('');
      carregarExames();
    } catch (err) {
      setErro(err.message);
    } finally {
      setCarregando(false);
    }
  };

  return (
    <div>
      <BackButton onClick={onBack} label="Voltar para Início" />

      <h2>Laudos & Exames Médicos</h2>
      <p className="text-muted" style={{ marginBottom: '20px' }}>
        Envie fotos ou PDFs dos seus laudos. O sistema extrai e estrutura automaticamente os indicadores clínicos.
      </p>

      {sucesso && (
        <div role="status" style={{ padding: '12px', backgroundColor: '#E8F8F0', color: '#1E7E34', borderRadius: 'var(--radius-sm)', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <CheckCircle2 size={18} /> {sucesso}
        </div>
      )}

      {erro && (
        <div role="alert" style={{ padding: '12px', backgroundColor: '#FDEEE9', color: '#8A2B1A', borderRadius: 'var(--radius-sm)', marginBottom: '16px', borderLeft: '4px solid #D9534F' }}>
          {erro}
        </div>
      )}

      {/* Formulário de Upload */}
      <form onSubmit={handleUpload} className="card">
        <h3 style={{ fontSize: '1.05rem', marginBottom: '12px' }}>Enviar Novo Laudo</h3>

        <div className="form-group">
          <label htmlFor="exame-tipo">Tipo de Exame</label>
          <select
            id="exame-tipo"
            className="form-control"
            value={tipo}
            onChange={(e) => setTipo(e.target.value)}
          >
            <option value="Hemograma Completo">Hemograma Completo</option>
            <option value="Glicemia de Jejum">Glicemia de Jejum</option>
            <option value="Urina Tipo 1 (EAS) + Urocultura">Urina Tipo 1 (EAS) + Urocultura</option>
            <option value="Sorologia para Toxoplasmose (IgG/IgM)">Sorologia para Toxoplasmose (IgG/IgM)</option>
            <option value="Ultrassonografia Morfológica">Ultrassonografia Morfológica</option>
            <option value="Ecocardiograma Fetal">Ecocardiograma Fetal</option>
            <option value="Outro Laudo">Outro Laudo Obstétrico</option>
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="exame-data">Data de Realização</label>
          <input
            id="exame-data"
            type="date"
            className="form-control"
            value={dataRealizacao}
            max={new Date().toISOString().split('T')[0]}
            onChange={(e) => setDataRealizacao(e.target.value)}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="exame-arquivo">Arquivo do Laudo (PDF, JPG ou PNG, máx 10MB)</label>
          <input
            id="exame-arquivo"
            type="file"
            accept=".pdf,.jpg,.jpeg,.png"
            className="form-control"
            onChange={(e) => setArquivo(e.target.files[0])}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="exame-obs">Observações (Opcional)</label>
          <input
            id="exame-obs"
            type="text"
            className="form-control"
            placeholder="Ex: Exame solicitado na última consulta"
            value={observacoes}
            onChange={(e) => setObservacoes(e.target.value)}
          />
        </div>

        <button
          type="submit"
          className="btn btn-primary"
          style={{ width: '100%', minHeight: '48px', marginTop: '10px' }}
          disabled={carregando}
        >
          {carregando ? 'Processando OCR...' : 'Enviar Laudo para Análise'}
          <UploadCloud size={18} />
        </button>
      </form>

      {/* Lista de Exames Cadastrados */}
      <h3 style={{ marginTop: '24px', marginBottom: '12px' }}>Histórico de Exames Enviados</h3>
      {exames.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '24px' }}>
          <p className="text-muted">Nenhum exame enviado ainda.</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {exames.map((ex) => (
            <div key={ex.id} className="card" style={{ margin: 0, padding: '14px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '6px' }}>
                <div>
                  <h4 style={{ fontSize: '0.98rem', color: 'var(--color-vinho)', margin: 0 }}>{ex.tipo}</h4>
                  <span style={{ fontSize: '0.78rem', color: 'var(--color-text-muted)' }}>
                    Realizado em: {new Date(ex.data_realizacao + 'T12:00:00').toLocaleDateString('pt-BR')}
                  </span>
                </div>
                <span className="badge-rosa" style={{ fontSize: '0.72rem' }}>OCR Processado</span>
              </div>

              {ex.valores_extraidos && (
                <div style={{ backgroundColor: '#FFFFFF', padding: '8px 12px', borderRadius: 'var(--radius-sm)', marginTop: '8px', border: '1px solid var(--color-border)', fontSize: '0.82rem' }}>
                  <strong style={{ color: 'var(--color-vinho)', display: 'block', marginBottom: '4px' }}>Valores Estruturados Identificados:</strong>
                  <ul style={{ margin: 0, paddingLeft: '16px', color: 'var(--color-text-main)' }}>
                    {Object.entries(ex.valores_extraidos).map(([chave, valor]) => (
                      <li key={chave}>
                        <span style={{ textTransform: 'capitalize' }}>{chave.replace(/_/g, ' ')}</span>: <strong>{String(valor)}</strong>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
