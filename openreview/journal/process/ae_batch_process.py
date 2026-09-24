def process(client, edit, invitation):
    import openreview
    from openreview.journal.ae_batch import prepare_ae_batch
    journal = openreview.journal.Journal()
    return prepare_ae_batch(client, journal, edit.note)
