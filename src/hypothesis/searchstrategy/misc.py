# coding=utf-8

# Copyright (C) 2013-2015 David R. MacIver (david@drmaciver.com)

# This file is part of Hypothesis (https://github.com/DRMacIver/hypothesis)

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

# END HEADER

from __future__ import division, print_function, absolute_import, \
    unicode_literals

from random import Random

import hypothesis.specifiers as specifiers
import hypothesis.internal.distributions as dist
from hypothesis.types import RandomWithSeed
from hypothesis.internal.compat import hrange, integer_types
from hypothesis.internal.chooser import chooser
from hypothesis.searchstrategy.strategies import BadData, SearchStrategy, \
    MappedSearchStrategy, strategy, check_type, check_data_type


class BoolStrategy(SearchStrategy):

    """A strategy that produces Booleans with a Bernoulli conditional
    distribution."""
    template_upper_bound = 2

    def __repr__(self):
        return 'BoolStrategy()'

    def reify(self, value):
        return value

    def strictly_simpler(self, x, y):
        return (not x) and y

    def basic_simplify(self, random, value):
        if value:
            yield False

    def draw_parameter(self, random):
        return random.random()

    def draw_template(self, random, p):
        return dist.biased_coin(random, p)

    def to_basic(self, value):
        check_type(bool, value)
        return int(value)

    def from_basic(self, value):
        check_data_type(int, value)
        return bool(value)


class JustStrategy(SearchStrategy):

    """
    A strategy which simply returns a single fixed value with probability 1.
    """
    template_upper_bound = 1

    def __init__(self, value):
        SearchStrategy.__init__(self)
        self.value = value

    def __repr__(self):
        return 'JustStrategy(value=%r)' % (self.value,)

    def draw_parameter(self, random):
        return None

    def draw_template(self, random, pv):
        return None

    def reify(self, template):
        assert template is None
        return self.value

    def to_basic(self, template):
        return None

    def from_basic(self, data):
        if data is not None:
            raise BadData('Expected None but got %r' % (repr(data,)))
        return None


class RandomStrategy(MappedSearchStrategy):

    """A strategy which produces Random objects.

    The conditional distribution is simply a RandomWithSeed seeded with
    a 128 bits of data chosen uniformly at random.

    """

    def pack(self, i):
        return RandomWithSeed(i)


class SampledFromStrategy(SearchStrategy):

    """A strategy which samples from a set of elements. This is essentially
    equivalent to using a OneOfStrategy over Just strategies but may be more
    efficient and convenient.

    The conditional distribution chooses uniformly at random from some
    non-empty subset of the elements.

    """

    def __init__(self, elements):
        SearchStrategy.__init__(self)
        self.elements = tuple(elements)
        if not self.elements:
            raise ValueError(
                'SampledFromStrategy requires at least one element')
        self.template_upper_bound = len(elements)

    def to_basic(self, template):
        return template

    def from_basic(self, data):
        check_data_type(integer_types, data)
        if data < 0:
            raise BadData('Index out of range: %d < 0' % (data,))
        elif data >= len(self.elements):
            raise BadData(
                'Index out of range: %d >= %d' % (data, len(self.elements)))

        return data

    def basic_simplify(self, random, template):
        for i in hrange(0, template):
            yield i

    def strictly_simpler(self, x, y):
        return x < y

    def __repr__(self):
        return 'SampledFromStrategy(%r)' % (self.elements,)

    def draw_parameter(self, random):
        n = len(self.elements)
        if n == 1:
            return
        return chooser(random.getrandbits(8) + 1 for _ in hrange(n))

    def draw_template(self, random, pv):
        if len(self.elements) == 1:
            return 0
        return pv.choose(random)

    def reify(self, template):
        return self.elements[template]


@strategy.extend_static(bool)
def bool_strategy(cls, settings):
    return BoolStrategy()


@strategy.extend(specifiers.Just)
def define_just_strategy(specifier, settings):
    return JustStrategy(specifier.value)


@strategy.extend_static(Random)
def define_random_strategy(specifier, settings):
    return RandomStrategy(strategy(int, settings))


@strategy.extend(specifiers.SampledFrom)
def define_sampled_strategy(specifier, settings):
    return SampledFromStrategy(specifier.elements)


@strategy.extend(type(None))
@strategy.extend_static(type(None))
def define_none_strategy(specifier, settings):
    return JustStrategy(None)
