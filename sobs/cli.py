from sobs import tasks
import click


@click.command()
def init_database():
    print("--- initializing database")
    tasks.create_tables()


@click.command()
def load_database():
    print("--- loading database")
    tasks.load_from_ncbi_tar("NCBI_SRA_Metadata_Full_20190629.tar.gz")


@click.group()
def cli():
    pass


cli.add_command(init_database)
cli.add_command(load_database)
