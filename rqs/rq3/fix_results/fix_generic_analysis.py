import pandas as pd

print("🔹 Reading CSV file with fix results...\n")
df = pd.read_csv("fix_generic_summary.csv")

print("Data preview:")
print(df.head(), "\n")

df["fixed_correctly"] = df["fixed_correctly"].str.strip().str.upper()

total = len(df)
total_fixed = (df["fixed_correctly"] == "YES").sum()
accuracy = total_fixed / total

print("=== General Statistics ===")
print(f"Total samples: {total}")
print(f"Total correctly fixed: {total_fixed}")
print(f"Overall accuracy rate: {accuracy:.2%}\n")

print("=== Results by model ===")
results_by_model = (
    df.groupby("model")["fixed_correctly"]
    .value_counts()
    .unstack(fill_value=0)
    .reset_index()
)

results_by_model["Total"] = results_by_model["YES"] + results_by_model["NO"]
results_by_model["Accuracy"] = results_by_model["YES"] / results_by_model["Total"]

results_by_model = results_by_model.sort_values("Accuracy", ascending=False)

print(results_by_model, "\n")

print("=== Model ranking by accuracy rate ===")
for _, row in results_by_model.iterrows():
    print(f"{row['model']}: {row['Accuracy']:.2%} ({int(row['YES'])}/{int(row['Total'])} correct)")


