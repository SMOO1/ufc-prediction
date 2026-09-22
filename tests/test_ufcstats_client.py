import unittest

from ufcstats_client import UFCStatsClient, normalize_fighter_name


DIRECTORY_HTML = """
<table>
  <tr class="b-statistics__table-row">
    <td class="b-statistics__table-col"><a href="http://ufcstats.com/fighter-details/test">Sean</a></td>
    <td class="b-statistics__table-col"><a href="http://ufcstats.com/fighter-details/test">O'Malley</a></td>
    <td class="b-statistics__table-col"><a href="http://ufcstats.com/fighter-details/test">Suga</a></td>
  </tr>
</table>
"""

PROFILE_HTML = """
<h2 class="b-content__title">Sean O'Malley Record: 20-3-0 (1 NC)</h2>
<ul>
  <li class="b-list__box-list-item">Height: 5' 11&quot;</li>
  <li class="b-list__box-list-item">Weight: 135 lbs.</li>
  <li class="b-list__box-list-item">Reach: 72&quot;</li>
  <li class="b-list__box-list-item">STANCE: Switch</li>
  <li class="b-list__box-list-item">DOB: Oct 24, 1994</li>
  <li class="b-list__box-list-item">SLpM: 5.98</li>
  <li class="b-list__box-list-item">Str. Acc.: 60%</li>
  <li class="b-list__box-list-item">SApM: 3.40</li>
  <li class="b-list__box-list-item">Str. Def: 59%</li>
  <li class="b-list__box-list-item">TD Avg.: 0.23</li>
  <li class="b-list__box-list-item">TD Acc.: 42%</li>
  <li class="b-list__box-list-item">TD Def.: 60%</li>
  <li class="b-list__box-list-item">Sub. Avg.: 0.2</li>
</ul>
"""


class UFCStatsClientTests(unittest.TestCase):
    def test_name_normalization_accepts_requested_input_format(self):
        self.assertEqual(normalize_fighter_name("sean_omalley"), "sean omalley")
        self.assertEqual(normalize_fighter_name("Sean O'Malley"), "sean omalley")

    def test_directory_and_profile_fields_are_parsed(self):
        matches = UFCStatsClient.parse_directory(DIRECTORY_HTML)
        self.assertEqual(matches, [{
            "name": "Sean O'Malley",
            "nickname": "Suga",
            "url": "http://ufcstats.com/fighter-details/test",
        }])

        profile = UFCStatsClient.parse_profile(PROFILE_HTML, matches[0])
        self.assertEqual(profile.name, "Sean O'Malley")
        self.assertEqual(profile.record, "20-3-0 (1 NC)")
        self.assertEqual(profile.height_inches, 71)
        self.assertEqual(profile.weight_lbs, 135)
        self.assertEqual(profile.reach_inches, 72)
        self.assertEqual(profile.stance, "Switch")
        self.assertEqual(profile.dob.year, 1994)
        self.assertAlmostEqual(profile.slpm, 5.98)
        self.assertAlmostEqual(profile.str_acc, 0.60)
        self.assertAlmostEqual(profile.sapm, 3.40)
        self.assertAlmostEqual(profile.str_def, 0.59)
        self.assertAlmostEqual(profile.td_avg, 0.23)
        self.assertAlmostEqual(profile.td_acc, 0.42)
        self.assertAlmostEqual(profile.td_def, 0.60)
        self.assertAlmostEqual(profile.sub_avg, 0.2)


if __name__ == "__main__":
    unittest.main()
