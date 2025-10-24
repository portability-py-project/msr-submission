from pathlib import Path

def process_files(base_dir: str):

    base_path = Path(base_dir)
    input_dir = base_path / "input"
    output_dir = base_path / "output"

    output_dir.mkdir(parents=True, exist_ok=True)

    for txt_file in input_dir.glob("*.txt"):
        print(f"Processing {txt_file.name}...")

        with txt_file.open("r", encoding="utf-8") as f:
            content = f.readlines()

        processed = [line.strip() for line in content if line.strip()]

        output_file = output_dir / f"processed_{txt_file.name}"
        with output_file.open("w", encoding="utf-8") as f:
            for line in processed:
                f.write(line + "\n")

        print(f"Saved {output_file}")


process_files("my_project_data")
