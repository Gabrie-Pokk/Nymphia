import React from 'react';
import { ArrowLeft } from 'lucide-react';

export default function BackButton({ onClick, label = 'Voltar' }) {
  return (
    <button
      className="btn-back"
      onClick={onClick}
      aria-label={`Voltar para tela anterior (${label})`}
    >
      <ArrowLeft size={18} />
      <span>{label}</span>
    </button>
  );
}
