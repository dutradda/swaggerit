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


from tests.integration.fixtures import ModelSQLAlchemyRedisBase
import sqlalchemy as sa


mtm_table = sa.Table(
    'model1_model4', ModelSQLAlchemyRedisBase.metadata,
    sa.Column('model1_id', sa.Integer, sa.ForeignKey('model1.id', ondelete='CASCADE')),
    sa.Column('model4_id', sa.Integer, sa.ForeignKey('model4.id', ondelete='CASCADE')),
    mysql_engine='innodb'
)


class Model1(ModelSQLAlchemyRedisBase):
    __tablename__ = 'model1'
    __table_args__ = {'mysql_engine':'innodb'}
    id = sa.Column(sa.Integer, primary_key=True)
    model2_id = sa.Column(sa.ForeignKey('model2.id'))

    model2 = sa.orm.relationship('Model2') # one-to-many
    model3 = sa.orm.relationship('Model3', uselist=True) # many-to-one
    model4 = sa.orm.relationship('Model4', uselist=True, secondary='model1_model4') # many-to-many


mtm_table = sa.Table(
    'model2_model5', ModelSQLAlchemyRedisBase.metadata,
    sa.Column('model2_id', sa.Integer, sa.ForeignKey('model2.id', ondelete='CASCADE')),
    sa.Column('model5_id', sa.Integer, sa.ForeignKey('model5.id', ondelete='CASCADE')),
    mysql_engine='innodb'
)


class Model2(ModelSQLAlchemyRedisBase):
    __tablename__ = 'model2'
    __table_args__ = {'mysql_engine':'innodb'}
    id = sa.Column(sa.Integer, primary_key=True)
    model3_id = sa.Column(sa.ForeignKey('model3.id'))

    model3 = sa.orm.relationship('Model3') # one-to-many
    model4 = sa.orm.relationship('Model4', uselist=True) # many-to-one
    model5 = sa.orm.relationship('Model5', uselist=True, secondary='model2_model5') # many-to-many


mtm_table = sa.Table(
    'model3_model6', ModelSQLAlchemyRedisBase.metadata,
    sa.Column('model3_id', sa.Integer, sa.ForeignKey('model3.id', ondelete='CASCADE')),
    sa.Column('model6_id', sa.Integer, sa.ForeignKey('model6.id', ondelete='CASCADE')),
    mysql_engine='innodb'
)


class Model3(ModelSQLAlchemyRedisBase):
    __tablename__ = 'model3'
    __table_args__ = {'mysql_engine':'innodb'}
    id = sa.Column(sa.Integer, primary_key=True)
    model4_id = sa.Column(sa.ForeignKey('model4.id'))
    model1_id = sa.Column(sa.ForeignKey('model1.id'))

    model4 = sa.orm.relationship('Model4') # one-to-many
    model5 = sa.orm.relationship('Model5', uselist=True) # many-to-one
    model6 = sa.orm.relationship('Model6', uselist=True, secondary='model3_model6') # many-to-many


mtm_table = sa.Table(
    'model4_model7', ModelSQLAlchemyRedisBase.metadata,
    sa.Column('model4_id', sa.Integer, sa.ForeignKey('model4.id', ondelete='CASCADE')),
    sa.Column('model7_id', sa.Integer, sa.ForeignKey('model7.id', ondelete='CASCADE')),
    mysql_engine='innodb'
)


class Model4(ModelSQLAlchemyRedisBase):
    __tablename__ = 'model4'
    __table_args__ = {'mysql_engine':'innodb'}
    id = sa.Column(sa.Integer, primary_key=True)
    model5_id = sa.Column(sa.ForeignKey('model5.id'))
    model2_id = sa.Column(sa.ForeignKey('model2.id'))

    model5 = sa.orm.relationship('Model5') # one-to-many
    model6 = sa.orm.relationship('Model6', uselist=True) # many-to-one
    model7 = sa.orm.relationship('Model7', uselist=True, secondary='model4_model7') # many-to-many


mtm_table = sa.Table(
    'model5_model8', ModelSQLAlchemyRedisBase.metadata,
    sa.Column('model5_id', sa.Integer, sa.ForeignKey('model5.id', ondelete='CASCADE')),
    sa.Column('model8_id', sa.Integer, sa.ForeignKey('model8.id', ondelete='CASCADE')),
    mysql_engine='innodb'
)


class Model5(ModelSQLAlchemyRedisBase):
    __tablename__ = 'model5'
    __table_args__ = {'mysql_engine':'innodb'}
    id = sa.Column(sa.Integer, primary_key=True)
    model6_id = sa.Column(sa.ForeignKey('model6.id'))
    model3_id = sa.Column(sa.ForeignKey('model3.id'))

    model6 = sa.orm.relationship('Model6') # one-to-many
    model7 = sa.orm.relationship('Model7', uselist=True) # many-to-one
    model8 = sa.orm.relationship('Model8', uselist=True, secondary='model5_model8') # many-to-many


mtm_table = sa.Table(
    'model6_model9', ModelSQLAlchemyRedisBase.metadata,
    sa.Column('model6_id', sa.Integer, sa.ForeignKey('model6.id', ondelete='CASCADE')),
    sa.Column('model9_id', sa.Integer, sa.ForeignKey('model9.id', ondelete='CASCADE')),
    mysql_engine='innodb'
)


class Model6(ModelSQLAlchemyRedisBase):
    __tablename__ = 'model6'
    __table_args__ = {'mysql_engine':'innodb'}
    id = sa.Column(sa.Integer, primary_key=True)
    model7_id = sa.Column(sa.ForeignKey('model7.id'))
    model4_id = sa.Column(sa.ForeignKey('model4.id'))

    model7 = sa.orm.relationship('Model7') # one-to-many
    model8 = sa.orm.relationship('Model8', uselist=True) # many-to-one
    model9 = sa.orm.relationship('Model9', uselist=True, secondary='model6_model9') # many-to-many


class Model7(ModelSQLAlchemyRedisBase):
    __tablename__ = 'model7'
    __table_args__ = {'mysql_engine':'innodb'}
    id = sa.Column(sa.Integer, primary_key=True)
    model8_id = sa.Column(sa.ForeignKey('model8.id'))
    model5_id = sa.Column(sa.ForeignKey('model5.id'))

    model8 = sa.orm.relationship('Model8') # one-to-many
    model9 = sa.orm.relationship('Model9', uselist=True) # many-to-one


class Model8(ModelSQLAlchemyRedisBase):
    __tablename__ = 'model8'
    __table_args__ = {'mysql_engine':'innodb'}
    id = sa.Column(sa.Integer, primary_key=True)
    model9_id = sa.Column(sa.ForeignKey('model9.id'))
    model6_id = sa.Column(sa.ForeignKey('model6.id'))

    model9 = sa.orm.relationship('Model9') # one-to-many


class Model9(ModelSQLAlchemyRedisBase):
    __tablename__ = 'model9'
    __table_args__ = {'mysql_engine':'innodb'}
    id = sa.Column(sa.Integer, primary_key=True)
    model7_id = sa.Column(sa.ForeignKey('model7.id'))


class Model10(ModelSQLAlchemyRedisBase):
    __tablename__ = 'model10'
    __table_args__ = {'mysql_engine':'innodb'}
    id = sa.Column(sa.Integer, primary_key=True)


class Model11(ModelSQLAlchemyRedisBase):
    __tablename__ = 'model11'
    __table_args__ = {'mysql_engine':'innodb'}
    id = sa.Column(sa.Integer, primary_key=True)


class Model12(ModelSQLAlchemyRedisBase):
    __tablename__ = 'model_no_redis'
    __table_args__ = {'mysql_engine':'innodb'}
    __use_redis__ = False

    id = sa.Column(sa.Integer, primary_key=True)


class Model13(ModelSQLAlchemyRedisBase):
    __tablename__ = 'Model13'
    __table_args__ = {'mysql_engine':'innodb'}
    id = sa.Column(sa.Integer, primary_key=True)


class Model13_two_ids(ModelSQLAlchemyRedisBase):
    __tablename__ = 'Model13_two_ids'
    __table_args__ = {'mysql_engine':'innodb'}
    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    id2 = sa.Column(sa.Integer, primary_key=True)


class Model13_three_ids(ModelSQLAlchemyRedisBase):
    __tablename__ = 'Model13_three_ids'
    __table_args__ = {'mysql_engine':'innodb'}
    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    id2 = sa.Column(sa.Integer, primary_key=True)
    id3 = sa.Column(sa.Integer, primary_key=True)


class Model14(ModelSQLAlchemyRedisBase):
    __tablename__ = 'Model14'
    __table_args__ = {'mysql_engine':'innodb'}
    id = sa.Column(sa.Integer, primary_key=True)
    Model13_id = sa.Column(sa.ForeignKey('Model13.id'))
    Model13 = sa.orm.relationship('Model13')


class Model15(ModelSQLAlchemyRedisBase):
    __tablename__ = 'Model15'
    __table_args__ = {'mysql_engine':'innodb'}
    id = sa.Column(sa.Integer, primary_key=True)
    Model13_id = sa.Column(sa.ForeignKey('Model13.id', ondelete='CASCADE'))
    Model14_id = sa.Column(sa.ForeignKey('Model14.id', ondelete='CASCADE'))
    Model13 = sa.orm.relationship('Model13')
    Model14 = sa.orm.relationship('Model14')


mtm_table = sa.Table(
    'mtm', ModelSQLAlchemyRedisBase.metadata,
    sa.Column('Model13_id', sa.Integer, sa.ForeignKey('Model13.id', ondelete='CASCADE')),
    sa.Column('Model14_id', sa.Integer, sa.ForeignKey('Model14_mtm.id', ondelete='CASCADE')),
    mysql_engine='innodb'
)


class Model14_mtm(ModelSQLAlchemyRedisBase):
    __tablename__ = 'Model14_mtm'
    __table_args__ = {'mysql_engine':'innodb'}
    id = sa.Column(sa.Integer, primary_key=True)
    Model13 = sa.orm.relationship(
        'Model13', secondary='mtm', uselist=True)


class Model15_mtm(ModelSQLAlchemyRedisBase):
    __tablename__ = 'Model15_mtm'
    __table_args__ = {'mysql_engine':'innodb'}
    id = sa.Column(sa.Integer, primary_key=True)
    Model13_id = sa.Column(sa.ForeignKey('Model13.id', ondelete='CASCADE'))
    Model14_id = sa.Column(sa.ForeignKey('Model14_mtm.id', ondelete='CASCADE'))
    Model13 = sa.orm.relationship(Model13)
    Model14 = sa.orm.relationship(Model14_mtm)


class Model14_primary_join(ModelSQLAlchemyRedisBase):
    __tablename__ = 'Model14_primary_join'
    __table_args__ = {'mysql_engine':'innodb'}
    id = sa.Column(sa.Integer, primary_key=True)
    id2 = sa.Column(sa.Integer)
    Model13_id = sa.Column(sa.ForeignKey('Model13.id', ondelete='CASCADE'))
    Model13 = sa.orm.relationship(
        Model13,
        primaryjoin='and_(Model14_primary_join.Model13_id==Model13.id, Model14_primary_join.id2==Model13.id)')


class Model13_mto(ModelSQLAlchemyRedisBase):
    __tablename__ = 'Model13_mto'
    __table_args__ = {'mysql_engine':'innodb'}
    id = sa.Column(sa.Integer, primary_key=True)

    Model14 = sa.orm.relationship('Model14_mto', uselist=True)


class Model14_mto(ModelSQLAlchemyRedisBase):
    __tablename__ = 'Model14_mto'
    __table_args__ = {'mysql_engine':'innodb'}
    id = sa.Column(sa.Integer, primary_key=True)
    Model13_id = sa.Column(sa.ForeignKey('Model13_mto.id', ondelete='CASCADE'))


class Model15_mto(ModelSQLAlchemyRedisBase):
    __tablename__ = 'Model15_mto'
    __table_args__ = {'mysql_engine':'innodb'}
    id = sa.Column(sa.Integer, primary_key=True)
    Model13_id = sa.Column(sa.ForeignKey('Model13_mto.id', ondelete='CASCADE'))
    Model14_id = sa.Column(sa.ForeignKey('Model14_mto.id', ondelete='CASCADE'))
    Model13 = sa.orm.relationship('Model13_mto')
    Model14 = sa.orm.relationship('Model14_mto')


class Model13_nested(ModelSQLAlchemyRedisBase):
    __tablename__ = 'Model13_nested'
    id = sa.Column(sa.Integer, primary_key=True)
    test = sa.Column(sa.String(100))


class Model14_nested(ModelSQLAlchemyRedisBase):
    __tablename__ = 'Model14_nested'
    __table_args__ = {'mysql_engine':'innodb'}
    id = sa.Column(sa.Integer, primary_key=True)
    Model13_id = sa.Column(sa.ForeignKey('Model13_nested.id'))
    Model13 = sa.orm.relationship('Model13_nested')


class Model15_nested(ModelSQLAlchemyRedisBase):
    __tablename__ = 'Model15_nested'
    __table_args__ = {'mysql_engine':'innodb'}
    id = sa.Column(sa.Integer, primary_key=True)
    Model13_id = sa.Column(sa.ForeignKey('Model13_nested.id', ondelete='CASCADE'))
    Model14_id = sa.Column(sa.ForeignKey('Model14_nested.id', ondelete='CASCADE'))
    Model13 = sa.orm.relationship('Model13_nested')
    Model14 = sa.orm.relationship('Model14_nested')


mtm_table = sa.Table(
    'mtm_nested', ModelSQLAlchemyRedisBase.metadata,
    sa.Column('Model13_id', sa.Integer, sa.ForeignKey('Model13_nested.id', ondelete='CASCADE')),
    sa.Column('Model14_id', sa.Integer, sa.ForeignKey('Model14_mtm_nested.id', ondelete='CASCADE')),
    mysql_engine='innodb'
)


class Model14_mtm_nested(ModelSQLAlchemyRedisBase):
    __tablename__ = 'Model14_mtm_nested'
    __table_args__ = {'mysql_engine':'innodb'}
    id = sa.Column(sa.Integer, primary_key=True)
    Model13 = sa.orm.relationship('Model13_nested', secondary='mtm_nested', uselist=True)


class Model15_mtm_nested(ModelSQLAlchemyRedisBase):
    __tablename__ = 'Model15_mtm_nested'
    __table_args__ = {'mysql_engine':'innodb'}
    id = sa.Column(sa.Integer, primary_key=True)
    Model13_id = sa.Column(sa.ForeignKey('Model13_nested.id', ondelete='CASCADE'))
    Model14_id = sa.Column(sa.ForeignKey('Model14_mtm_nested.id', ondelete='CASCADE'))
    Model13 = sa.orm.relationship('Model13_nested')
    Model14 = sa.orm.relationship('Model14_mtm_nested')


class Model13_mto_nested(ModelSQLAlchemyRedisBase):
    __tablename__ = 'Model13_mto_nested'
    __table_args__ = {'mysql_engine':'innodb'}
    id = sa.Column(sa.Integer, primary_key=True)

    Model14 = sa.orm.relationship('Model14_mto_nested', uselist=True)


class Model14_mto_nested(ModelSQLAlchemyRedisBase):
    __tablename__ = 'Model14_mto_nested'
    __table_args__ = {'mysql_engine':'innodb'}
    id = sa.Column(sa.Integer, primary_key=True)
    Model13_id = sa.Column(sa.ForeignKey('Model13_mto_nested.id', ondelete='CASCADE'))
    test = sa.Column(sa.String(100))


class Model15_mto_nested(ModelSQLAlchemyRedisBase):
    __tablename__ = 'Model15_mto_nested'
    __table_args__ = {'mysql_engine':'innodb'}
    id = sa.Column(sa.Integer, primary_key=True)
    Model13_id = sa.Column(sa.ForeignKey('Model13_mto_nested.id', ondelete='CASCADE'))
    Model14_id = sa.Column(sa.ForeignKey('Model14_mto_nested.id', ondelete='CASCADE'))
    Model13 = sa.orm.relationship('Model13_mto_nested')
    Model14 = sa.orm.relationship('Model14_mto_nested')
