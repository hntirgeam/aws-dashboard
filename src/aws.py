import boto3
import click
from colorama import init as windows_color_init

from .parsers import DB_INSTANCES_TABLE_HEADERS, INSTANCES_TABLE_HEADERS, EC2Service, RDSService, sort_parsed_data

ACTION_HELP_STR = "Actions"
DB_HELP_STR = "Show DB instances table"
ORDER_HELP_STR = "Table sorting. Options: table header lowercase (e.g. `state name`)"
ENV_HELP_STR = "{} only instances that match specified env"
COLOR_HELP_STR = "Old style shell"
TABLE_STYLE_HELP_STR = "Table style. Options: plain, simple, github, grid, etc. (check tabulate doc)"
SH_COMPATIBLE_HELP_STR = "Prints as lines of code that would be easier to parse using sh/bash scripts."
SH_SEPARATOR_HELP_STR = "Defines separator for sh-compatible output. Defaults to `|`"
STATE_HELP_STR = "Shows only <state name> instances"
ACTION_STR = "This action will {} listed {} instance(s):"
ERROR_STR = "Something went wrong. Check this out"
BOTO3_CONFIG_ERROR_STR = (
    'Looks like "{}"\nhttps://boto3.amazonaws.com/v1/documentation/api/latest/guide/quickstart.html#configuration'
)


@click.group()
def cli():
    pass


@cli.command()
@click.option("--no-db", default=False, is_flag=True, help=DB_HELP_STR)
@click.option("--order", default="state", help=ORDER_HELP_STR)
@click.option("--env", default="all", help=ENV_HELP_STR.format("List"))
@click.option("--state", default="all", help=STATE_HELP_STR)
@click.option("--no-color", default=False, is_flag=True, help=COLOR_HELP_STR)
@click.option("--table", default="psql", help=TABLE_STYLE_HELP_STR)
@click.option("--sh", default=False, is_flag=True, help=SH_COMPATIBLE_HELP_STR)
@click.option("--sh-separator", default="|", help=SH_SEPARATOR_HELP_STR)
def status(**kwargs):
    no_color = kwargs.get("no_color")
    show_db_table = kwargs.get("no_db")
    show_db_table = not show_db_table
    order_by = kwargs.get("order")
    env = kwargs.get("env")
    state = kwargs.get("state")
    tablefmt = kwargs.get("table")

    sh_compatible_output = kwargs.get("sh")
    sh_sep = kwargs.get("sh_separator")

    color = not no_color
    if color:
        windows_color_init()  # He he...

    ec2_parser = EC2Service(ec2, color=color)
    parsed_ec2_data = ec2_parser.parse_data()
    sorted_ec2_data = sort_parsed_data(parsed_ec2_data, order_by=order_by, env=env, state=state)
    if sorted_ec2_data:
        ec2_parser.show_parsed_data(data=sorted_ec2_data, tablefmt=tablefmt, sh=sh_compatible_output, separ=sh_sep)
    elif not sh_compatible_output:
        print("No EC2 data found!")

    if show_db_table:
        rds_parser = RDSService(rds, color=color)
        parsed_rds_data = rds_parser.parse_data()
        sorted_rds_data = sort_parsed_data(parsed_rds_data, order_by=order_by, env=env, state=state, rds=True)
        if sorted_rds_data:
            rds_parser.show_parsed_data(data=sorted_rds_data, tablefmt=tablefmt, sh=sh_compatible_output, separ=sh_sep)
        elif not sh_compatible_output:
            print("No RDS data found!")


@cli.command()
@click.argument("ids", nargs=-1)
@click.confirmation_option(prompt="Are you sure you want to start this instance(s)?")
def start(ids):
    ids = list(dict.fromkeys(ids))

    try:
        response = ec2.start_instances(InstanceIds=ids, DryRun=False)
        print(response)
    except Exception as e:
        print(f"{ERROR_STR}:{e}")


@cli.command()
@click.argument("ids", nargs=-1)
@click.confirmation_option(prompt="Are you sure you want to stop this instance(s)?")
def stop(ids):
    ids = list(dict.fromkeys(ids))

    try:
        response = ec2.stop_instances(InstanceIds=ids, DryRun=False)
        print(response)
    except Exception as e:
        print(f"{ERROR_STR}:{e}")


@cli.command()
@click.option("--env", required=True, help=ENV_HELP_STR.format("Start"))
def bulk_start(env):
    ec2_parser = EC2Service(ec2, color=False)
    parsed_ec2_data = ec2_parser.parse_data()
    sorted_ec2_data = sort_parsed_data(parsed_ec2_data, order_by="state", env=env)

    rds_parser = RDSService(rds, color=False)
    parsed_rds_data = rds_parser.parse_data()
    sorted_rds_data = sort_parsed_data(parsed_rds_data, order_by="state", env=env, rds=True)

    if sorted_ec2_data:
        print(ACTION_STR.format("start", "EC2"))
        for server in sorted_ec2_data:
            print(server[0])
        print()

    if sorted_rds_data:
        print(ACTION_STR.format("start", "RDS"))
        for server in sorted_rds_data:
            print(server[0])
        print()

    if click.confirm("Do you want to start listed instance(s)?"):
        try:
            id_index = INSTANCES_TABLE_HEADERS.index("Id")
            response = ec2.start_instances(InstanceIds=[i[id_index] for i in sorted_ec2_data], DryRun=False)
            print(response)
        except Exception as e:
            print(f"{ERROR_STR}:{e}")

        try:
            identifier_index = DB_INSTANCES_TABLE_HEADERS.index("Name")
            for cluster in sorted_rds_data:
                response = rds.start_db_cluster(DBClusterIdentifier=cluster[identifier_index])
                print(response)
        except Exception as e:
            print(f"{ERROR_STR}:{e}")


@cli.command()
@click.option("--env", required=True, help=ENV_HELP_STR.format("Stop"))
def bulk_stop(env):
    ec2_parser = EC2Service(ec2, color=False)
    parsed_ec2_data = ec2_parser.parse_data()
    sorted_ec2_data = sort_parsed_data(parsed_ec2_data, order_by="state", env=env)

    rds_parser = RDSService(rds, color=False)
    parsed_rds_data = rds_parser.parse_data()
    sorted_rds_data = sort_parsed_data(parsed_rds_data, order_by="state", env=env, rds=True)

    if sorted_ec2_data:
        print(ACTION_STR.format("stop", "EC2"))
        for server in sorted_ec2_data:
            print(server[0])
        print()

    if sorted_rds_data:
        print(ACTION_STR.format("stop", "RDS"))
        for server in sorted_rds_data:
            print(server[0])
        print()

    if click.confirm("Do you want to stop listed instance(s)?"):
        if click.confirm("Are you SURE?"):
            if click.confirm("This is your last warning"):
                try:
                    id_index = INSTANCES_TABLE_HEADERS.index("Id")
                    response = ec2.stop_instances(InstanceIds=[i[id_index] for i in sorted_ec2_data], DryRun=False)
                    print(response)
                except Exception as e:
                    print(f"{ERROR_STR}:{e}")

                try:
                    identifier_index = DB_INSTANCES_TABLE_HEADERS.index("Name")
                    for cluster in sorted_rds_data:
                        response = rds.stop_db_cluster(DBClusterIdentifier=cluster[identifier_index])
                        print(response)
                except Exception as e:
                    print(f"{ERROR_STR}:{e}")


def main():
    global ec2, rds

    try:
        ec2 = boto3.client("ec2")
        rds = boto3.client("rds")
    except Exception as e:
        print(BOTO3_CONFIG_ERROR_STR.format(e))
        exit(1)

    cli()


if __name__ == "__main__":
    main()
