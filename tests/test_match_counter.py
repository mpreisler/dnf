# Copyright (C) 2012-2013  Red Hat, Inc.
#
# This copyrighted material is made available to anyone wishing to use,
# modify, copy, or redistribute it subject to the terms and conditions of
# the GNU General Public License v.2, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY expressed or implied, including the implied warranties of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General
# Public License for more details.  You should have received a copy of the
# GNU General Public License along with this program; if not, write to the
# Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.  Any Red Hat trademarks that are incorporated in the
# source code or documentation are not subject to the GNU General Public
# License and may only be used or replicated with the express permission of
# Red Hat, Inc.
#

from __future__ import absolute_import
from __future__ import unicode_literals
from tests import support
from tests.support import mock

import dnf.match_counter

class PackageStub(support.MockPackage):
    @classmethod
    def several(cls, count):
        for _ in range(count):
            yield cls()

    def __init__(self, nevra='nevra-1-1.noarch', summary='summary'):
        super(PackageStub, self).__init__(nevra)
        self.summary = summary
        self.url = ''
        self.description = ''


class MatchCounterTest(support.TestCase):
    def test_canonize_string_set(self):
        a = ['f', 'p']
        b = ['p']
        self.assertLess(dnf.match_counter._canonize_string_set(b, 2),
                        dnf.match_counter._canonize_string_set(a, 2))

    def test_matched(self):
        pkg = support.MockPackage("humbert-1-1.noarch")
        pkg.url = url = "http://humbert.com"
        pkg.summary = summary = "Glimpses of an incomparably more poignant bliss."
        counter = dnf.match_counter.MatchCounter()
        counter.add(pkg, 'summary', 'poignant')
        counter.add(pkg, 'url', 'humbert')
        counter.add(pkg, 'summary', 'humbert')
        self.assertItemsEqual(counter.matched_needles(pkg),
                              ['humbert', 'poignant'])
        self.assertItemsEqual(counter.matched_keys(pkg), ['url', 'summary'])
        self.assertItemsEqual(counter.matched_haystacks(pkg), [url, summary])

    @mock.patch('dnf.match_counter.MatchCounter._eval_distance', return_value=0)
    def test_sorted(self, _):
        counter = dnf.match_counter.MatchCounter()
        self.assertEqual(counter.sorted(), [])

        counter = dnf.match_counter.MatchCounter()
        pkg1, pkg2, pkg3 = PackageStub().several(3)
        counter.add(pkg1, 'name', '')
        counter.add(pkg2, 'summary', '')
        self.assertEqual(counter.sorted(), [pkg2, pkg1])

        counter.add(pkg3, 'url', '')
        self.assertEqual(counter.sorted(), [pkg3, pkg2, pkg1])
        self.assertEqual(counter.sorted(reverse=True), [pkg1, pkg2, pkg3])

    @mock.patch('dnf.match_counter.MatchCounter._eval_distance', return_value=0)
    def test_sorted_with_needles(self, _):
        # the same needles should be listed together:
        counter = dnf.match_counter.MatchCounter()
        pkg1, pkg2, pkg3, pkg4 = PackageStub().several(4)
        counter.add(pkg1, 'summary', 'grin')
        counter.add(pkg2, 'summary', 'foolish')
        counter.add(pkg3, 'summary', 'grin')
        counter.add(pkg4, 'summary', 'grin')

        srt = counter.sorted()
        self.assertIn(srt.index(pkg2), (0, 3))

        # more unique needles is more than less unique needles:
        counter = dnf.match_counter.MatchCounter()
        counter.add(pkg1, 'summary', 'a')
        counter.add(pkg1, 'summary', 'b')
        counter.add(pkg2, 'summary', 'b')
        counter.add(pkg2, 'summary', 'b')

        self.assertSequenceEqual(counter.sorted(), (pkg2, pkg1))

    @mock.patch('dnf.match_counter.MatchCounter._eval_distance', return_value=0)
    def test_sorted_limit(self, _):
        counter = dnf.match_counter.MatchCounter()
        pkg1, pkg2, pkg3 = PackageStub().several(3)
        counter.add(pkg1, 'name', '')
        counter.add(pkg2, 'url', '')
        counter.add(pkg3, 'description', '')
        self.assertSequenceEqual(counter.sorted(limit_to=[pkg1, pkg2]),
                                 (pkg2, pkg1))

    @mock.patch('dnf.match_counter.MatchCounter._eval_distance', return_value=0)
    def test_sorted_exact_match(self, _):
        """Exactly matching the name beats name and summary non-exact match."""
        counter = dnf.match_counter.MatchCounter()
        pkg1 = PackageStub('wednesday-1-1.noarch', 'morning')
        pkg2 = PackageStub('wednesdaymorning-1-1.noarch', "5 o'clock")
        counter.add(pkg1, 'name', 'wednesday')
        counter.add(pkg2, 'name', 'wednesday')
        counter.add(pkg2, 'summary', 'clock')
        self.assertSequenceEqual(counter.sorted(), (pkg2, pkg1))

    def test_total(self):
        counter = dnf.match_counter.MatchCounter()
        counter.add(3, 'summary', 'humbert')
        counter.add(3, 'url', 'humbert')
        counter.add(20, 'summary', 'humbert')
        self.assertEqual(len(counter), 2)
        self.assertEqual(counter.total(), 3)

    def test_distance(self):
        pkg2 = support.MockPackage('rust-and-stardust-1-2.x86_64')
        pkg1 = support.MockPackage('rust-1-3.x86_64')
        counter = dnf.match_counter.MatchCounter()
        counter.add(pkg1, 'name', 'rust')
        counter.add(pkg2, 'name', 'rust')
        # 'rust-and-stardust' is a worse match for 'rust' than 'rust' itself
        self.assertSequenceEqual([x.name for x in counter.sorted()],
                                 ['rust-and-stardust', 'rust'])
