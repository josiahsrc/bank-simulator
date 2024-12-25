import random
import argparse
import matplotlib.pyplot as plt
import logging
import signal
import sys
import statistics
import numpy as np

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
        self.scores = {}
        self.strategies = []
        self.rounds = 0

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
            log.info("Rolled 7")
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


class BankAfterRound(Strategy):
    def __init__(self, name, round):
        self.round = round
        super().__init__(name)

    def will_bank(self, state):
        return state.round >= self.round


class ConstantBank(Strategy):
    def __init__(self, name, bank_at):
        self.bank_at = bank_at
        super().__init__(name)

    def will_bank(self, state):
        return state.bank >= self.bank_at


class RoundBasedConstantBank(Strategy):
    def __init__(self, name, values):
        """
        values: [[round, bank_at], [round, bank_at], ...]
        if less that round, bank it
        """
        self.values = values
        super().__init__(name)

    def will_bank(self, state):
        for round, bank_at in self.values:
            if state.round <= round:
                return state.bank >= bank_at

        last_value = self.values[-1][1]
        return state.bank >= last_value


class SmartBank(Strategy):
    def __init__(
        self, name, lead_bank=500, catch_up_bank=300, offset=100, divide_mult=1
    ):
        self.lead_bank = lead_bank
        self.catch_up_bank = catch_up_bank
        self.offset = offset
        self.divide_mult = divide_mult
        super().__init__(name)

    def will_bank(self, state):
        my_score = state.scores.get(self.name, 0)
        highest_other_score = 0
        for strategy in state.strategies:
            if strategy.name == self.name:
                continue
            highest_other_score = max(
                highest_other_score, state.scores.get(strategy.name, 0)
            )

        if my_score < highest_other_score + self.offset:
            rounds_left = max((state.rounds - state.round) * self.divide_mult, 1)
            difference = highest_other_score - my_score
            return state.bank >= difference / rounds_left + self.catch_up_bank

        return state.bank >= self.lead_bank


def main():
    signal.signal(signal.SIGINT, signal_handler)
    parser = argparse.ArgumentParser()
    parser.add_argument("--rounds", type=int, default=20)
    parser.add_argument("--iterations", type=int, default=1000)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.INFO)

    strategies = [
        # RoundBasedConstantBank("Bank 1500/600", [[10, 1500], [20, 600]]),
        # RoundBasedConstantBank("Bank 1000/500", [[10, 1000], [20, 500]]),
    ]

    strategies.append(BankAfterRound(f"Bank round {40}", 40))
    # for v in range(1, 40):
    #     strategies.append(BankAfterRound(f"Bank round {v}", v))

    # for v in range(200, 15000, 500):
    #     strategies.append(ConstantBank(f"Bank at {v}", v))

    # for v in range(200, 2000, 200):
    #     strategies.append(SmartBank(f"Scaled diff {v}", catch_up_bank=v))

    # for v in range(200, 1000, 200):
    #     strategies.append(
    #         SmartBank(f"Absolute diff {v}", catch_up_bank=v, divide_mult=0)
    #     )

    strategy_names = [s.name for s in strategies]

    reached_round_count = {}
    results = {}
    wins = {}
    bank_count = {}
    for strategy in strategies:
        results[strategy.name] = []
        wins[strategy.name] = 0
        bank_count[strategy.name] = 0

    for i in range(args.iterations):
        game = GameState()
        game.rounds = args.rounds
        game.strategies = strategies
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
                reached_round_count[game.round - 1] = (
                    reached_round_count.get(game.round - 1, 0) + 1
                )
                for strategy in strategies:
                    if strategy in banked_players:
                        continue

                    should_bank = strategy.will_bank(game)
                    if should_bank:
                        scores[strategy.name] += game.bank
                        banked_players.add(strategy)
                        bank_count[strategy.name] += 1
                        log.info(f"{strategy.name} banked {game.bank}")

        for strategy in strategies:
            results[strategy.name].append(scores[strategy.name])
            log.info(f"{strategy.name} scored {scores[strategy.name]}")

        # determine the winner
        max_score = max(scores.values())
        winners = [name for name, score in scores.items() if score == max_score]
        for winner in winners:
            wins[winner] += 1

        game.scores = scores

    average_results = {}
    for strategy in strategies:
        average_results[strategy.name] = sum(results[strategy.name]) / args.iterations
    log.info(f"Results: {average_results}")

    stddev_results = {}
    for strategy in strategies:
        if len(results[strategy.name]) > 1:
            stddev_results[strategy.name] = statistics.stdev(results[strategy.name])
        else:
            stddev_results[strategy.name] = 0

    chances = args.rounds * args.iterations
    print("ROUNDS REACHED", reached_round_count)
    ROUNDS_REACHED = 50
    round_reach_likelihood = []
    for i in range(ROUNDS_REACHED):
        times_reached = reached_round_count.get(i, 0)
        round_reach_likelihood.append(times_reached / chances)

    # graph the likelihood of reaching a round using reached_round_count
    plt.figure(figsize=(15, 8))
    plt.plot(range(ROUNDS_REACHED), round_reach_likelihood)
    plt.xlabel("Round")
    plt.ylabel("Likelihood of Reaching Round")
    plt.title("Likelihood of Reaching Round")
    plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x:.0%}'))
    plt.gca().yaxis.set_major_locator(plt.MultipleLocator(0.05))  # Show more percentage ticks
    plt.gca().xaxis.set_major_locator(plt.MultipleLocator(1))  # Space vertical lines every 1
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.grid(axis='x', linestyle='--', alpha=0.7)  # Add vertical dotted lines
    plt.tight_layout()
    plt.savefig("results-round-reach.png", bbox_inches="tight", dpi=300)

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

    # render the number of times each strategy banked
    plt.figure(figsize=(15, 8))
    plt.barh(list(bank_count.keys()), list(bank_count.values()))
    plt.xlabel("Number of Times Banked")
    plt.ylabel("Strategy")
    plt.title("Number of Times Banked by Strategy")
    plt.tight_layout()
    plt.savefig("results-bank-count.png", bbox_inches="tight", dpi=300)


if __name__ == "__main__":
    main()
