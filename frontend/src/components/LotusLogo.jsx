import React from 'react';

export default function LotusLogo({ size = 32, color = 'currentColor', className = '' }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 100 100"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-label="Logo Nymphia - Flor de Lótus em traço contínuo"
      role="img"
    >
      {/* Flor de lótus estilizada em traço contínuo, sem preenchimento */}
      <path
        d="M50 20
           C46 32 38 46 32 58
           C26 70 34 82 50 82
           C66 82 74 70 68 58
           C62 46 54 32 50 20Z"
        stroke={color}
        strokeWidth="3.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {/* Pétala esquerda em traço aberto */}
      <path
        d="M44 48
           C32 44 18 52 16 66
           C14 78 28 84 40 80
           C43 79 46 76 48 72"
        stroke={color}
        strokeWidth="3"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {/* Pétala direita em traço aberto */}
      <path
        d="M56 48
           C68 44 82 52 84 66
           C86 78 72 84 60 80
           C57 79 54 76 52 72"
        stroke={color}
        strokeWidth="3"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {/* Base de sustentação sutil */}
      <path
        d="M32 86 C42 89 58 89 68 86"
        stroke={color}
        strokeWidth="2.5"
        strokeLinecap="round"
      />
    </svg>
  );
}
