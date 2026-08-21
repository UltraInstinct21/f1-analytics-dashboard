"""
2026 Season Projection Engine
==============================
Generates simulated standings and round-by-round race results for the 2026 F1 season.
"""

import random


def predict_full_season(seed: int = 2026) -> dict:
    """
    Generates a simulated 2026 F1 Season Projection.
    Returns a dictionary containing 'standings' and 'race_results'.
    """
    drivers = [
        {"code": "VER", "name": "Max Verstappen", "team": "Red Bull Racing", "base_pace": 98},
        {"code": "NOR", "name": "Lando Norris", "team": "McLaren", "base_pace": 96},
        {"code": "PIA", "name": "Oscar Piastri", "team": "McLaren", "base_pace": 95},
        {"code": "HAM", "name": "Lewis Hamilton", "team": "Ferrari", "base_pace": 97},
        {"code": "LEC", "name": "Charles Leclerc", "team": "Ferrari", "base_pace": 96},
        {"code": "RUS", "name": "George Russell", "team": "Mercedes", "base_pace": 94},
        {"code": "ANT", "name": "Kimi Antonelli", "team": "Mercedes", "base_pace": 92},
        {"code": "SAI", "name": "Carlos Sainz", "team": "Williams", "base_pace": 93},
        {"code": "ALB", "name": "Alexander Albon", "team": "Williams", "base_pace": 91},
        {"code": "TSU", "name": "Yuki Tsunoda", "team": "Red Bull Racing", "base_pace": 90},
        {"code": "HUL", "name": "Nico Hulkenberg", "team": "Sauber", "base_pace": 89},
        {"code": "BOR", "name": "Gabriel Bortoleto", "team": "Sauber", "base_pace": 87},
        {"code": "ALO", "name": "Fernando Alonso", "team": "Aston Martin", "base_pace": 92},
        {"code": "STR", "name": "Lance Stroll", "team": "Aston Martin", "base_pace": 88},
        {"code": "GAS", "name": "Pierre Gasly", "team": "Alpine", "base_pace": 89},
        {"code": "DOO", "name": "Jack Doohan", "team": "Alpine", "base_pace": 86},
        {"code": "OCO", "name": "Esteban Ocon", "team": "Haas F1 Team", "base_pace": 88},
        {"code": "BEA", "name": "Oliver Bearman", "team": "Haas F1 Team", "base_pace": 87},
        {"code": "LAW", "name": "Liam Lawson", "team": "Racing Bulls", "base_pace": 89},
        {"code": "HAD", "name": "Isack Hadjar", "team": "Racing Bulls", "base_pace": 85},
        {"code": "BOT", "name": "Valtteri Bottas", "team": "Cadillac", "base_pace": 86},
        {"code": "PER", "name": "Sergio Perez", "team": "Cadillac", "base_pace": 85},
    ]

    calendar = [
        "Australian Grand Prix", "Chinese Grand Prix", "Japanese Grand Prix",
        "Bahrain Grand Prix", "Saudi Arabian Grand Prix", "Miami Grand Prix",
        "Canadian Grand Prix", "Monaco Grand Prix", "Spanish Grand Prix (Barcelona)",
        "Austrian Grand Prix", "British Grand Prix", "Belgian Grand Prix",
        "Hungarian Grand Prix", "Dutch Grand Prix", "Italian Grand Prix",
        "Spanish Grand Prix (Madrid)", "Azerbaijan Grand Prix", "Singapore Grand Prix",
        "United States Grand Prix", "Mexico City Grand Prix", "São Paulo Grand Prix",
        "Las Vegas Grand Prix", "Qatar Grand Prix", "Abu Dhabi Grand Prix"
    ]

    points_map = {1: 25, 2: 18, 3: 15, 4: 12, 5: 10, 6: 8, 7: 6, 8: 4, 9: 2, 10: 1}

    standings_data = {
        d["code"]: {"points": 0, "wins": 0, "podiums": 0, "name": d["name"], "team": d["team"]}
        for d in drivers
    }
    race_results = []

    rng = random.Random(seed)

    for i, race in enumerate(calendar):
        race_performance = []
        for d in drivers:
            noise = rng.uniform(-5, 5)
            score = d["base_pace"] + noise
            race_performance.append((d["code"], score))

        race_performance.sort(key=lambda x: x[1], reverse=True)
        winner_code = race_performance[0][0]
        standings_data[winner_code]["wins"] += 1

        for pos, (code, score) in enumerate(race_performance[:10], 1):
            pts = points_map.get(pos, 0)
            standings_data[code]["points"] += pts
            if pos <= 3:
                standings_data[code]["podiums"] += 1

        race_results.append({
            "Round": i + 1,
            "Race": race,
            "Winner": standings_data[winner_code]["name"],
            "Team": standings_data[winner_code]["team"],
        })

    final_standings = []
    for code, data in standings_data.items():
        final_standings.append({
            "code": code,
            "name": data["name"],
            "team": data["team"],
            "points": data["points"],
            "wins": data["wins"],
            "podiums": data["podiums"],
        })

    final_standings.sort(key=lambda x: x["points"], reverse=True)

    return {
        "standings": final_standings,
        "race_results": race_results,
    }
