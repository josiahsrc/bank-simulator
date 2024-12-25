import random
import argparse
import matplotlib.pyplot as plt
import logging
import signal
import sys
import statistics

log = logging.getLogger(__name__)


def signal_handler(sig, frame):
    print("\nExiting gracefully...")
    sys.exit(0)


class GameState:
    def __init__(self):
        self.bank = 0
        self.dice1 = 0
        self.dice2 = 0
        self.round = 0

    def sum(self):
        return self.dice1 + self.dice2

    def advance(self) -> bool:
        self.round += 1

        self.dice1 = random.randint(1, 6)
        self.dice2 = random.randint(1, 6)

        advanced = True
        added = self.sum()
        if self.round <= 3:
            if added == 7:
                self.bank += 70
            else:
                self.bank += added
        elif added == 7:
            advanced = False
        elif self.dice1 == self.dice2:
            self.bank *= 2
        else:
            self.bank += added

        return advanced


class Strategy:
    def __init__(self, name):
        self.name = name
        pass

    def will_bank(self, state: GameState):
        pass


class BankAtAConstant(Strategy):
    def __init__(self, name, bank_at):
        self.bank_at = bank_at
        super().__init__(name)

    def will_bank(self, state):
        return state.bank >= self.bank_at


def main():
    signal.signal(signal.SIGINT, signal_handler)
    parser = argparse.ArgumentParser()
    parser.add_argument("--rounds", type=int, default=20)
    parser.add_argument("--iterations", type=int, default=1000)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.INFO)

    strategies = []
    for v in range(50):
        value = v * 200
        strategies.append(BankAtAConstant(f"Bank at {value}", value))

    strategy_names = [s.name for s in strategies]

    results = {}
    wins = {}
    for strategy in strategies:
        results[strategy.name] = []
        wins[strategy.name] = 0

    for i in range(args.iterations):
        game = GameState()
        log.info(f"Starting game {i}")

        scores = {}
        for strategy in strategies:
            scores[strategy.name] = 0

        for r in range(args.rounds):
            game.bank = 0
            game.round = 0

            banked_players = set()
            log.info(f"Starting round {r}")

            while game.advance():
                log.info(f"Round {r} bank: {game.bank}")
                for strategy in strategies:
                    if strategy in banked_players:
                        continue

                    should_bank = strategy.will_bank(game)
                    if should_bank:
                        scores[strategy.name] += game.bank
                        banked_players.add(strategy)
                        log.info(f"{strategy.name} banked {game.bank}")

        for strategy in strategies:
            results[strategy.name].append(scores[strategy.name])
            log.info(f"{strategy.name} scored {scores[strategy.name]}")

        # determine the winner
        winner = max(scores, key=scores.get)
        wins[winner] += 1

    average_results = {}
    for strategy in strategies:
        average_results[strategy.name] = sum(results[strategy.name]) / args.iterations
    log.info(f"Results: {average_results}")

    stddev_results = {}
    for strategy in strategies:
        stddev_results[strategy.name] = statistics.stdev(results[strategy.name])

    # histogram
    fig, axes = plt.subplots(5, 10, figsize=(20, 10), sharex=True, sharey=True)
    axes = axes.flatten()
    for i, (name, scores) in enumerate(results.items()):
        axes[i].hist(scores, bins=20)
        axes[i].set_title(name)
    plt.tight_layout()
    plt.savefig("results-hist.png", bbox_inches="tight", dpi=300)

    # std dev
    plt.figure(figsize=(15, 8))
    plt.barh(list(stddev_results.keys()), list(stddev_results.values()))
    plt.xlabel("Standard Deviation")
    plt.ylabel("Strategy")
    plt.title("Standard Deviation of Scores by Strategy")
    plt.tight_layout()
    plt.savefig("results-stddev.png", bbox_inches="tight", dpi=300)

    # bar chart of wins
    plt.figure(figsize=(15, 8))
    plt.barh(strategy_names, [wins.get(name, 0) for name in strategy_names])
    plt.xlabel("Wins")
    plt.ylabel("Strategy")
    plt.title("Wins by Strategy")
    plt.tight_layout()
    plt.savefig("results-wins.png", bbox_inches="tight", dpi=300)

    # render the average results as a bar chart. names on the left, scores across the bottom
    plt.figure(figsize=(15, 8))
    plt.barh(list(average_results.keys()), list(average_results.values()))
    plt.xlabel("Average Score")
    plt.ylabel("Strategy")
    plt.title("Average Scores by Strategy")
    plt.tight_layout()
    plt.savefig("results-avg-score.png", bbox_inches="tight", dpi=300)


if __name__ == "__main__":
    main()
