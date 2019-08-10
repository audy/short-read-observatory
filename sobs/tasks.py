import tarfile
import xml.etree.ElementTree
from pprint import pprint
from collections import defaultdict
from pprint import pprint

from sobs.models import Experiment, Sample, Run, get_database

import peewee


def fetch_first_n_sequences_of_fastq_from_ncbi_sra(sra_id, out_path, n=25):
    """
    Given an NCBI SRA Run ID, will fetch the first n lines of that file and
    save it to {SRR_ID}.fastq
    """

    n_lines = n * 4  # because fastq

    res = subprocess.check_output(
        f"/usr/local/bin/fastq-dump -F -Z {sra_id} | head -n {n_lines} > {out_path}", shell=True
    )

    return res


def recurse_node(node):
    return [node, [child for child in node.iter()]]


def get_first_node(node, selector):
    results = node.findall(selector)

    if len(results) == 0:
        return None
    elif len(results) == 1:
        return results[0].text
    else:
        raise Exception(f"expected <= 1 results")


def load_run_data(node):
    for run in node.findall("RUN"):
        primary_key = run.attrib["accession"]

        # sometimes like this
        experiment_accessions = run.findall("EXPERIMENT_REF")

        assert len(experiment_accessions) == 1
        experiment_accession = experiment_accessions[0].attrib["accession"]

        title = get_first_node(run, "TITLE")

        yield primary_key, {"title": title, "experiment_accession": experiment_accession}


def load_sample_data(node):
    """
    Loads all sample data


    But we really mostly only care about a few attributes:

        - lat_lon
        - organism
    """
    for sample in node.findall("SAMPLE"):
        primary_key = sample.attrib["accession"]

        #
        # taxid
        #

        try:
            taxid = int(get_first_node(sample, "SAMPLE_NAME/TAXON_ID"))
            scientific_name = get_first_node(sample, "SAMPLE_NAME/SCIENTIFIC_NAME")

            if scientific_name == "metagenome":
                print_attributes = True
        except IndexError:
            taxid = None
            scientific_name = None

        #
        # sample_attributes
        #

        sample_attributes = sample.findall("SAMPLE_ATTRIBUTES/SAMPLE_ATTRIBUTE")

        attributes = defaultdict(list)
        for attribute in sample_attributes:
            tags = attribute.findall("TAG")
            values = attribute.findall("VALUE")

            assert len(tags) == 1, pprint(recurse_node(attribute))

            if len(values) == 0:
                value_text = None
                tag_text = tags[0].text
            elif len(values) == 1:
                tag_text, value_text = tags[0].text, values[0].text

            if tag_text is not None:

                # strip periods because they kill the mongo
                tag_text = tag_text.replace(".", "_")

                attributes[tag_text].append(value_text)

        yield (
            primary_key,
            {"attributes": attributes, "scientific_name": scientific_name, "taxid": taxid},
        )


def load_experiment_data(node):
    # TODO:
    # - PLATFORM
    for experiment in node.findall("EXPERIMENT"):
        primary_key = experiment.attrib["accession"]

        # jump through hoops to get to layout
        layout = {n.tag for n in experiment.find("DESIGN/LIBRARY_DESCRIPTOR/LIBRARY_LAYOUT")}

        assert len(layout) == 1, layout

        layout_text = list(layout)[0]

        # jump through hoops to get to playform
        # jump through hoops to get to layout
        platform = experiment.find("PLATFORM")

        platform_type = list(platform.iter())[1].tag

        platform_instrument_model = platform.find("*/INSTRUMENT_MODEL").text

        experiment_data = {
            "sample_accession": get_first_node(
                experiment, "DESIGN/SAMPLE_DESCRIPTOR/IDENTIFIERS/PRIMARY_ID"
            ),
            "description": get_first_node(experiment, "DESIGN/DESIGN_DESCRIPTION"),
            "library_name": get_first_node(experiment, "DESIGN/LIBRARY_DESCRIPTOR/LIBRARY_NAME"),
            "library_strategy": get_first_node(
                experiment, "DESIGN/LIBRARY_DESCRIPTOR/LIBRARY_STRATEGY"
            ),
            "library_source": get_first_node(
                experiment, "DESIGN/LIBRARY_DESCRIPTOR/LIBRARY_SOURCE"
            ),
            "library_selection": get_first_node(
                experiment, "DESIGN/LIBRARY_DESCRIPTOR/LIBRARY_SELECTION"
            ),
            "library_layout": layout_text,
            "platform_type": platform_type,
            "platform_instrument_model": platform_instrument_model,
        }

        yield primary_key, experiment_data


def create_tables():
    db = get_database()
    db.create_tables([Experiment, Sample, Run])


def load_from_ncbi_tar(tar_path, batch_size=10000):
    with tarfile.open(tar_path, "r:gz") as tar:
        for n, member in enumerate(tar):
            print(member)
            h = tar.extractfile(member)

            experiments_batch = []
            samples_batch = []
            runs_batch = []

            if h is not None:
                if "experiment" in member.name:
                    # experiment alias -> biosample identifier
                    with tar.extractfile(member) as handle:
                        root = xml.etree.ElementTree.parse(handle)
                        for _id, experiment_data in load_experiment_data(root):
                            experiments_batch.append({"id": _id, **experiment_data})

                            if len(experiments_batch) >= batch_size:
                                Experiment.insert_many(experiments_batch).execute()
                                experiments_batch = []

                    # insert final batch
                    if len(experiments_batch) > 0:
                        Experiment.insert_many(experiments_batch).execute()

                if "sample" in member.name:
                    with tar.extractfile(member) as handle:
                        root = xml.etree.ElementTree.parse(handle)
                        for _id, sample_data in load_sample_data(root):
                            row = {"id": _id, **sample_data}
                            samples_batch.append(row)
                            if len(samples_batch) >= batch_size:
                                Sample.insert_many(samples_batch).execute()
                                samples_batch = []

                    # insert final batch
                    if len(samples_batch) > 0:
                        Sample.insert_many(samples_batch).execute()

                if "run" in member.name:
                    with tar.extractfile(member) as handle:
                        root = xml.etree.ElementTree.parse(handle)
                        for _id, run_data in load_run_data(root):
                            runs_batch.append({"id": _id, **run_data})

                            if len(runs_batch) >= batch_size:
                                Run.insert_many(runs_batch).execute()
                                runs_batch = []
                    # insert final batch
                    if len(runs_batch) > 0:
                        Run.insert_many(runs_batch).execute()

            else:
                pass
