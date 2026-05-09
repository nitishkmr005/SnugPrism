"""Add Statistics and ML Models Q&As to questions.json (idempotent)."""
import json
from pathlib import Path

QA_FILE = Path(__file__).parent.parent / "data" / "seed" / "questions.json"

NEW_QUESTIONS = [
    # ── STATISTICS ──────────────────────────────────────────────────────────────
    {
        "topic_slug": "statistics",
        "question": "Your A/B test shows p=0.04 after running for two days. Your PM immediately wants to ship. What questions do you ask before making the decision?",
        "answer": """p=0.04 alone is not a ship signal. Ask these before deciding:

**1. Did you peek?** If you checked the results before the planned end date, the p-value is invalid — repeated testing inflates Type I error. Use sequential testing (e.g., always-valid p-values) if you need to peek.

**2. What was the pre-specified sample size?** If you haven't reached the planned n, stopping early is underpowered — you may have caught a noise spike. Check if actual_n / planned_n < 0.8.

**3. What is the effect size?** Statistical significance ≠ practical significance. A 0.01% CTR lift that's "significant" on 10M users is meaningless if the business threshold is 1%.

**4. Which metrics moved?** Check guardrail metrics (revenue, session length, retention). A positive primary metric with a broken guardrail is a no-ship.

**5. Is there SRM?** If treatment/control split deviates from expected, the randomization is broken — p-value is uninterpretable.

**6. Multiple comparisons?** If you tested 20 metrics and one hit p=0.04, expected false positive rate is ~65% without correction.

**Production rule:** Set end date, primary metric, and decision threshold *before* running the experiment, not after seeing results.""",
        "difficulty": "hard",
        "tags": ["statistics", "ab-testing", "hypothesis-testing", "p-value"],
        "code_snippet": None,
        "comparison_table": None,
        "reference_urls": []
    },
    {
        "topic_slug": "statistics",
        "question": "What is a p-value? What is the most common misconception about it?",
        "answer": """A **p-value** is the probability of observing data as extreme as (or more extreme than) what you observed, *assuming the null hypothesis is true*.

Formally: P(data | H₀ is true)

**Most common misconception:** "p=0.03 means there's a 3% chance the null hypothesis is true." This is wrong.

The p-value says nothing about the probability that H₀ is true — it's a statement about data given H₀, not about H₀ given data. That would require Bayesian reasoning with a prior on H₀.

**Other common misconceptions:**
- "p < 0.05 means the result is important" — effect size matters, not just significance
- "p = 0.06 means the experiment failed" — it means insufficient evidence to reject H₀ at α=0.05, not evidence of no effect
- "Replicating with p < 0.05 proves the result" — replication requires multiple independent studies, not a single confirmation

**What p < α actually means:** If the null were true, you'd observe data this extreme less than α fraction of the time. It's a long-run frequency guarantee, not a statement about this specific experiment.""",
        "difficulty": "easy",
        "tags": ["statistics", "hypothesis-testing", "p-value"],
        "code_snippet": None,
        "comparison_table": None,
        "reference_urls": []
    },
    {
        "topic_slug": "statistics",
        "question": "Explain Type I and Type II errors. For a fraud detection model, how do you decide which error is more costly?",
        "answer": """**Type I error (False Positive, α):** Rejecting H₀ when it is true. In fraud: flagging a legitimate transaction as fraud.

**Type II error (False Negative, β):** Failing to reject H₀ when it is false. In fraud: letting actual fraud through.

**Power = 1 − β:** Probability of correctly detecting a real effect when it exists.

**Setting the tradeoff for fraud detection:**
- Type I cost: customer friction, declined legitimate card, churn, support cost (~$5–20 per dispute)
- Type II cost: fraudulent transaction loss, chargeback fees, regulatory exposure (~$50–500+ per incident)

Since Type II is usually far more costly in fraud, you operate at **low decision threshold** (flag more) and **accept higher FPR** to maximize recall.

In practice, set the threshold by computing expected loss = FP_rate × cost_FP + FN_rate × cost_FN across thresholds and minimize total expected cost. This is the **cost-sensitive threshold selection** approach.

**Interview tip:** Never say "we minimize false positives" or "we minimize false negatives" in isolation — always frame as minimizing *expected cost* given the asymmetric penalties.""",
        "difficulty": "medium",
        "tags": ["statistics", "hypothesis-testing", "classification", "fraud"],
        "code_snippet": None,
        "comparison_table": {
            "headers": ["", "Predicted Positive", "Predicted Negative"],
            "rows": [
                ["Actual Positive", "TP (correct)", "FN — Type II error"],
                ["Actual Negative", "FP — Type I error", "TN (correct)"]
            ]
        },
        "reference_urls": []
    },
    {
        "topic_slug": "statistics",
        "question": "You're running 20 simultaneous A/B tests across different metrics. How do you handle multiple comparisons?",
        "answer": """Running 20 independent tests at α=0.05 gives an expected **4 false positives** even if no effect exists. The family-wise error rate (FWER) = 1 − (1−0.05)²⁰ ≈ 64%.

**Methods to correct:**

**1. Bonferroni correction** — divide α by number of tests: α_adjusted = 0.05/20 = 0.0025. Simple, conservative, controls FWER. Too strict when tests are correlated.

**2. Benjamini-Hochberg (FDR control)** — controls False Discovery Rate (expected fraction of false positives among rejected tests), not FWER. Less conservative, better for exploratory analysis. Algorithm: rank p-values ascending, reject those where p_i ≤ (i/m) × α.

**3. Hierarchical testing** — pre-specify a primary metric; only test secondary metrics if primary is significant. Preserves FWER without sacrificing power.

**4. Bayesian approach** — assign priors to each hypothesis; posterior credible intervals naturally account for multiple looks without correction.

**Practical recommendation:**
- Use **Bonferroni** when you have ≤5 pre-specified primary metrics
- Use **BH (FDR)** for exploratory metric discovery (e.g., 20+ behavioral metrics)
- Never test all metrics, see one hit p=0.04, and call it significant without disclosure""",
        "difficulty": "medium",
        "tags": ["statistics", "ab-testing", "multiple-testing", "fdr"],
        "code_snippet": None,
        "comparison_table": None,
        "reference_urls": []
    },
    {
        "topic_slug": "statistics",
        "question": "What assumptions does OLS linear regression make? How do you diagnose and fix each violation?",
        "answer": """**Five key assumptions (LINE + Homoscedasticity):**

**1. Linearity** — relationship between X and y is linear.
- Diagnose: residual vs. fitted plot (should show random scatter, no curve)
- Fix: transform features (log, sqrt, polynomial terms)

**2. Independence** — residuals are independent (no autocorrelation).
- Diagnose: Durbin-Watson test, ACF plot of residuals
- Fix: add time fixed effects, use time-series models (ARIMA), or GLS

**3. Normality of residuals** — residuals are normally distributed (for inference, not prediction).
- Diagnose: Q-Q plot, Shapiro-Wilk test
- Fix: transform y (Box-Cox), use robust regression, or rely on CLT for large n

**4. Homoscedasticity** — residual variance is constant across all X levels.
- Diagnose: Breusch-Pagan test, scale-location plot
- Fix: weighted least squares, HC3 robust standard errors, log-transform y

**5. No multicollinearity** — predictors are not highly correlated with each other.
- Diagnose: Variance Inflation Factor (VIF > 10 is problematic)
- Fix: drop correlated features, use PCA, ridge regression, or domain-based combination

**Important:** violations affect **inference** (coefficient p-values, CIs) more than **prediction accuracy**. For prediction-only ML pipelines, linearity and some heteroscedasticity are tolerable.""",
        "difficulty": "hard",
        "tags": ["statistics", "regression", "ols", "assumptions"],
        "code_snippet": None,
        "comparison_table": None,
        "reference_urls": []
    },
    {
        "topic_slug": "statistics",
        "question": "How do you compute the required sample size for an A/B test? Walk through each input parameter.",
        "answer": """Sample size formula for two-proportion z-test:

**n = (Z_α/2 + Z_β)² × (p₁(1−p₁) + p₂(1−p₂)) / (p₁ − p₂)²**

**Inputs:**
- **α (significance level):** typically 0.05; Z_α/2 = 1.96 for two-tailed test
- **β (Type II error rate):** typically 0.2 (80% power); Z_β = 0.84
- **p₁ (baseline conversion rate):** current measured CVR from your system
- **MDE (minimum detectable effect):** smallest lift you care about — p₂ = p₁ × (1 + MDE). This is the most consequential input. A 1% MDE on a 5% CVR baseline needs ~10× more users than a 10% MDE.
- **Traffic split:** symmetric 50/50 is most efficient. Uneven splits (e.g., 90/10) need much larger total n.

**Practical notes:**
- Power calculators (statsig.com, evan.miller.org) take these inputs.
- Always compute n *before* launching. Computing it post-hoc to justify stopping is p-hacking.
- Add 10-20% buffer for user drops (assignment without conversion event).
- For metric with continuous outcome (revenue), use the variance of the metric instead of p(1-p).

**Example:** baseline CTR = 5%, MDE = 10% relative lift (to 5.5%), α=0.05, power=80% → ~14,000 users per arm.""",
        "difficulty": "medium",
        "tags": ["statistics", "ab-testing", "sample-size", "power-analysis"],
        "code_snippet": None,
        "comparison_table": None,
        "reference_urls": []
    },
    {
        "topic_slug": "statistics",
        "question": "What is bootstrapping? When do you prefer it over parametric confidence intervals?",
        "answer": """**Bootstrapping** is a resampling method: draw B samples (with replacement) of size n from your observed data, compute the statistic on each sample, and use the resulting distribution to construct a confidence interval.

**Algorithm:**
1. From sample of size n, draw B=1000–10000 bootstrap samples (each size n, with replacement)
2. Compute statistic θ̂* on each bootstrap sample
3. CI = [θ̂*_α/2, θ̂*_(1-α/2)] (percentile method) or use BCa (bias-corrected accelerated)

**When to prefer bootstrap over parametric CIs:**

- **Non-normal data or small n:** Parametric CIs assume normality (or CLT kicks in for large n). Bootstrap makes no distributional assumption.
- **Complex statistics:** Median, correlation, AUROC, F1, NDCG — parametric CIs for these are derived or unavailable; bootstrap works for any statistic.
- **Skewed distributions:** Revenue, lifetime value, session duration — heavy-tailed, bootstrap captures asymmetry.
- **Ratios and differences of statistics:** e.g., CTR lift; parametric methods require delta method approximations.

**When parametric is fine:** large n (>1000), metric is a mean or proportion, data is approximately normal.

**Production use:** always bootstrap AUROC, NDCG@K, and any percentile metric (P50, P95) when reporting offline evaluation results.""",
        "difficulty": "medium",
        "tags": ["statistics", "bootstrap", "confidence-intervals", "resampling"],
        "code_snippet": None,
        "comparison_table": None,
        "reference_urls": []
    },
    {
        "topic_slug": "statistics",
        "question": "You have observational data and want to estimate a causal effect (e.g., does sending a discount email cause more purchases?). What challenges do you face and what methods help?",
        "answer": """The core challenge: users who received the discount likely differ from those who didn't — **selection bias / confounding**. Naive comparison (treated mean − control mean) conflates the treatment effect with pre-existing differences.

**Key challenges:**
- **Confounders:** variables that affect both treatment assignment and outcome (e.g., high-value users receive more emails AND buy more)
- **Selection bias:** treated group is not a random sample of the population
- **Reverse causality:** outcome may influence treatment (user purchased → triggered a "thank you" email)

**Methods to estimate causal effects:**

**Propensity Score Matching (PSM):** estimate P(treatment | covariates) with logistic regression; match treated and control units with similar propensity scores. Reduces observed confounding but can't address unobserved confounders.

**Inverse Propensity Weighting (IPW):** weight each observation by 1/P(treatment=actual|X). Creates a pseudo-population where treatment is independent of X.

**Difference-in-Differences (DiD):** compare pre/post change in treated group vs. control group. Assumes parallel trends — both groups would have evolved similarly without treatment.

**Instrumental Variables (IV):** use a variable that affects treatment but not outcome directly (e.g., randomized email send timing). Requires a valid instrument — hard to find.

**Regression Discontinuity (RD):** exploit a sharp threshold in treatment assignment (e.g., discount for users with loyalty score > 50). Causal near the threshold.

**Gold standard:** run an A/B test. Use observational methods only when experimentation is impossible.""",
        "difficulty": "hard",
        "tags": ["statistics", "causal-inference", "confounding", "observational-study"],
        "code_snippet": None,
        "comparison_table": None,
        "reference_urls": []
    },
    {
        "topic_slug": "statistics",
        "question": "Explain the Central Limit Theorem. Why does it matter for production ML and data pipelines?",
        "answer": """**CLT:** Given a population with mean μ and variance σ², the sampling distribution of the sample mean x̄ approaches Normal(μ, σ²/n) as n → ∞, regardless of the population's distribution.

Practically: if you take samples of size n ≥ 30 (rule of thumb), the distribution of sample means is approximately normal even if the underlying data is skewed, bimodal, or non-normal.

**Why it matters in production:**

**A/B testing:** We compute sample means (CVR, revenue per user). CLT justifies using z-tests and t-tests even when individual events (click=0 or 1) are Bernoulli — the mean is approximately normal.

**Metric aggregation:** Aggregate metrics (average session length, average order value) obey CLT. Percentile metrics (P99 latency) do not — need bootstrap or empirical distribution.

**Statistical monitoring:** Alerting on metric drift uses z-score thresholds. Valid only because CLT applies to the running mean.

**Where CLT breaks:** heavy-tailed data (revenue with rare $10K purchases), very small n, dependent samples (user sessions are correlated within a user). In these cases, bootstrap or permutation tests are more reliable.

**Interview tip:** CLT justifies the normality assumption in many standard tests, but knowing *when it doesn't apply* (percentiles, heavy tails) is what separates senior from junior practitioners.""",
        "difficulty": "easy",
        "tags": ["statistics", "clt", "sampling", "ab-testing"],
        "code_snippet": None,
        "comparison_table": None,
        "reference_urls": []
    },
    {
        "topic_slug": "statistics",
        "question": "What is Bayes' theorem? Walk through how you'd apply it to evaluate a diagnostic test result.",
        "answer": """**Bayes' theorem:** P(H|E) = P(E|H) × P(H) / P(E)

- **P(H):** prior probability (base rate)
- **P(E|H):** likelihood (how probable is the evidence if H is true)
- **P(H|E):** posterior probability (updated belief after observing evidence)

**Diagnostic test example:**
- Disease prevalence (base rate): 1% of population
- Test sensitivity = P(positive | disease) = 95%
- Test specificity = P(negative | no disease) = 90% → False positive rate = 10%

**Question:** If a test is positive, what is the probability of actually having the disease?

P(disease | positive) = P(positive | disease) × P(disease) / P(positive)

P(positive) = P(pos|disease)×P(disease) + P(pos|no disease)×P(no disease)
= 0.95×0.01 + 0.10×0.99 = 0.0095 + 0.099 = 0.1085

P(disease | positive) = 0.0095 / 0.1085 ≈ **8.8%**

**Key insight:** Despite a 95% sensitive test, a positive result only means 8.8% chance of disease — because the base rate (1%) is low and the 10% FPR produces many false positives among the 99% healthy population.

**ML applications:** spam filtering (prior = spam rate), anomaly detection (prior = anomaly frequency), fraud (prior = fraud rate). Low base rates always suppress posterior probabilities dramatically.""",
        "difficulty": "easy",
        "tags": ["statistics", "bayesian", "bayes-theorem", "base-rate"],
        "code_snippet": None,
        "comparison_table": None,
        "reference_urls": []
    },
    {
        "topic_slug": "statistics",
        "question": "What is MLE vs MAP estimation? When does MAP reduce to MLE?",
        "answer": """**MLE (Maximum Likelihood Estimation):** find parameters θ that maximize P(data | θ). No prior — data alone drives the estimate.

θ_MLE = argmax P(X | θ)

**MAP (Maximum A Posteriori):** find θ that maximizes P(θ | data) ∝ P(data | θ) × P(θ). Incorporates a prior belief about θ.

θ_MAP = argmax [P(X | θ) × P(θ)]

**When MAP reduces to MLE:** when the prior is **uniform** (constant) over all θ — P(θ) = constant, so the posterior is proportional to the likelihood, and the argmax is identical.

**Regularization as MAP:**
- L2 regularization (Ridge) = MAP with a Gaussian prior on weights: P(w) ~ N(0, σ²). Penalizing ||w||² is equivalent to maximizing the posterior under this prior.
- L1 regularization (Lasso) = MAP with a Laplace prior on weights. Laplace's sharper peak at zero encourages sparsity.

**When to use each:**
- MLE: large data, no strong prior knowledge, want maximum likelihood
- MAP: small data, domain knowledge about parameter range, want regularization

**Interview tip:** framing regularization as MAP is elegant and shows understanding that regularization isn't a hack — it's Bayesian inference.""",
        "difficulty": "medium",
        "tags": ["statistics", "mle", "map", "bayesian", "regularization"],
        "code_snippet": None,
        "comparison_table": None,
        "reference_urls": []
    },
    {
        "topic_slug": "statistics",
        "question": "Your model's performance varies significantly across demographic groups (e.g., 90% accuracy for group A, 70% for group B). How do you analyze and address this disparity?",
        "answer": """This is a **model fairness / subgroup performance** problem. The analysis has three stages: measure, diagnose, fix.

**1. Measure rigorously:**
- Compute the performance gap with confidence intervals (bootstrap by group). Is the gap statistically significant given group sample sizes?
- Report multiple metrics per group: accuracy, F1, FPR, FNR — accuracy gap may mask worse false negative rates for a minority group.

**2. Diagnose causes:**
- **Data imbalance:** group B is underrepresented in training → model sees fewer examples and generalizes poorly.
- **Label noise:** ground truth may be biased (e.g., historical hiring decisions reflecting past discrimination).
- **Feature covariate shift:** feature distributions differ by group — model extrapolates.
- **Proxy discrimination:** a "neutral" feature (zip code, device type) acts as a proxy for a protected attribute.

**3. Mitigations:**
- **Resampling/reweighting:** oversample underrepresented group in training, or use instance weights to equalize group contribution.
- **Group-stratified evaluation:** set separate decision thresholds per group to equalize error rates (equalized odds).
- **Fairness constraints:** add demographic parity or equalized odds constraints to the training objective (e.g., via fairlearn).
- **Better data collection:** gather more labeled examples from underperforming group.

**Tradeoff:** fairness constraints typically reduce aggregate performance — explicitly communicate the accuracy-fairness tradeoff to stakeholders before making a decision.""",
        "difficulty": "medium",
        "tags": ["statistics", "fairness", "bias", "subgroup-analysis"],
        "code_snippet": None,
        "comparison_table": None,
        "reference_urls": []
    },

    # ── ML MODELS ───────────────────────────────────────────────────────────────
    {
        "topic_slug": "ml_models",
        "question": "Walk through the bias-variance tradeoff. How does it guide your choice between a linear model and a deep neural network?",
        "answer": """**Total expected error = Bias² + Variance + Irreducible noise**

- **Bias:** error from wrong assumptions — model is too simple to capture the true pattern (underfitting). Linear models have high bias on non-linear data.
- **Variance:** error from sensitivity to training data fluctuations — model memorizes noise (overfitting). Deep networks with unlimited capacity have high variance on small datasets.
- **Irreducible noise:** inherent randomness in the problem — no model can eliminate it.

**Tradeoff:** reducing bias typically increases variance and vice versa. The goal is the sweet spot that minimizes total error on unseen data.

**Practical implications:**

| Situation | Recommendation |
|---|---|
| Small dataset, simple relationship | Linear/logistic regression — low variance, tolerable bias |
| Large dataset, complex non-linear patterns | Neural network or gradient boosting — can absorb bias |
| Noisy labels | Simpler model — high-capacity models overfit to label noise |
| Many irrelevant features | Regularized model (Lasso, Ridge) — reduces variance |

**Diagnosing via learning curves:**
- High bias: both train and val error are high and plateau early → add model complexity
- High variance: low train error, high val error, large gap → add data, regularize, reduce model size

**Interview tip:** always frame model selection in terms of bias-variance, not "model X is better than model Y."  The right model depends on dataset size, signal-to-noise ratio, and feature structure.""",
        "difficulty": "medium",
        "tags": ["ml_models", "bias-variance", "model-selection", "regularization"],
        "code_snippet": None,
        "comparison_table": None,
        "reference_urls": []
    },
    {
        "topic_slug": "ml_models",
        "question": "Explain L1 vs L2 regularization. What does L1 do that L2 doesn't, and when do you use each?",
        "answer": """Both add a penalty to the loss function to discourage large weights.

**L2 (Ridge):** Loss + λ||w||² — penalizes squared magnitudes. Gradient: 2λw — shrinks all weights proportionally but rarely to exactly zero. Closed-form solution exists.

**L1 (Lasso):** Loss + λ||w||₁ — penalizes absolute magnitudes. Gradient: λ·sign(w) — constant penalty regardless of weight size, can push weights exactly to zero → produces **sparse solutions**.

**Why L1 produces sparsity:** geometrically, L1 constraint is a diamond (in 2D). The loss ellipses tend to hit the diamond at a corner (where one weight = 0). L2 constraint is a circle — corners don't exist, weights shrink but survive.

**When to use:**
- **L2:** many features all expected to contribute, no need for feature selection, differentiability matters (gradient-based solvers prefer L2)
- **L1:** high-dimensional sparse data (text, genomics), need interpretability through feature selection, want automatic identification of irrelevant features
- **Elastic Net (L1 + L2):** best of both — L1 for sparsity, L2 to handle correlated features (L1 alone picks one arbitrarily from a correlated group)

**As MAP:** L2 = Gaussian prior on weights; L1 = Laplace prior (sharper peak at 0, heavier tails → sparsity).

**Choosing λ:** cross-validate. Start with a log-scale grid (1e-5 to 1e2).""",
        "difficulty": "medium",
        "tags": ["ml_models", "regularization", "lasso", "ridge", "l1-l2"],
        "code_snippet": None,
        "comparison_table": {
            "headers": ["Property", "L1 (Lasso)", "L2 (Ridge)"],
            "rows": [
                ["Penalty", "λ·Σ|wᵢ|", "λ·Σwᵢ²"],
                ["Solutions", "Sparse (weights → 0)", "Small but non-zero"],
                ["Feature selection", "Yes (implicit)", "No"],
                ["Correlated features", "Picks one arbitrarily", "Distributes evenly"],
                ["Differentiable", "No (at 0)", "Yes"],
                ["MAP prior", "Laplace", "Gaussian"]
            ]
        },
        "reference_urls": []
    },
    {
        "topic_slug": "ml_models",
        "question": "How does gradient boosting work? What are the most important hyperparameters and how do you tune them?",
        "answer": """Gradient boosting builds an ensemble of **weak learners (shallow decision trees) sequentially**, where each new tree corrects the residual errors of the previous ensemble.

**Algorithm:**
1. Initialize with a constant prediction (e.g., mean of y)
2. Compute pseudo-residuals = negative gradient of loss w.r.t. current prediction
3. Fit a shallow tree to these residuals
4. Update: F(x) ← F(x) + η × tree(x) where η is the learning rate
5. Repeat until stopping criterion

The "gradient" in the name: we're performing gradient descent in function space — each tree step is a gradient descent step.

**Key hyperparameters:**

| Parameter | Effect | Tuning guide |
|---|---|---|
| `n_estimators` | Number of trees | More = better (with early stopping) |
| `learning_rate` (η) | Step size per tree | Lower → need more trees; typical 0.01–0.1 |
| `max_depth` | Tree depth | 3–6 for tabular; deeper = higher variance |
| `subsample` | Fraction of data per tree | 0.6–0.8 reduces variance (stochastic GB) |
| `colsample_bytree` | Fraction of features per tree | 0.6–0.8 reduces variance |
| `min_child_weight` | Min samples in a leaf | Higher = more regularization |
| `lambda/alpha` | L2/L1 on leaf weights | Regularizes leaf values directly |

**Tuning strategy:** fix `n_estimators=1000` with early stopping, tune `max_depth` and `learning_rate` first (most impactful), then `subsample/colsample_bytree`. Use Optuna or Bayesian search, not grid search.

**XGBoost vs LightGBM vs CatBoost:** LightGBM is fastest on large data (histogram-based splits, leaf-wise growth). CatBoost handles categorical features natively. XGBoost is most widely supported.""",
        "difficulty": "medium",
        "tags": ["ml_models", "gradient-boosting", "xgboost", "ensemble", "hyperparameter-tuning"],
        "code_snippet": None,
        "comparison_table": None,
        "reference_urls": []
    },
    {
        "topic_slug": "ml_models",
        "question": "Your model achieves 98% training accuracy but 65% validation accuracy. Walk through your debugging process.",
        "answer": """This is a classic **overfitting** pattern — high variance, low bias. Systematic debugging:

**Step 1 — Verify the split is clean:**
- Check for data leakage: is any information from the future or from validation in the training features?
- Are train/val splits randomized at the correct level? (e.g., split by user_id, not by row, if rows per user are correlated)
- Check for target leakage: does any feature encode the label?

**Step 2 — Analyze learning curves:**
Plot train vs. val error vs. training set size:
- If gap shrinks as n increases → model needs more data
- If gap stays constant → model is too complex for the task (reduce capacity)

**Step 3 — Regularization:**
- Add L2/dropout (if neural net), reduce `max_depth` (if tree), increase `min_samples_leaf`
- For gradient boosting: lower `learning_rate`, add `subsample` / `colsample_bytree`
- For neural nets: add dropout, weight decay, batch normalization

**Step 4 — Simplify the model:**
- Start with a linear baseline — if it also overfits, suspect data leakage
- Ablate features: does removing certain features close the gap?

**Step 5 — More data or augmentation:**
- Collect more training examples (most effective if step 1–3 don't help)
- Data augmentation for images, text, time series

**Most commonly missed:** data leakage at the feature engineering stage. If you compute "user's average CTR across all time" and include future clicks in that average, val accuracy will always be lower than training accuracy.""",
        "difficulty": "medium",
        "tags": ["ml_models", "overfitting", "debugging", "learning-curves", "data-leakage"],
        "code_snippet": None,
        "comparison_table": None,
        "reference_urls": []
    },
    {
        "topic_slug": "ml_models",
        "question": "How do you handle severely imbalanced classes (e.g., 1% positive rate)? What approaches don't work?",
        "answer": """**What doesn't work:** accuracy as a metric — predicting all negatives gives 99% accuracy on 1% positive data. Also, most default classification thresholds (0.5) are miscalibrated for imbalanced data.

**Approaches that work:**

**1. Evaluation metrics first:**
Use Precision, Recall, F1, AUROC, AUPRC. AUPRC (area under precision-recall curve) is the most informative for imbalanced data — AUROC can be optimistic because it averages over all thresholds including those producing mostly negatives.

**2. Threshold optimization:**
After training, choose the decision threshold that maximizes your cost-weighted F1 or minimizes expected cost — don't use 0.5.

**3. Class weighting:**
Set `class_weight='balanced'` in sklearn or `scale_pos_weight` in XGBoost. Equivalent to oversampling — computationally free and usually sufficient.

**4. Resampling:**
- Oversampling positives: duplicate or use SMOTE (synthetic minority oversampling — interpolates between minority neighbors)
- Undersampling negatives: randomly drop majority class. Faster training but discards information.
- SMOTE + Tomek links: oversample then clean borderline examples

**5. Ensemble methods (EasyEnsemble, BalancedBagging):**
Train multiple models on different undersampled subsets; ensemble predictions.

**What rarely helps:** oversampling then splitting (leakage) — always split first, then apply resampling only to training data.

**Production tip:** for very imbalanced problems (< 0.1%), anomaly detection framing (One-Class SVM, Isolation Forest, autoencoders) often outperforms classification.""",
        "difficulty": "medium",
        "tags": ["ml_models", "class-imbalance", "smote", "evaluation", "threshold"],
        "code_snippet": None,
        "comparison_table": None,
        "reference_urls": []
    },
    {
        "topic_slug": "ml_models",
        "question": "Explain backpropagation. What is the vanishing gradient problem and how do modern networks address it?",
        "answer": """**Backpropagation** is the algorithm for computing gradients of the loss with respect to all parameters in a neural network using the chain rule.

Forward pass: compute predictions layer by layer.
Backward pass: starting from the loss, apply chain rule layer by layer back to the inputs:
∂L/∂w_l = (∂L/∂z_{l+1}) × (∂z_{l+1}/∂z_l) × (∂z_l/∂w_l)

Accumulated gradients update weights via gradient descent.

**Vanishing gradient:** in deep networks, gradients are products of many Jacobians (one per layer). If each Jacobian has entries < 1 (common with sigmoid/tanh activations), the product approaches zero exponentially with depth → early layers receive near-zero gradients and learn nothing.

**Solutions:**

**1. ReLU activation:** f(x) = max(0, x). Gradient is 1 for x > 0 — doesn't saturate. Mostly solves vanishing gradient in feed-forward networks.

**2. Residual connections (ResNets):** y = F(x) + x. The identity shortcut creates a "gradient highway" — gradients flow directly through the skip connection undiminished.

**3. Batch Normalization:** normalizes layer inputs to zero mean, unit variance. Keeps activations in the non-saturating range; reduces internal covariate shift.

**4. Better initialization (He, Xavier):** scale initial weights to keep variance stable across layers. He init (for ReLU): w ~ N(0, 2/fan_in).

**5. Gradient clipping:** caps gradient norm to a threshold. Addresses the opposite problem — *exploding* gradients in RNNs/LSTMs.

**Transformers:** use LayerNorm + residual connections in every block, making very deep models trainable.""",
        "difficulty": "medium",
        "tags": ["ml_models", "backpropagation", "vanishing-gradient", "relu", "deep-learning"],
        "code_snippet": None,
        "comparison_table": None,
        "reference_urls": []
    },
    {
        "topic_slug": "ml_models",
        "question": "What is model calibration? How do you diagnose poor calibration and fix it?",
        "answer": """A model is **well-calibrated** if its predicted probabilities match empirical frequencies: when the model says 80% probability, about 80% of those cases should be positive.

**Why calibration matters:** downstream decisions (threshold setting, expected value calculations, cost-sensitive classification) require probabilities, not just rankings. A model with good AUROC can be poorly calibrated.

**Diagnosis: reliability diagram (calibration plot)**
- Bucket predictions into bins (e.g., [0–0.1], [0.1–0.2], ...)
- Plot mean predicted probability vs. actual positive fraction per bin
- Well-calibrated: points fall on the diagonal (y=x)
- Overconfident: curve bows below diagonal (model says 90%, actually 70%)
- Underconfident: curve bows above diagonal

**Quantitative measure:** Expected Calibration Error (ECE) = weighted average of |predicted − actual| per bin.

**Common miscalibration patterns:**
- Random Forests: systematically overconfident (probabilities cluster around 0.5 and extremes are too extreme)
- Gradient boosting: often overconfident
- Naive Bayes: underconfident (assumes feature independence, dampens extreme probabilities)

**Fixes:**

**Platt Scaling:** fit a logistic regression on top of the model's raw scores using a holdout calibration set. Works well for sigmoid-shaped miscalibration.

**Isotonic Regression:** non-parametric monotonic transformation fitted to the calibration set. More flexible than Platt but needs more data.

**Temperature Scaling** (deep learning): divide logits by a scalar T. T > 1 softens probabilities (reduces overconfidence). T is tuned on a calibration set.

**Rule:** always fit calibration transformations on a *separate held-out set* — not the training set or test set.""",
        "difficulty": "medium",
        "tags": ["ml_models", "calibration", "probability-estimation", "platt-scaling"],
        "code_snippet": None,
        "comparison_table": None,
        "reference_urls": []
    },
    {
        "topic_slug": "ml_models",
        "question": "Explain PCA. How do you decide how many principal components to keep?",
        "answer": """**PCA (Principal Component Analysis)** finds a new coordinate system where the axes (principal components) are ordered by the amount of variance they explain. The first PC explains the most variance, each subsequent PC explains less, and all PCs are orthogonal.

**Algorithm:**
1. Standardize features (subtract mean, divide by std — mandatory if features have different scales)
2. Compute the covariance matrix Σ
3. Eigen-decompose Σ → eigenvalues λ_i (variance explained) and eigenvectors (PC directions)
4. Sort by λ descending; project data onto top k eigenvectors

**How many components to keep:**

**1. Explained variance threshold:** keep the minimum k such that Σλ_1..k / Σλ_all ≥ 0.95 (or 0.99). Most common approach.

**2. Scree plot / elbow method:** plot eigenvalues vs. component index; keep components before the "elbow" where the curve flattens.

**3. Task-specific:** downstream model performance often stabilizes before 95% variance threshold — tune k as a hyperparameter.

**When to use PCA:**
- Reducing dimensionality before slow algorithms (SVM, KNN)
- Removing multicollinearity before regression
- Visualization (reduce to 2–3 components)
- Denoising (low-rank reconstruction)

**PCA limitations:**
- Only captures linear structure — use t-SNE or UMAP for non-linear structure
- Components are hard to interpret (linear combinations of features)
- Sensitive to outliers (they inflate variance)
- Not suitable as a feature engineering step when interpretability is needed""",
        "difficulty": "easy",
        "tags": ["ml_models", "pca", "dimensionality-reduction", "unsupervised"],
        "code_snippet": None,
        "comparison_table": None,
        "reference_urls": []
    },
    {
        "topic_slug": "ml_models",
        "question": "Compare Random Forest and Gradient Boosting. For a new tabular ML problem, which do you start with?",
        "answer": """Both are tree ensembles but differ in how trees are built:

**Random Forest (Bagging):** trains many deep trees **independently** on bootstrap samples + random feature subsets, then averages. Trees have high variance individually; averaging reduces it. Parallelizable.

**Gradient Boosting:** trains shallow trees **sequentially**, each correcting the previous ensemble's errors. Trees have lower variance individually; boosting reduces bias. Not parallelizable (sequential by design), but within-tree operations are parallelized (XGBoost/LGBM).

**Performance comparison:**
- Gradient boosting typically outperforms RF on structured/tabular data — it's the dominant approach in Kaggle tabular competitions
- RF is more robust to noisy hyperparameters — works well out of the box with fewer tuning
- RF handles missing values poorly; LightGBM has native missing value support

**When to prefer Random Forest:**
- Need fast prototyping without tuning
- Very noisy labels (boosting overfits to noise more aggressively)
- Parallelism matters (RF trains all trees simultaneously)

**Recommendation for a new tabular problem:**
1. Start with LightGBM/XGBoost — best expected performance on tabular data
2. Use early stopping (`early_stopping_rounds=50`) to avoid overfitting
3. Fit an RF as a quick baseline to compare; if RF matches LGBM, invest in simpler model
4. Only go to neural networks (TabNet, FT-Transformer) if boosting plateaus and you have > 100K rows""",
        "difficulty": "medium",
        "tags": ["ml_models", "random-forest", "gradient-boosting", "ensemble", "tabular"],
        "code_snippet": None,
        "comparison_table": {
            "headers": ["Property", "Random Forest", "Gradient Boosting"],
            "rows": [
                ["Training", "Parallel (independent trees)", "Sequential (corrective trees)"],
                ["Tree depth", "Deep (low bias, high variance per tree)", "Shallow (low variance, targeted bias)"],
                ["Hyperparameter sensitivity", "Low", "High"],
                ["Overfitting risk", "Low", "Higher (needs careful tuning)"],
                ["Speed", "Fast (parallelizable)", "Slower but LGBM is optimized"],
                ["Best for", "Quick baseline, noisy data", "Production accuracy on tabular data"]
            ]
        },
        "reference_urls": []
    },
    {
        "topic_slug": "ml_models",
        "question": "Your deployed model's performance degrades over 3 months. Walk through your monitoring and retraining strategy.",
        "answer": """Model degradation is called **model drift** — incoming data distribution diverges from training distribution. Two types:

**1. Data drift (covariate shift):** input feature distributions change. Example: user demographics shift after a new product launch. Model still targets the right relationship but inputs are out-of-distribution.

**2. Concept drift:** the relationship between inputs and labels changes. Example: fraud patterns evolve; a feature that predicted fraud in 2023 no longer does.

**Monitoring strategy:**

- **Data drift:** monitor feature distribution statistics (mean, std, percentiles) and flag when PSI (Population Stability Index) > 0.2 or KL divergence exceeds threshold. Tools: Evidently, Whylogs, Arize.
- **Label drift:** monitor prediction distribution (proxy for label distribution if labels are delayed). Alert when predicted positive rate shifts significantly.
- **Model performance:** if you have ground truth (even delayed), monitor AUROC/precision/recall on a rolling window. Set alert thresholds.

**Retraining strategy:**

- **Scheduled retraining:** retrain on a fixed cadence (weekly, monthly). Simple, predictable.
- **Triggered retraining:** retrain when drift metrics exceed threshold. More efficient.
- **Continuous training:** stream new data into training incrementally (online learning). Complex but minimizes staleness.

**Deployment:** use a **shadow deployment** — run new model alongside old, compare metrics on live traffic before promoting. Never replace production model without validation period.""",
        "difficulty": "hard",
        "tags": ["ml_models", "model-drift", "monitoring", "retraining", "production"],
        "code_snippet": None,
        "comparison_table": None,
        "reference_urls": []
    },
    {
        "topic_slug": "ml_models",
        "question": "What are SHAP values? When is a tree model's built-in feature importance misleading?",
        "answer": """**SHAP (SHapley Additive exPlanations)** assigns each feature a contribution value to a specific prediction based on Shapley values from cooperative game theory. For each prediction, SHAP answers: "how much did feature X push this prediction above or below the baseline (expected prediction)?"

**Properties:**
- **Local:** explains individual predictions, not just global importance
- **Consistent:** if a feature has more impact in the model, its SHAP value is higher (not always true for built-in importance)
- **Additive:** sum of all SHAP values = prediction − baseline

**When built-in feature importance is misleading:**

**1. Impurity-based (Gini/entropy) importance in sklearn Random Forest:**
- Biased toward high-cardinality features (many unique values) because they get more split opportunities
- A random ID column can appear as an important feature

**2. Permutation importance:**
- Underestimates correlated features: permuting X1 while X2 is correlated with X1 doesn't fully break X1's contribution
- SHAP handles correlated features better

**3. Gradient boosting feature importance:**
- Based on split count or split gain — doesn't tell you *direction* of the effect
- A feature used many times with small improvements may look more important than one used rarely with large improvement

**SHAP advantages over built-in importance:**
- Shows direction (positive/negative effect) via SHAP value sign
- Shows interaction effects with SHAP interaction values
- Works for any model (not just trees; uses KernelSHAP for black boxes)

**When to use:** always for model debugging, regulatory explanations, or feature selection. Use built-in importance only for quick gut-checks during EDA.""",
        "difficulty": "medium",
        "tags": ["ml_models", "shap", "feature-importance", "interpretability", "explainability"],
        "code_snippet": None,
        "comparison_table": None,
        "reference_urls": []
    },
    {
        "topic_slug": "ml_models",
        "question": "How do you select features? Compare filter, wrapper, and embedded methods.",
        "answer": """**Filter methods:** score each feature independently of the model using a statistical criterion, then select top-k.
- Examples: correlation with target, mutual information, chi-square test (categorical), ANOVA F-score
- Fast (O(features)), model-agnostic, but ignores feature interactions
- Use for: initial dimensionality reduction, removing clearly irrelevant features

**Wrapper methods:** train a model on different feature subsets and select the subset with best validation performance.
- Examples: forward selection (add features one by one), backward elimination (remove one by one), RFE (Recursive Feature Elimination)
- Captures feature interactions but expensive — O(features²) model fits for forward/backward
- Use for: small/medium feature sets where accuracy is critical

**Embedded methods:** feature selection happens *during* model training.
- Examples: L1 regularization (Lasso) drives weights to 0, tree-based models rank features by split importance
- Balance between filter (speed) and wrapper (interaction awareness)
- Use for: most production scenarios — train with L1/LGBM, select features with non-zero importance

**Practical workflow:**
1. Remove near-zero variance features and features with > 50% missing (filter)
2. Remove highly correlated pairs (keep one from each pair with >0.95 correlation)
3. Fit LGBM and remove zero-importance features (embedded)
4. Optionally: run RFE or permutation importance for fine-grained selection

**Leakage warning:** always do feature selection on training data only, not on the full dataset — selecting features based on their correlation with the target across train+test is a form of data leakage.""",
        "difficulty": "medium",
        "tags": ["ml_models", "feature-selection", "filter-methods", "wrapper", "embedded"],
        "code_snippet": None,
        "comparison_table": {
            "headers": ["Method", "Speed", "Captures interactions", "Model dependency"],
            "rows": [
                ["Filter (correlation, MI)", "Fast O(d)", "No", "None"],
                ["Wrapper (RFE, forward)", "Slow O(d²)", "Yes", "Model-specific"],
                ["Embedded (L1, tree importance)", "Medium", "Partially", "Model-specific"]
            ]
        },
        "reference_urls": []
    },
]


def main():
    data = json.loads(QA_FILE.read_text())
    existing = {q["question"] for q in data}
    added = 0
    for q in NEW_QUESTIONS:
        if q["question"] in existing:
            print(f"  SKIP: {q['question'][:70]}")
            continue
        data.append(q)
        existing.add(q["question"])
        added += 1
        print(f"  ADD [{q['topic_slug']}]: {q['question'][:70]}")
    QA_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    print(f"\nDone: +{added} questions. Total: {len(data)}")


if __name__ == "__main__":
    main()
