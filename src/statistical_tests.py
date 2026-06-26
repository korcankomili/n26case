from scipy.stats import chisquare, chi2, chi2_contingency, ncx2
import pandas as pd 
import numpy as np
from scipy.optimize import brentq

def contingency_table(df, outcome, group_col="treatment"):  
    if isinstance(outcome, str):
        return pd.crosstab(df[group_col], df[outcome])
    if len(outcome) == 1:
        return pd.crosstab(df[group_col], df[outcome[0]])
    return df.groupby(group_col)[outcome].sum() 

def chi2_by_step(df, group_col, counts, steps):
    """Chi-square + Cohen's w per funnel step across groups.
    p tells you if a difference is detectable; w tells you if it matters.
    w is N-independent, so it survives the 1.2M-row overpower trap."""
    g = df.groupby(group_col)[counts].sum()
    rows = []
    for name, base, adv in steps:
        tab = np.c_[g[adv].values, (g[base] - g[adv]).values]
        chi2_stat, p, dof, _ = chi2_contingency(tab)
        n = tab.sum()
        w = np.sqrt(chi2_stat / n)
        band = ("negligible" if w < 0.1 else "small" if w < 0.3
                else "medium" if w < 0.5 else "large")
        rows.append(dict(step=name, n=int(n), chi2=round(chi2_stat, 2),
                         dof=dof, p=round(p, 3), cohens_w=round(w, 4), band=band))
    return pd.DataFrame(rows)

def chi2_test(df, outcome, group_col="treatment"):
    """
        This function helps us understand if the outcome is associated with the group by using a chi-square test of independence.
        The null hypothesis is that the outcome is independent of the group.
    """
    table = contingency_table(df, outcome, group_col)
    chi2_stat, p_value, dof, expected = chi2_contingency(table)
    cohen_w = np.sqrt(chi2_stat / table.values.sum())
 
    print(f"Chi2: {chi2_stat:.4f}, dof: {dof}, p-value: {p_value:.5f}, Cohen's w: {cohen_w:.4f}")
    if p_value < 0.05:
        print(f"Reject the null hypothesis: '{outcome}' is associated with '{group_col}'.")
    else:
        print(f"Fail to reject the null hypothesis: no significant association between '{outcome}' and '{group_col}'.")
 
    return chi2_stat, p_value, dof

def chi2_residuals(df, outcome, group_col="treatment"):
    """
        This function helps us understand which cells drive the association by computing adjusted standardized residuals.
        A cell with |residual| > ~2 stands out (positive = observed above expected, negative = below).
    """
    table = contingency_table(df, outcome, group_col)
    observed = table.values.astype(float)
    N = observed.sum()
    row = observed.sum(axis=1, keepdims=True)
    col = observed.sum(axis=0, keepdims=True)
    expected = row @ col / N
    residuals = (observed - expected) / np.sqrt(expected * (1 - row / N) * (1 - col / N))
 
    return pd.DataFrame(residuals, index=table.index, columns=table.columns)

def chi2_power_report(chi2_stat, N, dof, power=0.80):
    """
        This function summarises the power diagnostics of a chi-square test in one table:
        the observed effect, the minimum detectable effect at the current N, the power at
        the observed effect, and the N needed to reach the target power. Effect is Cohen's w.
    """
    crit = chi2.ppf(0.95, dof)
    w = np.sqrt(chi2_stat / N)
    lam = brentq(lambda L: ncx2.sf(crit, dof, L) - power, 1e-6, 1e4)
    mde_w = np.sqrt(lam / N)
    power_obs = ncx2.sf(crit, dof, N * w ** 2)
    n_needed = lam / w ** 2
    significant = chi2.sf(chi2_stat, dof) < 0.05
 
    if power_obs >= power:
        print(f"""
        Significant and well-powered (power={power_obs:.2f}): observed w={w:.3f} is above the MDE w={mde_w:.3f}. 
        Reliable association, trust the result.""")

    elif significant:
        print(f"""
        Significant but underpowered (power={power_obs:.2f}): observed w={w:.3f} is below the MDE w={mde_w:.3f}, 
        so the effect estimate may be unstable/inflated. Worth replicating with more data.""")
        
    else:
        print(f"""
        Inconclusive (power={power_obs:.2f}): not significant, but observed w={w:.3f} is below the MDE w={mde_w:.3f}, 
        so the test was too weak to detect it. Absence of evidence is not evidence of absence. Need ~{n_needed:.0f} total for power={power}.""")
 
    return pd.DataFrame({
        "question": [
            "observed effect (Cohen's w)",
            f"MDE: smallest detectable w at N={N}",
            "power at the observed effect",
            f"N needed for power={power}",
        ],
        "value": [w, mde_w, power_obs, n_needed],
    })