import boto3
import click
from colorama import init as windows_color_init

from parsers import EC2Service, RDSService, sort_parsed_data

ACTION_HELP_STR = "Actions"
DB_HELP_STR = "Show DB instances table"
ORDER_HELP_STR = "Table sorting. Options: table header lowercase (e.g. `state name`)"
ENV_HELP_STR = "List only instacies that match specified env"
COLOR_HELP_STR = "Old style shell"
TABLE_STYLE_HELP_STR = "Table style. Options: plain, simple, github, grid, etc. (check tabulate doc)"


@click.command()
@click.option("--action", default="status", help=ACTION_HELP_STR)
@click.option("--db", default=False, is_flag=True, help=DB_HELP_STR)
@click.option("--order", default="state", help=ORDER_HELP_STR)
@click.option("--env", default="all", help=ENV_HELP_STR)
@click.option("--no-color", default=False, is_flag=True, help=COLOR_HELP_STR)
@click.option("--table", default="psql", help=TABLE_STYLE_HELP_STR)
def main(**kwargs):
    """Main function that calls all stuff related to parsing/sorting/printing."""
    ec2 = boto3.client("ec2")
    rds = boto3.client("rds")

    action = kwargs.get("action")
    no_color = kwargs.get("no_color")

    color = not no_color
    if color:
        windows_color_init()  # He he...

    if action == "status":
        show_db_table = kwargs.get("db")
        order_by = kwargs.get("order")
        env = kwargs.get("env")
        tablefmt = kwargs.get("table")

        ec2_parser = EC2Service(ec2, color=color)
        parsed_ec2_data = ec2_parser.parse_data()
        sorted_ec2_data = sort_parsed_data(parsed_ec2_data, order_by=order_by, env=env)
        ec2_parser.show_parsed_data(data=sorted_ec2_data, tablefmt=tablefmt)

        if show_db_table:
            rds_parser = RDSService(rds, color=color)
            parsed_rds_data = rds_parser.parse_data()
            sorted_rds_data = sort_parsed_data(parsed_rds_data, order_by=order_by, env=env, rds=True)
            rds_parser.show_parsed_data(data=sorted_rds_data, tablefmt=tablefmt)


if __name__ == "__main__":
    main()
