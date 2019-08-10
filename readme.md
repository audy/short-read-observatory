# :earth_americas: :earth_asia: :earth_africa: Short Read Observatory

Create a relational database from NCBI/SRA so that I can query SRA sample data
and extract SRA Run IDs

# Instructions

Install requirements:

`python setup.py install`

Or, if developing:

`pip install -e .`

Run `sobs --help` for the rest.

# Schema

There are 3 tables:

- `sample`
- `run`
- `experiment`

The schema is ~roughly~ the same as the NCBI SRA ([see their
documentation](https://www.ncbi.nlm.nih.gov/sra/docs/submitmeta/)) although I
didn't extract everything from their XML dumps. To get from experiment to run,
you have to join on sample. In SQL, this would look like:

```sql
select
  scientific_name,
  count(*)
from
  experiment
left join
  sample
on
  experiment.sample_accession = sample.id
left join
  run
on
  run.experiment_accession = experiment.id
where
  scientific_name = "soil metagenome"
group by
  sample.scientific_name
order by
  count desc
```


Output a list of SRR IDs (needed to download the fastq files) with some relevant metadata:

```sql
select
  experiment.id as experiment_accession,
  sample.id as sample_accession,
  sample.scientific_name,
  sample.taxid,
  run.id as run_accession,
  scientific_name,
  experiment.library_name,
  experiment.library_strategy,
  experiment.library_source,
  experiment.library_selection,
  experiment.library_layout,
  experiment.platform_type,
  experiment.platform_instrument_model,
  run.title,
  attributes->'lat_lon' as lat_lon,
  attributes->'geo_loc_name' as geo_loc_name,
  attributes->'study name' as study_name
from
  experiment
left join
  sample
on
  experiment.sample_accession = sample.id
left join
  run
on
  run.experiment_accession = experiment.id
where
  scientific_name LIKE %s
```
