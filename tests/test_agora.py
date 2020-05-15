import openreview
import pytest


class TestAgora():

    def test_setup(self, client):

        ##Create support group

        support_group = openreview.Group(
            id='openreview.net/Support',
            readers=['everyone'],
            writers=['openreview.net'],
            signatures=['openreview.net'],
            signatories=['openreview.net/Support'],
            members=[],

        )
        client.post_group(support_group)

        agora = openreview.agora.Agora(client, support_group.id)