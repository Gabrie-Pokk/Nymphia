#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nymphia -- Retreinamento Experimental dos 4 Modelos SIH sem a feature 'SEXO'

Contexto: Na coorte hospitalar de internações obstétricas (ESPEC == '02'),
a feature SEXO é 100% constante (valor '3' = Feminino, em todos os 169.213 registros),
apresentando variância zero e sem ganho de informação para os modelos.

Este script retreina os 4 modelos SIH com features ['IDADE', 'UF_ZI', 'MUNIC_RES']
usando os mesmos hiperparâmetros e partição estratificada de teste (80/20, seed 42),
salvando os novos modelos em pasta isolada (modelos_experimentais_sem_sexo) para
NÃO substituir os modelos de produção sem aprovação do Gabriel.
"""

import os
import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix
)

BASE_DIR = Path(__file__).resolve().parent.parent
PROD_MODELS_DIR = BASE_DIR / "nymphia_backend" / "modelos"
EXP_MODELS_DIR = BASE_DIR / "nymphia_backend" / "modelos_experimentais_sem_sexo"
PIPELINE_DIR = BASE_DIR / "pipeline_data"

EXP_MODELS_DIR.mkdir(parents=True, exist_ok=True)

def executar_experimento():
    print("=" * 70)
    print("AVALIAÇÃO E RETREINAMENTO DOS MODELOS SIH SEM A FEATURE 'SEXO'")
    print("=" * 70)

    sih_path = PIPELINE_DIR / "sih_condicoes.parquet"
    df = pd.read_parquet(sih_path)
    df_obs = df[df["ESPEC"] == "02"]
    
    # Validação da distribuição de SEXO
    sexo_counts = df_obs["SEXO"].value_counts().to_dict()
    print(f"Distribuição de SEXO na coorte ESPEC=='02': {sexo_counts}")
    assert len(sexo_counts) == 1, "SEXO não é 100% constante!"
    
    df_control = df_obs[df_obs["DIAG_PRINC"].str.startswith("O80", na=False)]
    
    conditions = {
        "pre_eclampsia": ("O14", "rf_pre_eclampsia.joblib"),
        "eclampsia": ("O15", "rf_eclampsia.joblib"),
        "diabetes_gestacional": ("O24", "rf_diabetes_gestacional.joblib"),
        "itu": ("N39", "rf_itu.joblib")
    }
    
    orig_features = ["IDADE", "SEXO", "UF_ZI", "MUNIC_RES"]
    new_features = ["IDADE", "UF_ZI", "MUNIC_RES"]
    
    relatorio = []
    
    for cond, (cid, mfile) in conditions.items():
        print(f"\n>>> Processando: {cond.upper()} ({mfile})")
        df_case = df_obs[df_obs["DIAG_PRINC"].str.startswith(cid, na=False)]
        df_comb = pd.concat([df_control.assign(target=0), df_case.assign(target=1)])
        
        train, test = train_test_split(df_comb, test_size=0.2, random_state=42, stratify=df_comb["target"])
        
        y_train = train["target"]
        y_test = test["target"]
        
        # 1. Avaliação do modelo original (COM SEXO)
        m_orig = joblib.load(PROD_MODELS_DIR / mfile)
        X_test_orig = test[orig_features].apply(pd.to_numeric, errors="coerce").fillna(0)
        probs_orig = m_orig.predict_proba(X_test_orig)[:, 1]
        preds_orig = m_orig.predict(X_test_orig)
        
        auc_orig = roc_auc_score(y_test, probs_orig)
        acc_orig = accuracy_score(y_test, preds_orig)
        p_orig = precision_score(y_test, preds_orig, pos_label=1)
        r_orig = recall_score(y_test, preds_orig, pos_label=1)
        f1_orig = f1_score(y_test, preds_orig, pos_label=1)
        cm_orig = confusion_matrix(y_test, preds_orig)
        
        # 2. Treinamento do novo modelo (SEM SEXO)
        X_train_new = train[new_features].apply(pd.to_numeric, errors="coerce").fillna(0)
        X_test_new = test[new_features].apply(pd.to_numeric, errors="coerce").fillna(0)
        
        m_new = RandomForestClassifier(
            n_estimators=150,
            max_depth=10,
            min_samples_leaf=5,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1
        )
        m_new.fit(X_train_new, y_train)
        
        # Salva em pasta experimental isolada
        exp_path = EXP_MODELS_DIR / mfile
        joblib.dump(m_new, exp_path)
        print(f"  Novo modelo salvo em: {exp_path}")
        
        probs_new = m_new.predict_proba(X_test_new)[:, 1]
        preds_new = m_new.predict(X_test_new)
        
        auc_new = roc_auc_score(y_test, probs_new)
        acc_new = accuracy_score(y_test, preds_new)
        p_new = precision_score(y_test, preds_new, pos_label=1)
        r_new = recall_score(y_test, preds_new, pos_label=1)
        f1_new = f1_score(y_test, preds_new, pos_label=1)
        cm_new = confusion_matrix(y_test, preds_new)
        
        item = {
            "condicao": cond,
            "orig_auc": auc_orig,
            "new_auc": auc_new,
            "diff_auc": auc_new - auc_orig,
            "orig_acc": acc_orig,
            "new_acc": acc_new,
            "diff_acc": acc_new - acc_orig,
            "orig_prec": p_orig,
            "new_prec": p_new,
            "diff_prec": p_new - p_orig,
            "orig_rec": r_orig,
            "new_rec": r_new,
            "diff_rec": r_new - r_orig,
            "orig_f1": f1_orig,
            "new_f1": f1_new,
            "diff_f1": f1_new - f1_orig,
            "cm_orig": cm_orig.tolist(),
            "cm_new": cm_new.tolist(),
        }
        relatorio.append(item)
        
        print(f"  COM SEXO -> AUC: {auc_orig:.4f} | Acc: {acc_orig:.4f} | Prec: {p_orig:.4f} | Rec: {r_orig:.4f} | F1: {f1_orig:.4f}")
        print(f"  SEM SEXO -> AUC: {auc_new:.4f} | Acc: {acc_new:.4f} | Prec: {p_new:.4f} | Rec: {r_new:.4f} | F1: {f1_new:.4f}")
        print(f"  Delta    -> AUC: {item['diff_auc']:+.4f} | Acc: {item['diff_acc']:+.4f} | Prec: {item['diff_prec']:+.4f} | Rec: {item['diff_rec']:+.4f} | F1: {item['diff_f1']:+.4f}")

    return relatorio


if __name__ == "__main__":
    res = executar_experimento()
