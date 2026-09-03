# AI Model Evaluation Report

## Purpose

The Module 3 model classifies simulated transactions for analyst support. It does not automatically block payments.

## Dataset

- Synthetic transaction records
- Features: amount, hour, one-hour velocity, new-device indicator and merchant risk
- No personal or real financial data

## Model

- StandardScaler
- Logistic Regression with balanced class weights
- Stratified train/test split
- Fixed random state for reproducibility

## Metrics

Verified on 3 September 2026 using `POST /api/v1/fraud/train`; the run is stored in the
`model_registry` table:

| Metric | Result |
|---|---:|
| Accuracy | 0.8900 |
| Precision | 0.7222 |
| Recall | 0.8478 |
| F1 score | 0.7800 |
| Rows | 800 |
| Fraud rate | 0.2288 |

These values describe one reproducible train/test split of a synthetic dataset. They are not evidence
of production performance, fairness across real populations, or regulatory approval.

## Governance controls

- Model and dataset purpose are documented.
- Model version, feature list, metrics and threshold are stored.
- Reasons are attached to alerts.
- Analysts record decisions and notes.
- No automated blocking occurs.
- Limitations and potential dataset bias must be explained during the viva.
