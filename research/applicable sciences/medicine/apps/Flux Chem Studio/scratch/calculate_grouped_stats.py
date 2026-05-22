import json
import math
import numpy as np

results_path = "/Users/tshuutheniemvula/Documents/Code/Flux Chem Studio/data/validation_results.json"

with open(results_path, "r") as f:
    data = json.load(f)

results = data["results"]

def get_ranks(v):
    temp = np.argsort(v)
    ranks = np.empty_like(temp, dtype=float)
    ranks[temp] = np.arange(len(v))
    _, counts = np.unique(v, return_counts=True)
    if np.any(counts > 1):
        i = 0
        for count in counts:
            if count > 1:
                ranks[v == v[temp[i]]] = np.mean(np.arange(i, i + count))
            i += count
    return ranks + 1.0

def normal_cdf(z):
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))

def correlation_p_value(r_val, n):
    if n <= 2:
        return 1.0
    if abs(r_val) >= 1.0:
        return 0.0
    t_stat = r_val * math.sqrt((n - 2) / (1.0 - r_val**2))
    p_val = 2.0 * (1.0 - normal_cdf(abs(t_stat)))
    return p_val

def get_broad_class(target_class):
    t_class = target_class.upper()
    if "VIRAL PROTEASE" in t_class or "PROTEASE" in t_class or "PROTEINASE" in t_class:
        return "Viral Protease"
    elif "THROMBIN" in t_class:
        return "Thrombin"
    elif "TRYPSIN" in t_class:
        return "Trypsin"
    elif "NUCLEAR RECEPTOR" in t_class:
        return "Nuclear Receptor"
    elif "GPCR" in t_class:
        return "GPCR"
    elif "KINASE" in t_class:
        return "Kinase"
    elif "CARBONIC ANHYDRASE" in t_class:
        return "Carbonic Anhydrase"
    elif "DHFR" in t_class:
        return "DHFR"
    else:
        return "General / Other"

grouped = {}
for r in results:
    b_class = get_broad_class(r["target_class"])
    grouped.setdefault(b_class, []).append(r)

print(f"{'Grouped Class':<25} | {'Count':<5} | {'Pearson r':<10} | {'p-value':<10}")
print("-" * 60)
for cls, items in sorted(grouped.items(), key=lambda x: len(x[1]), reverse=True):
    count = len(items)
    if count >= 3:
        exp = np.array([r["exp_pki"] for r in items])
        pred = np.array([-r["delta_E"] for r in items])
        
        mean_x = np.mean(exp)
        mean_y = np.mean(pred)
        cov = np.sum((exp - mean_x) * (pred - mean_y))
        std_x = np.sqrt(np.sum((exp - mean_x)**2))
        std_y = np.sqrt(np.sum((pred - mean_y)**2))
        
        r_val = cov / (std_x * std_y) if (std_x > 0 and std_y > 0) else 0.0
        p_val = correlation_p_value(r_val, count)
        print(f"{cls:<25} | {count:<5} | {r_val:<10.4f} | {p_val:<10.4e}")
    else:
        print(f"{cls:<25} | {count:<5} | {'N/A':<10} | {'N/A':<10}")
