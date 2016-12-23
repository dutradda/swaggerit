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
from swaggerit.exceptions import SwaggerItModelError
from copy import deepcopy
from unittest import mock
import pytest
import ujson
import sqlalchemy as sa


class TestModelBaseTodict(object):

    @pytest.mark.asyncio(forbid_global_loop=False)
    async def test_todict_after_get_from_database(self, session):
        session.add(await Model14.new(session, id=1, Model13={'id': 1, '_operation': 'insert'}))
        await session.commit()
        expected = {
            'id': 1,
            'Model13_id': 1,
            'Model13': {'id': 1}
        }
        session.query(Model14).filter_by(id=1).one().todict() == expected

    @pytest.mark.asyncio(forbid_global_loop=False)
    async def test_todict_after_get_from_database_with_mtm(self, session):
        session.add(await Model14_mtm.new(session, id=1, Model13=[{'id': 1, '_operation': 'insert'}]))
        await session.commit()
        expected = {
            'id': 1,
            'Model13': [{'id': 1}]
        }
        session.query(Model14_mtm).filter_by(id=1).one().todict() == expected

    @pytest.mark.asyncio(forbid_global_loop=False)
    async def test_todict_after_get_from_database_with_mtm_with_two_relations(
            self, session):
        session.add(await Model14_mtm.new(session, id=1, Model13=[{'id': 1, '_operation': 'insert'}, {'id': 2, '_operation': 'insert'}]))
        await session.commit()
        expected = {
            'id': 1,
            'Model13': [{'id': 1}, {'id': 2}]
        }
        session.query(Model14_mtm).filter_by(id=1).one().todict() == expected


class TestModelBaseGetRelated(object):

    @pytest.mark.asyncio(forbid_global_loop=False)
    async def test_get_related_with_one_model(self, session):
        m11 = await Model13.new(session, id=1)
        m21 = await Model14.new(session, id=1)
        m21.Model13 = m11
        session.add_all([m11, m21])
        await session.commit()

        assert m11.get_related(session) == {m21}

    @pytest.mark.asyncio(forbid_global_loop=False)
    async def test_get_related_with_two_models(self, session):
        m11 = await Model13.new(session, id=1)
        m21 = await Model14.new(session, id=1)
        m31 = await Model15.new(session, id=1)
        m31.Model13 = m11
        m31.Model14 = m21
        session.add_all([m11, m21, m31])
        await session.commit()

        assert m11.get_related(session) == {m31}
        assert m21.get_related(session) == {m31}

    @pytest.mark.asyncio(forbid_global_loop=False)
    async def test_get_related_with_two_related(self, session):
        m11 = await Model13.new(session, id=1)
        m21 = await Model14.new(session, id=1)
        m31 = await Model15.new(session, id=1)
        m31.Model13 = m11
        m21.Model13 = m11
        session.add_all([m11, m21, m31])
        await session.commit()

        assert m11.get_related(session) == {m31, m21}

    @pytest.mark.asyncio(forbid_global_loop=False)
    async def test_get_related_with_two_models_and_two_related(self, session):
        m11 = await Model13.new(session, id=1)
        m21 = await Model14.new(session, id=1)
        m31 = await Model15.new(session, id=1)
        m31.Model13 = m11
        m21.Model13 = m11
        m22 = await Model14.new(session, id=2)
        m32 = await Model15.new(session, id=2)
        m32.Model13 = m11
        m22.Model13 = m11
        session.add_all([m11, m21, m31, m22, m32])
        await session.commit()

        assert m11.get_related(session) == {m31, m21, m22, m32}

    @pytest.mark.asyncio(forbid_global_loop=False)
    async def test_get_related_with_mtm(
            self, session):
        m11 = await Model13.new(session, id=1)
        m12 = await Model13.new(session, id=2)
        m21 = await Model14_mtm.new(session, id=1)
        m31 = await Model15_mtm.new(session, id=1)
        m31.Model13 = m11
        m21.Model13 = [m11, m12]
        m22 = await Model14_mtm.new(session, id=2)
        m32 = await Model15_mtm.new(session, id=2)
        m32.Model13 = m11
        m22.Model13 = [m11, m12]
        session.add_all([m11, m12, m21, m31, m22, m32])
        await session.commit()

        assert m11.get_related(session) == {m31, m21, m22, m32}
        assert m12.get_related(session) == {m21, m22}

    @pytest.mark.asyncio(forbid_global_loop=False)
    async def test_get_related_with_primary_join(
            self, session):
        m11 = await Model13.new(session, id=5)
        m21 = await Model14_primary_join.new(session, id=1, id2=5)
        m21.Model13 = m11
        session.add_all([m11, m21])
        await session.commit()

        assert m21.Model13 == m11
        assert m11.get_related(session) == {m21}

    @pytest.mark.asyncio(forbid_global_loop=False)
    async def test_get_related_with_primary_join_get_no_result(
            self, session):
        m11 = await Model13.new(session, id=1)
        m21 = await Model14_primary_join.new(session, id=1, id2=5)
        m21.Model13 = m11
        session.add_all([m11, m21])
        await session.commit()

        assert m21.Model13 == None
        assert m11.get_related(session) == set()
        assert m21.get_related(session) == set()

    @pytest.mark.asyncio(forbid_global_loop=False)
    async def test_get_related_with_mto(
            self, session):
        m11 = await Model13_mto.new(session, id=1)
        m21 = await Model14_mto.new(session, id=1)
        m11.Model14 = [m21]
        session.add_all([m11, m21])
        await session.commit()

        assert m11.Model14 == [m21]
        assert m21.get_related(session) == {m11}

    @pytest.mark.asyncio(forbid_global_loop=False)
    async def test_get_related_with_mto_with_two_related(
            self, session):
        m11 = await Model13_mto.new(session, id=1)
        m21 = await Model14_mto.new(session, id=1)
        m22 = await Model14_mto.new(session, id=2)
        m11.Model14 = [m21, m22]
        session.add(m11)
        await session.commit()

        assert m11.Model14 == [m21, m22]
        assert m21.get_related(session) == {m11}


class TestModelBaseInsert(object):

    @pytest.mark.asyncio(forbid_global_loop=False)
    async def test_insert_with_one_object(self, session):
        objs = await Model13.insert(session, {'id': 1})
        assert objs == [{'id': 1}]

    @pytest.mark.asyncio(forbid_global_loop=False)
    async def test_insert_without_todict(self, session):
        objs = await Model13.insert(session, {'id': 1}, todict=False)
        assert [o.todict() for o in objs] == [{'id': 1}]

    @pytest.mark.asyncio(forbid_global_loop=False)
    async def test_insert_with_two_objects(self, session):
        objs = await Model13.insert(session, [{'id': 1}, {'id': 2}])
        assert objs == [{'id': 1}, {'id': 2}] or objs == [{'id': 2}, {'id': 1}]

    @pytest.mark.asyncio(forbid_global_loop=False)
    async def test_insert_with_two_nested_objects(self, session):
        objs = await Model14.insert(session, {'id': 1, 'Model13': {'id': 1, '_operation': 'insert'}})
        assert objs == [{'id': 1, 'Model13_id': 1, 'Model13': {'id': 1}}]

    @pytest.mark.asyncio(forbid_global_loop=False)
    async def test_insert_with_three_nested_objects(self, session):
        m1 = {'id': 1, '_operation': 'insert'}
        m2 = {'id': 1, 'Model13': m1, '_operation': 'insert'}
        objs = await Model15.insert(session, {'id': 1, 'Model14': m2})

        expected = {
            'id': 1,
            'Model13_id': None,
            'Model13': None,
            'Model14_id': 1,
            'Model14': {
                'id': 1,
                'Model13_id': 1,
                'Model13': {
                    'id': 1
                }
            }
        }
        assert objs == [expected]

    @pytest.mark.asyncio(forbid_global_loop=False)
    async def test_insert_with_nested_update(self, session):
        await Model13.insert(session, {'id': 1})
        await Model14.insert(session, {'id': 1})

        m3 = {
            'id': 1,
            'Model14': {
                'id': 1,
                '_operation': 'update',
                'Model13_id': 1
            }
        }
        objs = await Model15.insert(session, m3)

        expected = {
            'id': 1,
            'Model13_id': None,
            'Model13': None,
            'Model14_id': 1,
            'Model14': {
                'id': 1,
                'Model13_id': 1,
                'Model13': {
                    'id': 1
                }
            }
        }
        assert objs == [expected]

    @pytest.mark.asyncio(forbid_global_loop=False)
    async def test_insert_with_nested_update_and_get(self, session):
        await Model13.insert(session, {'id': 1})
        await Model14.insert(session, {'id': 1})

        m3 = {
            'id': 1,
            'Model14': {
                'id': 1,
                '_operation': 'update',
                'Model13': {'id': 1, '_operation': 'get'}
            }
        }
        objs = await Model15.insert(session, m3)

        expected = {
            'id': 1,
            'Model13_id': None,
            'Model13': None,
            'Model14_id': 1,
            'Model14': {
                'id': 1,
                'Model13_id': 1,
                'Model13': {
                    'id': 1
                }
            }
        }
        assert objs == [expected]

    @pytest.mark.asyncio(forbid_global_loop=False)
    async def test_insert_with_two_nested_update(self, session):
        await Model13_nested.insert(session, {'id': 1})
        await Model14_nested.insert(session, {'id': 1})

        m3 = {
            'id': 1,
            'Model14': {
                'id': 1,
                '_operation': 'update',
                'Model13': {
                    'id': 1,
                    '_operation': 'update',
                    'test': 'test_updated'
                }
            }
        }
        objs = await Model15_nested.insert(session, m3)

        expected = {
            'id': 1,
            'Model13_id': None,
            'Model13': None,
            'Model14_id': 1,
            'Model14': {
                'id': 1,
                'Model13_id': 1,
                'Model13': {
                    'id': 1,
                    'test': 'test_updated'
                }
            }
        }
        assert objs == [expected]

    @pytest.mark.asyncio(forbid_global_loop=False)
    async def test_insert_with_two_nested_update_with_mtm(self, session):
        await Model13_nested.insert(session, [{'id': 1}, {'id': 2}])
        await Model14_mtm_nested.insert(session, {'id': 1})

        m3 = {
            'id': 1,
            'Model14': {
                'id': 1,
                '_operation': 'update',
                'Model13': [
                    {
                        'id': 1,
                        '_operation': 'update',
                        'test': 'test_updated'
                    }, {
                        'id': 2,
                        '_operation': 'update',
                        'test': 'test_updated2'
                    }
                ]
            }
        }
        objs = await Model15_mtm_nested.insert(session, m3)

        expected = {
            'id': 1,
            'Model13_id': None,
            'Model13': None,
            'Model14_id': 1,
            'Model14': {
                'id': 1,
                'Model13': [
                    {
                        'id': 1,
                        'test': 'test_updated'
                    },{
                        'id': 2,
                        'test': 'test_updated2'
                    }
                ]
            }
        }
        assert objs == [expected]

    @pytest.mark.asyncio(forbid_global_loop=False)
    async def test_insert_with_two_nested_update_with_mto(self, session):
        await Model13_mto_nested.insert(session, {'id': 1})
        await Model14_mto_nested.insert(session, [{'id': 1}, {'id': 2}])

        m3 = {
            'id': 1,
            'Model13': {
                'id': 1,
                '_operation': 'update',
                'Model14': [
                    {
                        'id': 1,
                        '_operation': 'update',
                        'test': 'test_updated'
                    }, {
                        'id': 2,
                        '_operation': 'update',
                        'test': 'test_updated2'
                    }
                ]
            }
        }
        objs = await Model15_mto_nested.insert(session, m3)

        expected = {
            'id': 1,
            'Model14_id': None,
            'Model14': None,
            'Model13_id': 1,
            'Model13': {
                'id': 1,
                'Model14': [
                    {
                        'id': 1,
                        'Model13_id': 1,
                        'test': 'test_updated'
                    },{
                        'id': 2,
                        'Model13_id': 1,
                        'test': 'test_updated2'
                    }
                ]
            }
        }
        assert objs == [expected]

    @pytest.mark.asyncio(forbid_global_loop=False)
    async def test_insert_with_mtm_update_and_delete(self, session):
        m1 = {'id': 1, '_operation': 'insert'}
        m2 = {'id': 1, 'Model13': [m1]}
        await Model14_mtm.insert(session, m2)
        m3_insert = {
            'id': 1,
            'Model14': {
                'id': 1,
                '_operation': 'update',
                'Model13': [{
                    'id': 1,
                    '_operation': 'delete'
                }]
            }
        }
        objs = await Model15_mtm.insert(session, m3_insert)
        assert session.query(Model13).all() == []

        expected = {
            'id': 1,
            'Model13_id': None,
            'Model13': None,
            'Model14_id': 1,
            'Model14': {
                'id': 1,
                'Model13': []
            }
        }
        assert objs == [expected]

    @pytest.mark.asyncio(forbid_global_loop=False)
    async def test_insert_with_mtm_update_and_remove(self, session):
        m1 = {'id': 1, '_operation': 'insert'}
        m2 = {'id': 1, 'Model13': [m1]}
        await Model14_mtm.insert(session, m2)
        m3_insert = {
            'id': 1,
            'Model14': {
                'id': 1,
                '_operation': 'update',
                'Model13': [{
                    'id': 1,
                    '_operation': 'remove'
                }]
            }
        }
        objs = await Model15_mtm.insert(session, m3_insert)
        assert session.query(Model13).one().todict() == {'id': 1}

        expected = {
            'id': 1,
            'Model13_id': None,
            'Model13': None,
            'Model14_id': 1,
            'Model14': {
                'id': 1,
                'Model13': []
            }
        }
        assert objs == [expected]

    @pytest.mark.asyncio(forbid_global_loop=False)
    async def test_insert_with_mto_update_and_remove(self, session):
        m2 = {'id': 1, '_operation': 'insert'}
        m1 = {'id': 1, 'Model14': [m2]}
        await Model13_mto.insert(session, m1)
        m3_insert = {
            'id': 1,
            'Model13': {
                'id': 1,
                '_operation': 'update',
                'Model14': [{
                    'id': 1,
                    '_operation': 'remove'
                }]
            }
        }
        objs = await Model15_mto.insert(session, m3_insert)
        assert session.query(Model14_mto).one().todict() == {'id': 1, 'Model13_id': None}

        expected = {
            'id': 1,
            'Model13_id': 1,
            'Model14_id': None,
            'Model13': {
                'id': 1,
                'Model14': []
            },
            'Model14': None
        }
        assert objs == [expected]

    @pytest.mark.asyncio(forbid_global_loop=False)
    async def test_insert_nested_update_without_relationships(self, session):
        with pytest.raises(SwaggerItModelError):
            await Model14.insert(session, {'Model13': {'id': 1, '_operation': 'update'}})

    @pytest.mark.asyncio(forbid_global_loop=False)
    async def test_insert_nested_remove_without_relationships(self, session):
        with pytest.raises(SwaggerItModelError):
            await Model14.insert(session, {'Model13': {'id': 1, '_operation': 'remove'}})

    @pytest.mark.asyncio(forbid_global_loop=False)
    async def test_insert_nested_delete_without_relationships(self, session):
        with pytest.raises(SwaggerItModelError):
            await Model14.insert(session, {'Model13': {'id': 1, '_operation': 'delete'}})


class TestModelBaseUpdate(object):

    @pytest.mark.asyncio(forbid_global_loop=False)
    async def test_update_with_one_object(self, session):
        await Model13_nested.insert(session, {'id': 1})
        await Model13_nested.update(session, {'id': 1, 'test': 'test_updated'})
        assert session.query(Model13_nested).one().todict() == {'id': 1, 'test': 'test_updated'}

    @pytest.mark.asyncio(forbid_global_loop=False)
    async def test_update_with_two_objects(self, session):
        await Model13_nested.insert(session, [{'id': 1}, {'id': 2}])
        await Model13_nested.update(session, [
            {'id': 1, 'test': 'test_updated'},
            {'id': 2, 'test': 'test_updated2'}])
        assert [o.todict() for o in session.query(Model13_nested).all()] == \
            [{'id': 1, 'test': 'test_updated'}, {'id': 2, 'test': 'test_updated2'}]

    @pytest.mark.asyncio(forbid_global_loop=False)
    async def test_update_with_two_nested_objects(self, session):
        await Model13_nested.insert(session, {'id': 1})
        await Model14_nested.insert(session, {'id': 1})
        await Model14_nested.update(session, {'id': 1, 'Model13': {'id': 1, '_operation': 'update', 'test': 'test_updated'}})

        assert session.query(Model14_nested).one().todict() == {
            'id': 1,
            'Model13_id': 1,
            'Model13': {
                'id': 1,
                'test': 'test_updated'
            }
        }

    @pytest.mark.asyncio(forbid_global_loop=False)
    async def test_update_with_three_nested_objects(self, session):
        await Model13_nested.insert(session, {'id': 1})
        await Model14_nested.insert(session, {'id': 1})
        await Model15_nested.insert(session, {'id': 1})
        m3_update = {
            'id': 1,
            'Model14': {
                'id': 1,
                '_operation': 'update',
                'Model13': {
                    'id': 1,
                    '_operation': 'update',
                    'test': 'test_updated'
                }
            }
        }
        await Model15_nested.update(session, m3_update)

        assert session.query(Model15_nested).one().todict() == {
            'id': 1,
            'Model13_id': None,
            'Model13': None,
            'Model14_id': 1,
            'Model14': {
                'id': 1,
                'Model13_id': 1,
                'Model13': {
                    'id': 1,
                    'test': 'test_updated'
                }
            }
        }

    @pytest.mark.asyncio(forbid_global_loop=False)
    async def test_update_with_nested_insert(self, session):
        await Model14.insert(session, {'id': 1})

        m2_update = {
            'id': 1,
            'Model13': {
                'id': 1,
                '_operation': 'insert'
            }
        }
        await Model14.update(session, m2_update)

        expected = {
            'id': 1,
            'Model13_id': 1,
            'Model13': {
                'id': 1
            }
        }
        assert session.query(Model14).one().todict() == expected

    @pytest.mark.asyncio(forbid_global_loop=False)
    async def test_update_with_two_nested_insert(self, session):
        await Model15.insert(session, {'id': 1})

        m3_update = {
            'id': 1,
            'Model14': {
                'id': 1,
                '_operation': 'insert',
                'Model13': {
                    'id': 1,
                    '_operation': 'insert'
                }
            }
        }
        await Model15.update(session, m3_update)

        expected = {
            'id': 1,
            'Model13_id': None,
            'Model13': None,
            'Model14_id': 1,
            'Model14': {
                'id': 1,
                'Model13_id': 1,
                'Model13': {
                    'id': 1
                }
            }
        }
        assert session.query(Model15).one().todict() == expected

    @pytest.mark.asyncio(forbid_global_loop=False)
    async def test_update_with_two_nested_insert_with_mtm(self, session):
        await Model15_mtm.insert(session, {'id': 1})

        m3_update = {
            'id': 1,
            'Model14': {
                'id': 1,
                '_operation': 'insert',
                'Model13': [
                    {'id': 1, '_operation': 'insert'},
                    {'id': 2, '_operation': 'insert'}
                ]
            }
        }
        await Model15_mtm.update(session, m3_update)

        expected = {
            'id': 1,
            'Model13_id': None,
            'Model13': None,
            'Model14_id': 1,
            'Model14': {
                'id': 1,
                'Model13': [
                    {'id': 1},
                    {'id': 2}
                ]
            }
        }
        assert session.query(Model15_mtm).one().todict() == expected

    @pytest.mark.asyncio(forbid_global_loop=False)
    async def test_update_with_two_nested_insert_with_mto(self, session):
        await Model15_mto.insert(session, {'id': 1})

        m3_update = {
            'id': 1,
            'Model13': {
                'id': 1,
                '_operation': 'insert',
                'Model14': [
                    {'id': 1, '_operation': 'insert'},
                    {'id': 2, '_operation': 'insert'}
                ]
            }
        }
        await Model15_mto.update(session, m3_update)

        expected = {
            'id': 1,
            'Model13_id': 1,
            'Model13': {
                'id': 1,
                'Model14': [
                    {'id': 1, 'Model13_id': 1},
                    {'id': 2, 'Model13_id': 1}
                ]
            },
            'Model14_id': None,
            'Model14': None
        }
        assert session.query(Model15_mto).one().todict() == expected

    @pytest.mark.asyncio(forbid_global_loop=False)
    async def test_update_with_missing_id(self, session):
        session.add(await Model13.new(session, id=1))
        await session.commit()
        assert await Model13.update(session, [{'id': 1}, {'id': 2}]) == [{'id': 1}]

    @pytest.mark.asyncio(forbid_global_loop=False)
    async def test_update_with_missing_all_ids(self, session):
        assert await Model13.update(session, [{'id': 1}, {'id': 2}]) == []

    @pytest.mark.asyncio(forbid_global_loop=False)
    async def test_update_with_nested_remove_without_uselist(self, session):
        await Model14.insert(session, {'Model13': {'_operation': 'insert'}})
        await Model14.update(session, {'id': 1, 'Model13': {'id': 1, '_operation': 'remove'}})
        assert session.query(Model14).one().todict() == {'id': 1, 'Model13_id': None, 'Model13': None}

    @pytest.mark.asyncio(forbid_global_loop=False)
    async def test_update_with_nested_remove_with_two_relationships(self, session):
        await Model14_mtm.insert(session, {'Model13': [{'_operation': 'insert'}, {'_operation': 'insert'}]})
        await Model14_mtm.update(session, {'id': 1, 'Model13': [{'id': 2, '_operation': 'remove'}]})
        assert session.query(Model14_mtm).one().todict() == {'id': 1, 'Model13': [{'id': 1}]}


class TestModelBaseDelete(object):

    @pytest.mark.asyncio(forbid_global_loop=False)
    async def test_delete(self, session):
        await Model13.insert(session, {})
        assert await Model13.get(session) == [{'id': 1}]

        await Model13.delete(session, {'id': 1})
        assert await Model13.get(session) == []

    @pytest.mark.asyncio(forbid_global_loop=False)
    async def test_delete_with_invalid_id(self, session):
        await Model13.insert(session, {})
        await Model13.delete(session , [{'id': 2}, {'id': 3}])
        assert await Model13.get(session) == [{'id': 1}]

    @pytest.mark.asyncio(forbid_global_loop=False)
    async def test_delete_with_two_ids(self, session):
        await Model13_two_ids.insert(session, {'id2': 2})
        assert await Model13_two_ids.get(session) == [{'id': 1, 'id2': 2}]

        await Model13_two_ids.delete(session , {'id': 1, 'id2': 2})
        assert await Model13_two_ids.get(session) == []

    @pytest.mark.asyncio(forbid_global_loop=False)
    async def test_delete_with_three_ids(self, session):
        await Model13_three_ids.insert(session, {'id2': 2, 'id3': 3})
        assert await Model13_three_ids.get(session) == [{'id': 1, 'id2': 2, 'id3': 3}]

        await Model13_three_ids.delete(session , {'id': 1, 'id2': 2, 'id3': 3})
        assert await Model13_three_ids.get(session) == []
