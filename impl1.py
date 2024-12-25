import random
import matplotlib.pyplot as plt

# Define strategy variables outside the program
BANK_THRESHOLD1 = 300  # Minimum score to bank points after round 3
BANK_THRESHOLD2 = 600
SIMULATIONS = 1000  # Set the number of simulations
OUTLIER_MULTIPLE = 3  # Define the multiple to identify outliers


def roll_dice():
    """Simulates rolling two six-sided dice and returns their sum and individual rolls."""
    die1 = random.randint(1, 6)
    die2 = random.randint(1, 6)
    return die1 + die2, die1, die2


def simulate_game():
    rounds = 20
    cumulative_highest_score = 0
    my_score = 0

    for round_number in range(1, rounds + 1):
        round_score = 0
        roll_count = 0
        max_round_score = 0
        has_banked = False  # Track if points have been banked in the round

        while True:
            roll_count += 1
            roll, die1, die2 = roll_dice()

            if roll == 7:
                if roll_count <= 3:
                    round_score += (
                        70  # Add 70 points for rolling a 7 in the first 3 rolls
                    )
                else:
                    break
            elif die1 == die2:
                if roll_count <= 3:
                    round_score += roll  # Add the sum of the dice in the first 3 rolls
                else:
                    round_score *= 2  # Add only the roll value after the first 3 rolls
            else:
                round_score += roll

            # Update maximum score before a 7 is rolled
            max_round_score = max(max_round_score, round_score)

            # Check strategy: Bank points only after round 3 and if round_score >= BANK_THRESHOLD
            if round_number <= 10:
                if roll_count > 2 and round_score >= BANK_THRESHOLD1 and not has_banked:
                    my_score += round_score
                    has_banked = True
            else:
                if roll_count > 2 and round_score >= BANK_THRESHOLD2 and not has_banked:
                    my_score += round_score
                    has_banked = True

        # Add the maximum score achieved before rolling a 7 to the cumulative highest score.
        cumulative_highest_score += max_round_score

    return cumulative_highest_score, my_score


def simulate_multiple_games(simulations):
    total_cumulative_highest_score = 0
    total_my_score = 0
    percentage_scores = []  # Track the percentage of points achieved in each simulation
    cumulative_highest_scores_per_game = (
        []
    )  # Track the highest possible scores per game
    my_scores_per_game = []  # Track my scores per game

    for _ in range(simulations):
        cumulative_highest_score, my_score = simulate_game()
        cumulative_highest_scores_per_game.append(cumulative_highest_score)
        my_scores_per_game.append(my_score)

    average_cumulative_highest_score = (
        sum(cumulative_highest_scores_per_game) / simulations
    )

    # Filter out outliers
    filtered_highest_scores = []
    filtered_my_scores = []
    for chs, ms in zip(cumulative_highest_scores_per_game, my_scores_per_game):
        if chs <= OUTLIER_MULTIPLE * average_cumulative_highest_score:
            filtered_highest_scores.append(chs)
            filtered_my_scores.append(ms)

    total_cumulative_highest_score = sum(filtered_highest_scores)
    total_my_score = sum(filtered_my_scores)
    simulations_after_filter = len(filtered_highest_scores)

    average_cumulative_highest_score = (
        total_cumulative_highest_score / simulations_after_filter
    )
    average_my_score = total_my_score / simulations_after_filter
    percentage_scores = [
        (ms / chs) * 100 if chs > 0 else 0
        for chs, ms in zip(filtered_highest_scores, filtered_my_scores)
    ]
    average_percentage_of_total_possible = (
        sum(percentage_scores) / simulations_after_filter
    )
    average_percentage_of_highest_score = (
        average_my_score / average_cumulative_highest_score
    ) * 100

    print("\nSimulation Results:")
    print(
        f"  Total Cumulative Highest Score Across Simulations: {total_cumulative_highest_score}"
    )
    print(f"  Total My Score Across Simulations: {total_my_score}")
    print(f"  Average Cumulative Highest Score: {average_cumulative_highest_score}")
    print(f"  Average My Score: {average_my_score}")
    print(
        f"  Average Percentage of Total Possible Each Game: {average_percentage_of_total_possible:.2f}%"
    )
    print(
        f"  Average Percentage of Total Cumulative Highest Score: {average_percentage_of_highest_score:.2f}%"
    )

    # Generate the second graph
    plt.figure(figsize=(20, 10))
    plt.plot(
        range(1, simulations_after_filter + 1),
        filtered_highest_scores,
        label="Total Possible Points Per Game",
        color="r",
    )
    plt.plot(
        range(1, simulations_after_filter + 1),
        filtered_my_scores,
        label="My Points Per Game",
        color="g",
    )
    plt.title("Total Possible Points vs My Points Per Game (Filtered)")
    plt.xlabel("Simulation Number (Filtered)")
    plt.ylabel("Points")
    plt.legend()
    plt.grid(True)
    plt.show()


# Simulate the game
if __name__ == "__main__":
    simulate_multiple_games(SIMULATIONS)
