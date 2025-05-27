"""
各類評估指標的實作
"""
from typing import Tuple, Dict

def calculate_bertscore(reference: str, candidate: str) -> Tuple[float, dict]:
    """計算 BERTScore"""
    from bert_score import score as bert_score
    import torch
    P, R, F1 = bert_score(
        [candidate], [reference],
        lang="zh",
        verbose=False,
        device="cuda" if torch.cuda.is_available() else "cpu"
    )
    return float(F1[0]), {
        "precision": float(P[0]),
        "recall": float(R[0]),
        "f1": float(F1[0])
    }

def calculate_rouge(reference: str, candidate: str, rouge_type: str) -> Tuple[float, dict]:
    """計算 ROUGE 分數"""
    from rouge_score import rouge_scorer
    scorer = rouge_scorer.RougeScorer([rouge_type], use_stemmer=True)
    scores = scorer.score(reference, candidate)
    score = scores[rouge_type]
    return score.fmeasure, {
        "precision": score.precision,
        "recall": score.recall,
        "fmeasure": score.fmeasure
    }

def calculate_heading_quality(reference: str, candidate: str) -> Tuple[float, dict]:
    import re
    def extract_headings(text: str):
        return [line.strip() for line in text.split('\n') if re.match(r'^#+\s+', line)]
    ref_headings = extract_headings(reference)
    cand_headings = extract_headings(candidate)
    if not ref_headings and not cand_headings:
        return 1.0, {"message": "No headings found"}
    if not ref_headings or not cand_headings:
        return 0.0, {"message": "Missing headings in reference or candidate"}
    heading_count_similarity = 1 - abs(len(ref_headings) - len(cand_headings)) / max(len(ref_headings), 1)
    return heading_count_similarity, {
        "reference_headings": ref_headings,
        "candidate_headings": cand_headings,
        "similarity": heading_count_similarity
    }

def calculate_paragraph_structure(reference: str, candidate: str) -> Tuple[float, dict]:
    ref_paragraphs = [p for p in reference.split('\n\n') if p.strip()]
    cand_paragraphs = [p for p in candidate.split('\n\n') if p.strip()]
    if not ref_paragraphs and not cand_paragraphs:
        return 1.0, {"message": "No paragraphs found"}
    if not ref_paragraphs or not cand_paragraphs:
        return 0.0, {"message": "Missing paragraphs in reference or candidate"}
    para_count_similarity = 1 - abs(len(ref_paragraphs) - len(cand_paragraphs)) / max(len(ref_paragraphs), 1)
    return para_count_similarity, {
        "reference_paragraph_count": len(ref_paragraphs),
        "candidate_paragraph_count": len(cand_paragraphs),
        "similarity": para_count_similarity
    }

def calculate_list_usage(reference: str, candidate: str) -> Tuple[float, dict]:
    def count_lists(text: str) -> int:
        return sum(1 for line in text.split('\n') if line.strip().startswith(('-', '*', '•')))
    ref_list_count = count_lists(reference)
    cand_list_count = count_lists(candidate)
    if ref_list_count == 0 and cand_list_count == 0:
        return 1.0, {"message": "No lists found"}
    if ref_list_count == 0 or cand_list_count == 0:
        return 0.0, {"message": "Missing lists in reference or candidate"}
    list_usage_similarity = 1 - abs(ref_list_count - cand_list_count) / max(ref_list_count, 1)
    return list_usage_similarity, {
        "reference_list_count": ref_list_count,
        "candidate_list_count": cand_list_count,
        "similarity": list_usage_similarity
    }
