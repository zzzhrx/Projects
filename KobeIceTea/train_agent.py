from game.config import load_config
from rl.q_learning import train_agent


def main() -> None:
    config = load_config()
    trained_agent = train_agent(config)

    print("Q-learning training complete.")
    print(f"Episodes: {trained_agent.summary.episodes}")
    print(
        "Training average reward: "
        f"{trained_agent.summary.average_training_reward:.2f}"
    )
    print(
        "Training average score: "
        f"{trained_agent.summary.average_training_score:.2f}"
    )
    print(
        "Evaluation average score: "
        f"{trained_agent.summary.evaluation_average_score:.2f}"
    )
    print(
        "Evaluation average reward: "
        f"{trained_agent.summary.evaluation_average_reward:.2f}"
    )
    print(f"Best training score: {trained_agent.summary.best_training_score}")
    print(f"Final epsilon: {trained_agent.summary.final_epsilon:.3f}")


if __name__ == "__main__":
    main()
