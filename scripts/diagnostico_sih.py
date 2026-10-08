import pandas as pd
from pathlib import Path

arquivos_sih = sorted(list(Path('pipeline_data').glob('sih_*.parquet')))
print(f"Arquivos SIH encontrados: {len(arquivos_sih)}")

dfs = []
for p in arquivos_sih:
    if p.name == 'sih_condicoes.parquet':
        continue
    try:
        d = pd.read_parquet(p)
        if 'ESPEC' in d.columns and 'DIAG_PRINC' in d.columns:
            dfs.append(d)
    except Exception as e:
        print(f"Erro em {p.name}: {e}")

if dfs:
    df = pd.concat(dfs, ignore_index=True)
    print(f"Total de registros combinados: {len(df):,}")
    obst = df[df['ESPEC'] == '02']
    print(f"Total de internações obstétricas (ESPEC=02): {len(obst):,}\n")

    cids = {
        'ITU': 'N39',
        'Pré-eclâmpsia': 'O14',
        'Eclâmpsia': 'O15',
        'Diabetes gestacional': 'O24'
    }

    print(f"{'Condição':<22} {'Só PRINC':>10} {'+DIAG_SECUN':>12} {'+DIAGSEC1-9':>13} {'Ganho Total':>12}")
    diag_sec_cols = [c for c in obst.columns if c.startswith('DIAGSEC') or c == 'DIAG_SECUN']
    for nome, cid in cids.items():
        so_princ = obst['DIAG_PRINC'].astype(str).str.startswith(cid).sum()
        so_secun = obst['DIAG_SECUN'].astype(str).str.startswith(cid) if 'DIAG_SECUN' in obst.columns else False
        princ_secun = (obst['DIAG_PRINC'].astype(str).str.startswith(cid) | so_secun).sum()
        
        any_sec = obst[diag_sec_cols].apply(lambda col: col.astype(str).str.startswith(cid)).any(axis=1) if diag_sec_cols else False
        ambos = (obst['DIAG_PRINC'].astype(str).str.startswith(cid) | any_sec).sum()
        ganho = ambos / so_princ if so_princ else float('inf')
        print(f"{nome:<22} {so_princ:>10,} {princ_secun:>12,} {ambos:>13,} {ganho:>11.2f}x")

    if 'GESTRISCO' in obst.columns:
        cob = obst['GESTRISCO'].notna().mean()
        val_counts = obst['GESTRISCO'].value_counts(dropna=False).head(5).to_dict()
        print(f"\nCobertura do GESTRISCO: {cob:.1%}")
        print(f"Top 5 valores GESTRISCO: {val_counts}")
