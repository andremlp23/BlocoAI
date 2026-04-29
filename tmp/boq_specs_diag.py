import re
import json

specs_path = '/home/andremlp/Downloads/Specs_Extraction_Context (1).txt'
boq_path = '/home/andremlp/Downloads/Auditoria_Master_BlocoAI (3).txt'

with open(specs_path, 'r', encoding='utf-8') as f:
    specs = f.read()

with open(boq_path, 'r', encoding='utf-8') as f:
    boq = f.read()

spec_lines = [ln.strip() for ln in specs.splitlines() if ln.strip()]
boq_lines = [ln for ln in boq.splitlines() if ln.strip()]
boq_text = '\n'.join(boq_lines)

# Define patterns to extract candidate requirements from specs
candidate_prefixes = [
    'Submittal requirement:', 'Submittal requirement', 'Calculation submittal:', 'Quality Plan submittal:',
    'Certification submittal:', 'Pre-construction meeting:', 'Pre-erection meeting:', 'Connection design responsibility:',
    'Connection design workshop:', 'Sustainability declaration:', 'Pre-erection anchor verification:', 'Anchor bolts:',
    'Execution class:', 'Surface preparation:', 'Galvanising:', 'Intumescent', 'DFT', 'Welding rule', 'Bolted connection rule',
    'Shear studs', 'Shop priming', 'Batch control for coatings', 'Field quality control', 'Erection temporary bracing', 'Delivery and storage'
]

# Heuristic extraction of spec requirements: select lines containing key verbs or prefixes
requirements = []
for ln in spec_lines:
    for p in candidate_prefixes:
        if p.lower() in ln.lower():
            requirements.append(ln)
            break

# Also include lines that start with '- Submittal requirement' variants
for ln in spec_lines:
    if ln.lower().startswith('- submittal') and ln not in requirements:
        requirements.append(ln)

# Deduplicate
requirements = list(dict.fromkeys(requirements))

# Keywords to search in BOQ for each requirement (map)
kw_map = {
    'submitt': ['shop drawing', 'shop drawings', 'erection drawing', 'erection drawings', 'method statement', 'method statements', 'submittal', 'submit', 'submission'],
    'quality': ['quality plan', 'nbn en 1090', 'execution class', 'execution class', 'quality plan', 'certificate', 'certificates', 'mill certificate', 'welder'],
    'calculation': ['calculation', 'connection calculation', 'connection calculations', 'calcs', 'signed/sealed'],
    'meeting': ['pre-construction', 'pre-erection', 'preconstruction', 'pre-erection', 'meeting', 'conference', 'minutes'],
    'anchor': ['anchor', 'anchor verification', 'holding down', 'H.D.A.', 'H.D.A', 'hold down'],
    'galvanis': ['galvanis', 'galvanize', 'galvanize', 'galvanising', 'galvanizing', 'en iso 1461'],
    'intumes': ['intumes', 'intumescent', 'DFT', 'dry film', 'EN 13381', 'fireproof'],
    'surface': ['sa 2.5', 'sa2.5', 'blast', 'blast-clean', 'blast cleaning', 'surface preparation'],
    'weld': ['welder', 'weld', 'welding', 'en 1090', 'en 1011', 'qualification'],
    'bolts': ['bolt', 'bolts', 'high-strength', 'nbn en 14399', 'nbn en 15048'],
    'storage': ['store', 'storage', 'delivery', 'unload', 'platforms', 'skids'],
}

# Function to find matches in BOQ text

def find_boq_matches(kw_list):
    matches = []
    for kw in kw_list:
        for m in re.finditer(re.escape(kw), boq_text, flags=re.IGNORECASE):
            # get surrounding line (we have boq_lines)
            # find line index in boq_lines
            pos = m.start()
            # approximate by counting newlines
            line_idx = boq_text[:pos].count('\n')
            start = max(0, line_idx - 2)
            end = min(len(boq_lines), line_idx + 3)
            context = '\n'.join(boq_lines[start:end])
            matches.append({'kw': kw, 'index': line_idx+1, 'context': context})
    return matches

issues = []

for req in requirements:
    key = req.lower()
    # pick candidate keyword list
    kws = []
    if 'submitt' in key or 'submit' in key:
        kws = kw_map['submitt']
    elif 'quality' in key or 'quality plan' in key:
        kws = kw_map['quality']
    elif 'calculation' in key or 'calculation submittal' in key or 'connection' in key:
        kws = kw_map['calculation']
    elif 'pre-construction' in key or 'pre-erection' in key or 'meeting' in key or 'conference' in key:
        kws = kw_map['meeting']
    elif 'anchor' in key or 'anchor bolts' in key or 'H.D.A' in key:
        kws = kw_map['anchor']
    elif 'galvan' in key:
        kws = kw_map['galvanis']
    elif 'intumes' in key or 'dft' in key:
        kws = kw_map['intumes']
    elif 'surface' in key or 'blast' in key:
        kws = kw_map['surface']
    elif 'weld' in key or 'welder' in key:
        kws = kw_map['weld']
    elif 'bolt' in key or 'bolts' in key:
        kws = kw_map['bolts']
    elif 'store' in key or 'delivery' in key:
        kws = kw_map['storage']
    else:
        # fallback: search for major nouns
        kws = [word for word in ['submittal','quality','calculation','meeting','anchor','galvanis','intumescent','sa 2.5','weld','bolt','store']]

    matches = find_boq_matches(kws)
    found = len(matches) > 0

    # severity heuristics
    if 'submitt' in key or 'quality' in key or 'calculation' in key or 'connection' in key:
        severity = 'Critical'
    elif 'pre-' in key or 'anchor' in key:
        severity = 'High'
    elif 'intumes' in key or 'galvan' in key or 'surface' in key:
        severity = 'Medium'
    else:
        severity = 'Low'

    issue = {
        'requirement': req,
        'spec_snippet': req,
        'found_in_boq': found,
        'boq_matches': matches[:5],
        'severity': severity
    }
    issues.append(issue)

# Additional heuristic checks: paint units in BOQ
paint_tn_matches = re.findall(r"intumescent[^\n]*\btn\b", boq_text, flags=re.IGNORECASE)
if paint_tn_matches:
    issues.append({
        'requirement': 'Intumescent quantities/unit check',
        'spec_snippet': 'Intumescent DFT and application requirements (specs expect DFT/area, not tonnes)',
        'found_in_boq': True,
        'boq_matches': [{'kw':'tn','context':match} for match in paint_tn_matches],
        'severity': 'Medium',
        'note':'BOQ shows intumescent quantities in tn — possible unit mismatch vs SPECS (area/DFT).'
    })

# Summary
summary = {
    'total_requirements': len(requirements),
    'total_issues': sum(1 for i in issues if not i.get('found_in_boq') or i.get('severity') in ('Critical','High')),
    'critical_missing': sum(1 for i in issues if (not i.get('found_in_boq')) and i.get('severity')=='Critical')
}

report = {'summary': summary, 'issues': issues}
print(json.dumps(report, indent=2, ensure_ascii=False))
