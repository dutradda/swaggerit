# MIT License

# Copyright (c) 2016 Diogo Dutra <dutradda@gmail.com>

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


from tests.integration.models.orm.fixtures import *
import pytest


class TestModelGetRelatedHard(object):

    @pytest.mark.asyncio(forbid_global_loop=False)
    async def test_get_related_with_all_models_related_each_other(self, session):
        m11 = await Model1.new(session, id=1)
        m12 = await Model1.new(session, id=2)
        m13 = await Model1.new(session, id=3)

        m21 = await Model2.new(session, id=1)
        m22 = await Model2.new(session, id=2)
        m23 = await Model2.new(session, id=3)

        m31 = await Model3.new(session, id=1)
        m32 = await Model3.new(session, id=2)
        m33 = await Model3.new(session, id=3)

        m41 = await Model4.new(session, id=1)
        m42 = await Model4.new(session, id=2)
        m43 = await Model4.new(session, id=3)

        m51 = await Model5.new(session, id=1)
        m52 = await Model5.new(session, id=2)
        m53 = await Model5.new(session, id=3)

        m61 = await Model6.new(session, id=1)
        m62 = await Model6.new(session, id=2)
        m63 = await Model6.new(session, id=3)

        m71 = await Model7.new(session, id=1)
        m72 = await Model7.new(session, id=2)
        m73 = await Model7.new(session, id=3)

        m81 = await Model8.new(session, id=1)
        m82 = await Model8.new(session, id=2)
        m83 = await Model8.new(session, id=3)

        m91 = await Model9.new(session, id=1)
        m92 = await Model9.new(session, id=2)
        m93 = await Model9.new(session, id=3)

        m11.model2 = m21
        m11.model3 = [m31, m32]
        m11.model4 = [m42, m43]

        m12.model2 = m22
        m12.model3 = [m33]
        m12.model4 = [m43, m41]

        m13.model2 = m23
        m13.model4 = [m41, m42]

        m21.model3 = m33
        m21.model4 = [m41, m42]
        m21.model5 = [m52, m53]

        m22.model4 = [m43]
        m22.model5 = [m51, m53]

        m23.model5 = [m51, m52]

        m31.model4 = m41
        m31.model5 = [m51, m52]
        m31.model6 = [m62, m63]

        m32.model4 = m42
        m32.model5 = [m53]
        m32.model6 = [m61, m63]

        m33.model4 = m43
        m33.model6 = [m61, m62]

        m41.model5 = m53
        m41.model6 = [m61, m62]
        m41.model7 = [m72, m73]

        m42.model6 = [m63]
        m42.model7 = [m71, m73]

        m43.model7 = [m71, m72]

        m51.model6 = m61
        m51.model7 = [m71, m72]
        m51.model8 = [m82, m83]

        m52.model6 = m62
        m52.model7 = [m73]
        m52.model8 = [m81, m83]

        m53.model6 = m63
        m53.model8 = [m81, m82]

        m61.model7 = m73
        m61.model8 = [m81, m82]
        m61.model9 = [m92, m93]

        m62.model8 = [m83]
        m62.model9 = [m91, m93]

        m63.model9 = [m91, m92]

        m71.model8 = m81
        m71.model9 = [m91, m92]

        m72.model8 = m82
        m72.model9 = [m93]

        m73.model8 = m83

        m81.model9 = m93

        session.add_all([
            m11, m12, m13, m21, m22, m33,
            m31, m32, m33, m41, m42, m43,
            m51, m52, m53, m61, m62, m63,
            m71, m72, m73, m81, m82, m83,
            m91, m92, m93
            ])
        await session.commit()

        assert m21.get_related(session) == {m11}
        assert m22.get_related(session) == {m12}
        assert m23.get_related(session) == {m13}

        assert m31.get_related(session) == {m11}
        assert m32.get_related(session) == {m11}
        assert m33.get_related(session) == {m12, m21}

        assert m41.get_related(session) == {m12, m13, m21, m31}
        assert m42.get_related(session) == {m11, m13, m21, m32}
        assert m43.get_related(session) == {m11, m12, m22, m33}

        assert m51.get_related(session) == {m22, m23, m31}
        assert m52.get_related(session) == {m21, m23, m31}
        assert m53.get_related(session) == {m21, m22, m32, m41}

        assert m61.get_related(session) == {m32, m33, m41, m51}
        assert m62.get_related(session) == {m31, m33, m41, m52}
        assert m63.get_related(session) == {m31, m32, m42, m53}

        assert m71.get_related(session) == {m42, m43, m51}
        assert m72.get_related(session) == {m41, m43, m51}
        assert m73.get_related(session) == {m41, m42, m52, m61}

        assert m81.get_related(session) == {m52, m53, m61, m71}
        assert m82.get_related(session) == {m51, m53, m61, m72}
        assert m83.get_related(session) == {m51, m52, m62, m73}

        assert m91.get_related(session) == {m62, m63, m71}
        assert m92.get_related(session) == {m61, m63, m71}
        assert m93.get_related(session) == {m61, m62, m72, m81}
