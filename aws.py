import boto3
import click

from colorama import init as windows_color_init

from parsers import EC2Parser, RDSParser

windows_color_init()  # He he...

ACTION_HELP_STR = "Actions"
ORDER_HELP_STR = "Table sorting. Options: table header lowercase (e.g. `state name`)"
ENV_HELP_STR = "List only instacies that match specified env"
COLOR_HELP_STR = "Old style shell"
TABLE_STYLE_HELP_STR = "Table style. Options: plain, simple, github, grid, etc. (check tabulate doc)"


@click.command()
@click.option("-a", "--action", default="status", help=ACTION_HELP_STR)
@click.option("-o", "--order", default="name", help=ORDER_HELP_STR)
@click.option("-e", "--env", default="all", help=ENV_HELP_STR)
@click.option("-n", "--no-color", default=False, is_flag=True, help=COLOR_HELP_STR)
@click.option("-t", "--table", default="psql", help=TABLE_STYLE_HELP_STR)
def main(*args, **kwargs):
    ec2 = boto3.client("ec2")
    rds = boto3.client("rds")

    action = kwargs.get("action")
    no_color = kwargs.get("no_color")

    if action == "status":
        order_by = kwargs.get("order")
        env = kwargs.get("env")
        table = kwargs.get("table")

        ec2_parser = EC2Parser(ec2)
        ec2_parser.status(order_by=order_by, env=env, color=not no_color, tablefmt=table)

        rds_parser = RDSParser(rds)
        rds_parser.status(order_by=order_by, env=env, color=not no_color, tablefmt=table)


if __name__ == "__main__":
    main()
