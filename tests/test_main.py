import io
import json
import unittest
from collections import Counter
from unittest.mock import patch

import main


class AnnotationCountsTests(unittest.TestCase):
    def test_streams_map_dump_and_counts_image_hosts(self):
        maps = [
            {"resource": {"id": "https://maps.example.org/iiif/1"}},
            {"resource": {"id": "https://maps.example.org/iiif/2"}},
            {"resource": {"id": "https://other.example/iiif/3"}},
        ]
        body = b"\n".join(json.dumps(item).encode() for item in maps) + b"\n"
        with patch("main.urllib.request.urlopen", return_value=io.BytesIO(body)):
            counts = main.count_annotations_by_domain()
        self.assertEqual(counts, Counter({"maps.example.org": 2, "other.example": 1}))

    def test_groups_partners_other_institutions_and_unmatched_hosts(self):
        orgs = [
            {"id": "1", "name": "A Library", "plan": "innovator", "domains": ["example.org"]},
            {"id": "2", "name": "B Archive", "plan": "supporter", "domains": ["maps.example.org"]},
            {"id": "3", "name": "C Museum", "plan": "contributor", "domains": ["museum.org"]},
            {"id": "4", "name": "D Library", "plan": None, "domains": []},
        ]
        counts = Counter({
            "data.example.org": 2,
            "maps.example.org": 3,
            "museum.org": 4,
            "unlisted.org": 1,
        })
        sections = main.build_sections(orgs, counts)
        self.assertEqual([section["title"] for section in sections], [
            "Innovators", "Supporters", "Other institutions", "Other IIIF hosts"
        ])
        self.assertEqual(sections[0]["orgs"][0]["annotation_count"], 2)
        self.assertEqual(sections[1]["orgs"][0]["annotation_count"], 3)
        self.assertEqual([org["annotation_count"] for org in sections[2]["orgs"]], [4, 0])
        self.assertEqual(sections[3]["orgs"], [{"name": "unlisted.org", "annotation_count": 1}])

    def test_rejects_ambiguous_domain_ownership(self):
        orgs = [
            {"id": "1", "name": "A", "domains": ["example.org"]},
            {"id": "2", "name": "B", "domains": ["example.org"]},
        ]
        with self.assertRaisesRegex(ValueError, "Multiple institutions"):
            main.build_sections(orgs, Counter({"example.org": 1}))


if __name__ == "__main__":
    unittest.main()
