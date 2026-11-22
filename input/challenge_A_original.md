# Challenge A: AI Estimation and Bid Assistant for Bills of Quantities

(Text so, wie er uns im Team vorliegt. Die Punkte "What-if-Analysen" und
"Deliverables" stehen hier nicht; deren Quelle bitte ergänzen.)

## Problem

Bills of quantities (BoQs, German: Leistungsverzeichnisse) often contain several thousand line items. They span multiple cost groups and depend on each other across trades.
Companies don't have the time or staff to review BoQs in detail, spot risks, or learn from past projects in a systematic way.
Typical errors are typos, wrong calculations and missed change order opportunities. Each can have a large financial impact.

## Goal

Build a prototype that analyzes and structures BoQs:

- Automatically import and parse long BoQs (PDF, GAEB, Excel)
- Error detection as the first priority: find formal and content gaps such as missing items, unclear descriptions, contradictions and typos
- Risk assessment: flag typical high-risk items, such as vague scope descriptions or unusual quantities
- Detect change order potential and likely points of dispute during construction
- Optional: suggest unit prices or markups based on historical project data

## Dataset with Example BoQs

https://drive.google.com/drive/folders/1wS4UMVghBL8T5opmZ2UBmBu0kr6U8zIB?usp=sharing
(Inhalt liegt vollständig in data/raw/)
