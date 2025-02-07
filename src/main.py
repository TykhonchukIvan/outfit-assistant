from pprint import pprint
from src.core.service_mediator import ServiceMediator


def main():
    pprint({"INFO": "Starting application..."})
    mediator = ServiceMediator()
    mediator.run()


if __name__ == "__main__":
    main()
