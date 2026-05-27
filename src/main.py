# src/main.py
from utils import calculate_split

def start_app() -> None:
    print("System booting up...")
    data_points = 0
    total_score = 500
    
    # Passing 0 items will trigger a crash inside utils.py
    print(f"Calculating split for {total_score} points across {data_points} items...")
    result = calculate_split(total_score, data_points)
    print(f"Result: {result}")

if __name__ == "__main__":
    start_app()
