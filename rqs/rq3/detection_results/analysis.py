import pandas as pd
from sklearn.metrics import precision_score, recall_score, f1_score, accuracy_score, confusion_matrix

df = pd.read_csv('results_summary.csv')

MODELS = [
    "meta-llama/llama-3.3-70b-instruct", 
    "x-ai/grok-4-fast", 
    "openai/gpt-4o-mini", 
]

results = []

for model in MODELS:
    model_data = df[df['model'] == model]
    
    if len(model_data) == 0:
        print(f"Warning: No data found for {model}")
        continue
    
    y_true = model_data['class'].values
    y_pred = model_data['predicted'].values
    
    pos_label = 'nonportable'
    
    precision = precision_score(y_true, y_pred, pos_label=pos_label, zero_division=0)
    recall = recall_score(y_true, y_pred, pos_label=pos_label, zero_division=0)
    f1 = f1_score(y_true, y_pred, pos_label=pos_label, zero_division=0)
    accuracy = accuracy_score(y_true, y_pred)
    
    results.append({
        'Model': model.split('/')[-1],
        'Precision': precision,
        'Recall': recall,
        'F1-Score': f1,
        'Accuracy': accuracy,
        'Samples': len(model_data)
    })

results_df = pd.DataFrame(results)

print("\n" + "="*80)
print("PERFORMANCE METRICS BY MODEL (NonPort = Positive)")
print("="*80 + "\n")

print("LaTeX Format:")
print("-" * 80)
print(results_df.to_latex(index=False, float_format="%.3f"))

print("\nMarkdown Format:")
print("-" * 80)
print(results_df.to_markdown(index=False, floatfmt=".3f"))

print("\nSimple Table:")
print("-" * 80)
print(results_df.to_string(index=False, float_format=lambda x: f'{x:.3f}'))

print("\n" + "="*80)
print("COMPARATIVE ANALYSIS")
print("="*80)
print(f"\nBest Precision: {results_df.loc[results_df['Precision'].idxmax(), 'Model']} "
      f"({results_df['Precision'].max():.3f})")
print(f"Best Recall: {results_df.loc[results_df['Recall'].idxmax(), 'Model']} "
      f"({results_df['Recall'].max():.3f})")
print(f"Best F1-Score: {results_df.loc[results_df['F1-Score'].idxmax(), 'Model']} "
      f"({results_df['F1-Score'].max():.3f})")
print(f"Best Accuracy: {results_df.loc[results_df['Accuracy'].idxmax(), 'Model']} "
      f"({results_df['Accuracy'].max():.3f})")

print("\n" + "="*80)
print("CONFUSION MATRICES (NonPort = Positive)")
print("="*80)

for model in MODELS:
    model_data = df[df['model'] == model]
    
    if len(model_data) == 0:
        continue
    
    y_true = model_data['class'].values
    y_pred = model_data['predicted'].values
    
    cm = confusion_matrix(y_true, y_pred, labels=['portable', 'nonportable'])
    
    print(f"\n{model.split('/')[-1]}:")
    print(f"                 Predicted")
    print(f"               Port  NonPort")
    print(f"Actual Port    {cm[0][0]:4d}    {cm[0][1]:4d}")
    print(f"       NonPort {cm[1][0]:4d}    {cm[1][1]:4d}")
