import React, { useState } from 'react';

/**
 * Componente oficial de identidade visual Nymphia.
 * Renderiza o ícone floral de flor de lótus em traço suave
 * e suporta alternância automática entre modo claro (vinho) e modo escuro (rosa).
 */
export default function LotusLogo({
  size = 32,
  color = 'currentColor',
  variant = 'auto', // 'auto' | 'vinho' | 'rosa' | 'light' | 'dark'
  className = '',
  style = {},
  withName = false,
  direction = 'row' // 'row' | 'column'
}) {
  const [imgError, setImgError] = useState(false);

  // Determinar se é fundo escuro (precisa da flor rosa) ou fundo claro (flor vinho)
  const isDarkBg =
    variant === 'dark' ||
    variant === 'rosa' ||
    color === '#FFFFFF' ||
    color === 'white' ||
    color === '#fff';

  const logoSrc = isDarkBg ? '/logo-rosa.png' : '/logo-vinho.png';

  const logoImg = !imgError ? (
    <img
      src={logoSrc}
      alt="Logo Nymphia - Flor de Lótus"
      width={size}
      height={size}
      style={{
        objectFit: 'contain',
        display: 'inline-block',
        verticalAlign: 'middle',
        flexShrink: 0,
        ...style
      }}
      className={className}
      onError={() => setImgError(true)}
    />
  ) : (
    <svg
      width={size}
      height={size}
      viewBox="0 0 100 100"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      style={style}
      aria-label="Logo Nymphia - Flor de Lótus"
      role="img"
    >
      <path
        d="M50 20 C46 32 38 46 32 58 C26 70 34 82 50 82 C66 82 74 70 68 58 C62 46 54 32 50 20Z"
        stroke={isDarkBg ? 'var(--color-rosa-claro)' : 'var(--color-vinho)'}
        strokeWidth="3.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M44 48 C32 44 18 52 16 66 C14 78 28 84 40 80 C43 79 46 76 48 72"
        stroke={isDarkBg ? 'var(--color-rosa-claro)' : 'var(--color-vinho)'}
        strokeWidth="3"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M56 48 C68 44 82 52 84 66 C86 78 72 84 60 80 C57 79 54 76 52 72"
        stroke={isDarkBg ? 'var(--color-rosa-claro)' : 'var(--color-vinho)'}
        strokeWidth="3"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M32 86 C42 89 58 89 68 86"
        stroke={isDarkBg ? 'var(--color-rosa-claro)' : 'var(--color-vinho)'}
        strokeWidth="2.5"
        strokeLinecap="round"
      />
    </svg>
  );

  if (!withName) {
    return logoImg;
  }

  return (
    <div
      style={{
        display: 'inline-flex',
        flexDirection: direction,
        alignItems: 'center',
        justifyContent: 'center',
        gap: direction === 'row' ? '10px' : '8px'
      }}
      className={className}
    >
      {logoImg}
      <img
        src="/nymphia-brand-name.png"
        alt="Nymphia"
        style={{
          height: typeof size === 'number' ? Math.round(size * 0.72) : '24px',
          maxWidth: '180px',
          objectFit: 'contain'
        }}
      />
    </div>
  );
}

/**
 * Componente oficial de tipografia da marca ("NYMPHIA" estilizado com detalhes botânicos).
 */
export function NymphiaBrandName({ height = 32, className = '', style = {} }) {
  return (
    <img
      src="/nymphia-brand-name.png"
      alt="Nymphia"
      height={height}
      style={{
        height: `${height}px`,
        maxWidth: '100%',
        objectFit: 'contain',
        display: 'inline-block',
        verticalAlign: 'middle',
        ...style
      }}
      className={className}
    />
  );
}
