import re

def get_sabotage_intent(text, rating):
    """
    Analyzes if a fake review is specifically intended to sabotage a product.
    Returns a dictionary with the intent type and a confidence score.
    """
    text = text.lower()
    sabotage_score = 0
    flags = []

    # 1. Competitor Redirection (Highest Sabotage Indicator)
    competitor_patterns = [r'buy \w+ instead', r'switch to \w+', r'better than this', r'waste of money compared to']
    if any(re.search(p, text) for p in competitor_patterns):
        sabotage_score += 50
        flags.append("Competitor Promotion")

    # 2. Extreme Malicious Language
    malicious_terms = ['scam', 'fraud', 'illegal', 'stole', 'lawsuit', 'toxic']
    if any(term in text for term in malicious_terms):
        sabotage_score += 30
        flags.append("Defamatory Language")

    # 3. Rating Mismatch (Logic: 1-star rating but uses generic negative template)
    if rating <= 1:
        sabotage_score += 20
        flags.append("Targeted Rating Attack")

    # Determine Final Intent
    if sabotage_score >= 70:
        intent = "High-Level Sabotage (Malicious)"
    elif sabotage_score >= 40:
        intent = "Potential Competitor Bias"
    else:
        intent = "Generic Spam / Low Quality"

    return {
        "intent": intent,
        "score": min(sabotage_score, 100),
        "flags": flags
    }
